"""Full Discogs release details: credits, companies, country, community stats, prices.

The collection sync only gets `basic_information`. Details need one request per release, so
they are fetched separately ("enrich"), resumably, into their own SQLite file. That file is a
cache: deleting it loses nothing that cannot be fetched again, and enrichment only ever reads
the shelf database.
"""

from __future__ import annotations

import asyncio
import json
import logging
import sqlite3
import threading
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import httpx
from pydantic import BaseModel

from .discogs import DiscogsClient, DiscogsError
from .models import Override, Release, Scheme
from .ordering import eligible

log = logging.getLogger(__name__)

RELEASE, PRICES = "release", "prices"

SCHEMA = """
CREATE TABLE IF NOT EXISTS fetched (
  release_id INTEGER NOT NULL,
  kind       TEXT NOT NULL,
  fetched_at TEXT NOT NULL,
  status     INTEGER NOT NULL,
  currency   TEXT,
  data       TEXT NOT NULL DEFAULT '{}',
  PRIMARY KEY (release_id, kind)
);
"""


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


class DetailsStore:
    """One row per (release_id, kind): the raw JSON Discogs returned, or the HTTP error status."""

    def __init__(self, path: Path | str = ":memory:"):
        self.path = str(path)
        if self.path != ":memory:":
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.path, check_same_thread=False, timeout=30)
        self._conn.row_factory = sqlite3.Row
        self._lock = threading.RLock()
        self._parsed: tuple[tuple, dict[int, ReleaseDetails]] | None = None
        with self._lock:
            if self.path != ":memory:":
                self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.executescript(SCHEMA)

    def close(self) -> None:
        with self._lock:
            self._conn.close()

    def put(
        self,
        release_id: int,
        kind: str,
        data: dict[str, Any],
        status: int = 200,
        currency: str | None = None,
    ) -> None:
        with self._lock:
            self._conn.execute(
                "INSERT INTO fetched(release_id, kind, fetched_at, status, currency, data) "
                "VALUES(?,?,?,?,?,?) ON CONFLICT(release_id, kind) DO UPDATE SET "
                "fetched_at=excluded.fetched_at, status=excluded.status, "
                "currency=excluded.currency, data=excluded.data",
                (release_id, kind, _now(), status, currency, json.dumps(data)),
            )
            self._conn.commit()

    def fetched_at(self, kind: str) -> dict[int, str]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT release_id, fetched_at FROM fetched WHERE kind=?", (kind,)
            ).fetchall()
        return {r["release_id"]: r["fetched_at"] for r in rows}

    def raw(self, release_id: int, kind: str = RELEASE) -> dict[str, Any] | None:
        with self._lock:
            row = self._conn.execute(
                "SELECT data FROM fetched WHERE release_id=? AND kind=? AND status=200",
                (release_id, kind),
            ).fetchone()
        return json.loads(row["data"]) if row else None

    def counts(self) -> dict[str, int]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT kind, status=200 AS ok, COUNT(*) AS n FROM fetched GROUP BY kind, ok"
            ).fetchall()
        out = {RELEASE: 0, PRICES: 0, "failed": 0}
        for r in rows:
            if r["ok"]:
                out[r["kind"]] = r["n"]
            else:
                out["failed"] += r["n"]
        return out

    def details(self) -> dict[int, ReleaseDetails]:
        """Parsed details by release_id, re-parsed only when the table has changed."""
        with self._lock:
            version = tuple(
                self._conn.execute("SELECT COUNT(*), MAX(fetched_at) FROM fetched").fetchone()
            )
            if self._parsed is not None and self._parsed[0] == version:
                return self._parsed[1]
            rows = self._conn.execute(
                "SELECT release_id, kind, currency, data FROM fetched WHERE status=200"
            ).fetchall()
        releases: dict[int, dict] = {}
        prices: dict[int, dict] = {}
        currency: dict[int, str | None] = {}
        for r in rows:
            target = releases if r["kind"] == RELEASE else prices
            target[r["release_id"]] = json.loads(r["data"])
            if r["kind"] == RELEASE:
                currency[r["release_id"]] = r["currency"]
        out = {
            rid: parse_details(rid, data, prices.get(rid), currency.get(rid))
            for rid, data in releases.items()
        }
        with self._lock:
            self._parsed = (version, out)
        return out


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------


