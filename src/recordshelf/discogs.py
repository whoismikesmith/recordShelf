"""Discogs collection client and the background sync job."""

from __future__ import annotations

import asyncio
import logging
import re
import time
from collections.abc import AsyncIterator, Callable
from datetime import UTC, datetime
from typing import Any

import httpx
from pydantic import BaseModel

from .db import Database

log = logging.getLogger(__name__)

API = "https://api.discogs.com"
_NUM_SUFFIX = re.compile(r"\s*\(\d+\)$")
_LEADING_PUNCT = re.compile(r"^[^\w]+")
_ARTICLES = ("the ", "a ", "an ")


class DiscogsError(Exception):
    pass


def clean_artist_name(name: str) -> str:
    """Discogs disambiguates duplicate names as 'Bush (2)'. Drop the suffix for display."""
    return _NUM_SUFFIX.sub("", name or "").strip()


def artist_display(artists: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    for a in artists or []:
        name = clean_artist_name(a.get("name", ""))
        join = (a.get("join") or "").strip()
        if not name:
            continue
        parts.append(name)
        if join:
            parts.append(join if join == "," else f" {join} ")
    text = "".join(p if p != "," else ", " for p in parts).strip()
    return re.sub(r"\s+", " ", text)


def sort_name(name: str) -> str:
    """Shelf-style sort key: case-folded, leading punctuation and article dropped."""
    s = clean_artist_name(name).casefold()
    stripped = _LEADING_PUNCT.sub("", s)
    if stripped:
        s = stripped
    for art in _ARTICLES:
        if s.startswith(art):
            s = s[len(art) :]
            break
    return s.strip()


def parse_item(item: dict[str, Any]) -> dict[str, Any]:
    info = item.get("basic_information", {}) or {}
    artists = info.get("artists") or []
    labels = info.get("labels") or []
    formats = info.get("formats") or []
    first_format = formats[0] if formats else {}
    year = info.get("year") or None
    return {
        "instance_id": item["instance_id"],
        "release_id": item.get("id") or info.get("id"),
        "master_id": info.get("master_id") or None,
        "title": info.get("title") or "",
        "artist": artist_display(artists) or "Unknown Artist",
        "artist_sort": sort_name(artists[0]["name"]) if artists else "",
        "year": int(year) if year else None,
        "label": (labels[0].get("name") if labels else None) or None,
        "catno": (labels[0].get("catno") if labels else None) or None,
        "format": first_format.get("name") or None,
        "descriptions": list(first_format.get("descriptions") or []),
        "genres": list(info.get("genres") or []),
        "styles": list(info.get("styles") or []),
        "rating": int(item.get("rating") or 0),
        "date_added": item.get("date_added"),
        "folder_id": item.get("folder_id"),
        "thumb": info.get("thumb") or None,
        "cover": info.get("cover_image") or None,
        "raw": item,
    }


class DiscogsClient:
    def __init__(
        self,
        username: str,
        token: str = "",
        user_agent: str = "recordShelf/2.0",
        client: httpx.AsyncClient | None = None,
    ):
        if not username:
            raise DiscogsError("No Discogs username configured (set DISCOGS_USERNAME)")
        self.username = username
        self.token = token
        headers = {"User-Agent": user_agent, "Accept": "application/vnd.discogs.v2.discogs+json"}
        if token:
            headers["Authorization"] = f"Discogs token={token}"
        self._own_client = client is None
        self._client = client or httpx.AsyncClient(base_url=API, timeout=30)
        self._client.headers.update(headers)
        # Discogs allows 60 req/min authenticated, 25 unauthenticated. Stay under both.
        self._min_interval = 1.1 if token else 2.5
        self._last_request = 0.0

    async def aclose(self) -> None:
        if self._own_client:
            await self._client.aclose()

    async def _get(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        for _ in range(6):
            wait = self._min_interval - (time.monotonic() - self._last_request)
            if wait > 0:
                await asyncio.sleep(wait)
            self._last_request = time.monotonic()
            resp = await self._client.get(path, params=params)
            if resp.status_code == 429:
                header = resp.headers.get("Retry-After")
                retry = float(header) if header and header.replace(".", "", 1).isdigit() else 15.0
                log.warning("Discogs rate limited, sleeping %.0fs", retry)
                await asyncio.sleep(retry)
                continue
            if resp.status_code >= 400:
                try:
                    msg = resp.json().get("message", resp.text)
                except ValueError:
                    msg = resp.text
                raise DiscogsError(f"Discogs {resp.status_code}: {msg}")
            remaining = resp.headers.get("X-Discogs-Ratelimit-Remaining")
            if remaining is not None and remaining.isdigit() and int(remaining) <= 1:
                await asyncio.sleep(5)
            return resp.json()
        raise DiscogsError("Discogs kept rate limiting us; try again later")

    async def collection_pages(
        self, folder: int = 0, per_page: int = 100, sort: str = "artist"
    ) -> AsyncIterator[tuple[int, int, list[dict[str, Any]]]]:
        page = 1
        while True:
            data = await self._get(
                f"/users/{self.username}/collection/folders/{folder}/releases",
                {"page": page, "per_page": per_page, "sort": sort, "sort_order": "asc"},
            )
            pages = int(data.get("pagination", {}).get("pages", 1))
            yield page, pages, data.get("releases", [])
            if page >= pages:
                break
            page += 1

    async def identity_check(self) -> dict[str, Any]:
        return await self._get(f"/users/{self.username}", {})


class SyncStatus(BaseModel):
    state: str = "idle"  # idle | running | done | error
    page: int = 0
    pages: int = 0
    fetched: int = 0
    added: int = 0
    updated: int = 0
    removed: int = 0
    error: str | None = None
    started_at: str | None = None
    finished_at: str | None = None
    last_sync: str | None = None


class SyncManager:
    def __init__(
        self,
        db: Database,
        client_factory: Callable[[], DiscogsClient],
        on_change: Callable[[SyncStatus], Any] | None = None,
    ):
        self.db = db
        self._factory = client_factory
        self._on_change = on_change
        self._task: asyncio.Task | None = None
        self.status = SyncStatus(last_sync=db.get_meta("last_sync"))

    @property
    def running(self) -> bool:
        return self._task is not None and not self._task.done()

    def start(self) -> bool:
        if self.running:
            return False
        self._task = asyncio.create_task(self._run())
        return True

    async def wait(self) -> SyncStatus:
        if self._task is not None:
            await self._task
        return self.status

    def _notify(self) -> None:
        if self._on_change:
            try:
                self._on_change(self.status)
            except Exception:  # pragma: no cover - notification is best effort
                log.exception("sync status listener failed")

    async def _run(self) -> None:
        self.status = SyncStatus(
            state="running",
            started_at=datetime.now(UTC).isoformat(timespec="seconds"),
            last_sync=self.db.get_meta("last_sync"),
        )
        self._notify()
        client: DiscogsClient | None = None
        try:
            client = self._factory()
            rows: list[dict[str, Any]] = []
            async for page, pages, items in client.collection_pages():
                rows.extend(parse_item(i) for i in items)
                self.status.page, self.status.pages, self.status.fetched = page, pages, len(rows)
                self._notify()
            added, updated, removed = await asyncio.to_thread(self.db.replace_collection, rows)
            now = datetime.now(UTC).isoformat(timespec="seconds")
            self.db.set_meta("last_sync", now)
            self.status.added, self.status.updated, self.status.removed = added, updated, removed
            self.status.state = "done"
            self.status.last_sync = now
        except Exception as exc:  # surface the error to the UI rather than dying quietly
            log.exception("collection sync failed")
            self.status.state = "error"
            self.status.error = str(exc)
        finally:
            self.status.finished_at = datetime.now(UTC).isoformat(timespec="seconds")
            if client is not None:
                await client.aclose()
            self._notify()