@dataclass
class ReleaseDetails:
    release_id: int
    credits: dict[str, set[str]] = field(default_factory=dict)  # role -> Discogs artist names
    companies: dict[str, set[str]] = field(default_factory=dict)  # "Pressed By" -> names
    country: str | None = None
    have: int = 0
    want: int = 0
    rating: float = 0.0
    rating_count: int = 0
    lowest_price: float | None = None
    num_for_sale: int = 0
    currency: str | None = None
    suggested: dict[str, float] = field(default_factory=dict)  # condition -> value
    suggested_currency: str | None = None


def split_roles(role: str) -> list[str]:
    """'Producer, Mixed By [Assistant]' -> ['Producer', 'Mixed By']. Brackets hold detail
    (instrument variants, track notes) and may contain commas themselves."""
    out: list[str] = []
    depth, cur = 0, []
    for ch in role or "":
        if ch == "[":
            depth += 1
        elif ch == "]":
            depth = max(0, depth - 1)
        elif ch == "," and depth == 0:
            out.append("".join(cur))
            cur = []
        elif depth == 0:
            cur.append(ch)
    out.append("".join(cur))
    return [r.strip() for r in out if r.strip()]


def parse_details(
    release_id: int,
    data: dict[str, Any],
    prices: dict[str, Any] | None = None,
    currency: str | None = None,
) -> ReleaseDetails:
    d = ReleaseDetails(release_id=release_id, currency=currency)
    people = list(data.get("extraartists") or [])
    for track in data.get("tracklist") or []:
        people.extend(track.get("extraartists") or [])
        for sub in track.get("sub_tracks") or []:
            people.extend(sub.get("extraartists") or [])
    for p in people:
        name = (p.get("name") or "").strip()
        if not name:
            continue
        for role in split_roles(p.get("role") or ""):
            d.credits.setdefault(role, set()).add(name)
    for c in data.get("companies") or []:
        name, kind = (c.get("name") or "").strip(), (c.get("entity_type_name") or "").strip()
        if name and kind:
            d.companies.setdefault(kind, set()).add(name)
    d.country = data.get("country") or None
    community = data.get("community") or {}
    d.have, d.want = int(community.get("have") or 0), int(community.get("want") or 0)
    rating = community.get("rating") or {}
    d.rating, d.rating_count = float(rating.get("average") or 0), int(rating.get("count") or 0)
    lowest = data.get("lowest_price")
    d.lowest_price = float(lowest) if lowest is not None else None
    d.num_for_sale = int(data.get("num_for_sale") or 0)
    for condition, v in (prices or {}).items():
        if isinstance(v, dict) and v.get("value") is not None:
            d.suggested[condition] = float(v["value"])
            d.suggested_currency = v.get("currency") or d.suggested_currency
    return d


# ---------------------------------------------------------------------------
# Enrichment job
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Target:
    release_id: int
    label: str
    shelf: bool


def enrich_targets(
    releases: Iterable[Release],
    scheme: Scheme,
    overrides: dict[int, Override],
    placed: Iterable[int] = (),
) -> list[Target]:
    """One target per release id: shelf records (placed or eligible) first, then the rest."""
    placed = set(placed)
    best: dict[int, Target] = {}
    for r in sorted(releases, key=lambda r: (r.artist_sort, r.title.casefold(), r.instance_id)):
        shelf = r.instance_id in placed or eligible(r, scheme, overrides.get(r.instance_id))
        prev = best.get(r.release_id)
        if prev is None or (shelf and not prev.shelf):
            best[r.release_id] = Target(r.release_id, f"{r.artist} - {r.title}", shelf)
    return sorted(best.values(), key=lambda t: not t.shelf)


class EnrichStatus(BaseModel):
    state: str = "idle"  # idle | running | done | error
    total: int = 0
    done: int = 0
    fetched: int = 0
    cached: int = 0
    prices: int = 0
    errors: int = 0
    prices_skipped: str | None = None
    current: str | None = None
    error: str | None = None
    started_at: str | None = None
    finished_at: str | None = None


# Price suggestions are refused account-wide (no token, no seller settings) with these.
_ACCOUNT_REFUSALS = {401, 403, 422}


class EnrichManager:
    def __init__(
        self,
        store: DetailsStore,
        client_factory: Callable[[], DiscogsClient],
        on_change: Callable[[EnrichStatus], Any] | None = None,
        max_consecutive_errors: int = 5,
    ):
        self.store = store
        self._factory = client_factory
        self._on_change = on_change
        self.max_consecutive_errors = max_consecutive_errors
        self._task: asyncio.Task | None = None
        self.status = EnrichStatus()

    @property
    def running(self) -> bool:
        return self._task is not None and not self._task.done()

    def start(
        self, targets: list[Target], refresh_days: float | None = None, prices: bool = True
    ) -> bool:
        if self.running:
            return False
        self._task = asyncio.create_task(self._run(targets, refresh_days, prices))
        return True

    async def wait(self) -> EnrichStatus:
        if self._task is not None:
            await self._task
        return self.status

    def _notify(self) -> None:
        if self._on_change:
            try:
                self._on_change(self.status)
            except Exception:  # pragma: no cover - notification is best effort
                log.exception("enrich status listener failed")

    async def _run(self, targets: list[Target], refresh_days: float | None, prices: bool) -> None:
        st = self.status = EnrichStatus(state="running", total=len(targets), started_at=_now())
        self._notify()
        cutoff = (
            (datetime.now(UTC) - timedelta(days=refresh_days)).isoformat(timespec="seconds")
            if refresh_days is not None
            else None
        )
        have = self.store.fetched_at(RELEASE)
        have_prices = self.store.fetched_at(PRICES)

        def needed(cache: dict[int, str], rid: int) -> bool:
            return rid not in cache or (cutoff is not None and cache[rid] <= cutoff)

        client: DiscogsClient | None = None
        streak = 0
        try:
            client = self._factory()
            if prices and not client.token:
                prices, st.prices_skipped = False, "price suggestions need a Discogs token"
            currency = None
            if client.token:
                try:
                    currency = await client.currency()
                except (DiscogsError, httpx.HTTPError) as exc:
                    log.warning("could not read account currency: %s", exc)
            for t in targets:
                st.current = t.label
                want_release = needed(have, t.release_id)
                want_prices = prices and needed(have_prices, t.release_id)
                if not (want_release or want_prices):
                    st.cached += 1
                    st.done += 1
                    self._notify()
                    continue
                failed = False
                if want_release:
                    try:
                        data = await client.release(t.release_id, currency)
                        self.store.put(t.release_id, RELEASE, data, currency=currency)
                        st.fetched += 1
                    except DiscogsError as exc:
                        if exc.status == 404:
                            self.store.put(t.release_id, RELEASE, {"message": str(exc)}, 404)
                        else:
                            failed = True
                            st.errors += 1
                            log.warning("release %s: %s", t.release_id, exc)
                    except httpx.HTTPError as exc:
                        failed = True
                        st.errors += 1
                        log.warning("release %s: %s", t.release_id, exc)
                if want_prices and prices and not failed:
                    try:
                        data = await client.price_suggestions(t.release_id)
                        self.store.put(t.release_id, PRICES, data)
                        st.prices += 1
                    except DiscogsError as exc:
                        if exc.status in _ACCOUNT_REFUSALS:
                            prices, st.prices_skipped = False, str(exc)
                        elif exc.status == 404:
                            self.store.put(t.release_id, PRICES, {"message": str(exc)}, 404)
                        else:
                            failed = True
                            st.errors += 1
                            log.warning("prices %s: %s", t.release_id, exc)
                    except httpx.HTTPError as exc:
                        failed = True
                        st.errors += 1
                        log.warning("prices %s: %s", t.release_id, exc)
                streak = streak + 1 if failed else 0
                if streak >= self.max_consecutive_errors:
                    raise DiscogsError(f"{streak} requests in a row failed; stopping")
                st.done += 1
                self._notify()
            st.state = "done"
        except Exception as exc:  # surface the error to the UI rather than dying quietly
            log.exception("enrich failed")
            st.state = "error"
            st.error = str(exc)
        finally:
            st.current = None
            st.finished_at = _now()
            if client is not None:
                await client.aclose()
            self._notify()
