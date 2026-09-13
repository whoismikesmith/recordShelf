"""SQLite storage. One connection, one lock; the collection is small."""

from __future__ import annotations

import json
import sqlite3
import threading
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from .models import Override, Release

SCHEMA = """
CREATE TABLE IF NOT EXISTS releases (
  instance_id   INTEGER PRIMARY KEY,
  release_id    INTEGER NOT NULL,
  master_id     INTEGER,
  title         TEXT NOT NULL,
  artist        TEXT NOT NULL,
  artist_sort   TEXT NOT NULL,
  year          INTEGER,
  label         TEXT,
  catno         TEXT,
  format        TEXT,
  descriptions  TEXT NOT NULL DEFAULT '[]',
  genres        TEXT NOT NULL DEFAULT '[]',
  styles        TEXT NOT NULL DEFAULT '[]',
  rating        INTEGER NOT NULL DEFAULT 0,
  date_added    TEXT,
  folder_id     INTEGER,
  thumb         TEXT,
  cover         TEXT,
  raw           TEXT NOT NULL DEFAULT '{}'
);
CREATE TABLE IF NOT EXISTS shelf_order (
  position    INTEGER PRIMARY KEY,
  instance_id INTEGER NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS box_boundaries (
  box_id         TEXT PRIMARY KEY,
  first_position INTEGER NOT NULL,
  source         TEXT NOT NULL DEFAULT 'derived'
);
CREATE TABLE IF NOT EXISTS overrides (
  instance_id INTEGER PRIMARY KEY,
  section     TEXT,
  sort_key    TEXT,
  excluded    INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS meta (
  key   TEXT PRIMARY KEY,
  value TEXT NOT NULL
);
"""

JSON_COLS = ("descriptions", "genres", "styles")


def _row_to_release(row: sqlite3.Row) -> Release:
    d = dict(row)
    d.pop("raw", None)
    for col in JSON_COLS:
        d[col] = json.loads(d[col] or "[]")
    return Release(**d)


class Database:
    def __init__(self, path: Path | str = ":memory:", readonly: bool = False):
        """`readonly` opens an existing file with SQLite's mode=ro: no schema setup, no writes."""
        self.path = str(path)
        self._lock = threading.RLock()
        if readonly:
            uri = Path(self.path).resolve().as_uri() + "?mode=ro"
            self._conn = sqlite3.connect(uri, uri=True, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
            return
        if self.path != ":memory:":
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        with self._lock:
            if self.path != ":memory:":
                self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.executescript(SCHEMA)
            self._migrate()

    def _migrate(self) -> None:
        cols = {r["name"] for r in self._conn.execute("PRAGMA table_info(box_boundaries)")}
        if "source" not in cols:
            self._conn.execute(
                "ALTER TABLE box_boundaries ADD COLUMN source TEXT NOT NULL DEFAULT 'derived'"
            )
            self._conn.commit()

    def close(self) -> None:
        with self._lock:
            self._conn.close()

    # -- generic -----------------------------------------------------------

    def query(self, sql: str, params: tuple | dict = ()) -> list[sqlite3.Row]:
        with self._lock:
            return self._conn.execute(sql, params).fetchall()

    def execute(self, sql: str, params: tuple | dict = ()) -> None:
        with self._lock:
            self._conn.execute(sql, params)
            self._conn.commit()

    # -- meta --------------------------------------------------------------

    def get_meta(self, key: str, default: str | None = None) -> str | None:
        rows = self.query("SELECT value FROM meta WHERE key=?", (key,))
        return rows[0]["value"] if rows else default

    def set_meta(self, key: str, value: str) -> None:
        self.execute(
            "INSERT INTO meta(key,value) VALUES(?,?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, value),
        )

    def get_json(self, key: str, default: Any = None) -> Any:
        raw = self.get_meta(key)
        return json.loads(raw) if raw is not None else default

    def set_json(self, key: str, value: Any) -> None:
        self.set_meta(key, json.dumps(value))

    # -- releases ----------------------------------------------------------

    def list_releases(self) -> list[Release]:
        return [_row_to_release(r) for r in self.query("SELECT * FROM releases")]

    def basic_info(self) -> dict[int, dict[str, Any]]:
        """Discogs basic_information per instance: every artist, label and format, not just
        the first ones the columns keep."""
        rows = self.query("SELECT instance_id, raw FROM releases")
        return {
            r["instance_id"]: json.loads(r["raw"] or "{}").get("basic_information") or {}
            for r in rows
        }

    def get_release(self, instance_id: int) -> Release | None:
        rows = self.query("SELECT * FROM releases WHERE instance_id=?", (instance_id,))
        return _row_to_release(rows[0]) if rows else None

    def replace_collection(self, rows: Iterable[dict[str, Any]]) -> tuple[int, int, int]:
        """Upsert every row and delete anything not present. Returns (added, updated, removed)."""
        rows = list(rows)
        with self._lock:
            before = {
                r["instance_id"] for r in self._conn.execute("SELECT instance_id FROM releases")
            }
            incoming = {r["instance_id"] for r in rows}
            for r in rows:
                payload = dict(r)
                for col in JSON_COLS:
                    payload[col] = json.dumps(payload.get(col) or [])
                payload["raw"] = json.dumps(payload.get("raw") or {})
                cols = ",".join(payload)
                marks = ",".join("?" * len(payload))
                updates = ",".join(f"{c}=excluded.{c}" for c in payload if c != "instance_id")
                self._conn.execute(
                    f"INSERT INTO releases({cols}) VALUES({marks}) "
                    f"ON CONFLICT(instance_id) DO UPDATE SET {updates}",
                    tuple(payload.values()),
                )
            removed = before - incoming
            for iid in removed:
                self._conn.execute("DELETE FROM releases WHERE instance_id=?", (iid,))
                self._conn.execute("DELETE FROM shelf_order WHERE instance_id=?", (iid,))
                self._conn.execute("DELETE FROM overrides WHERE instance_id=?", (iid,))
            self._conn.commit()
            if removed:
                self._renumber()
        return len(incoming - before), len(incoming & before), len(removed)

    # -- shelf order -------------------------------------------------------

    def get_order(self) -> list[int]:
        return [
            r["instance_id"]
            for r in self.query("SELECT instance_id FROM shelf_order ORDER BY position")
        ]

    def set_order(self, ids: Iterable[int]) -> None:
        ids = list(dict.fromkeys(ids))
        with self._lock:
            self._conn.execute("DELETE FROM shelf_order")
            self._conn.executemany(
                "INSERT INTO shelf_order(position, instance_id) VALUES(?,?)",
                list(enumerate(ids)),
            )
            self._conn.commit()

    def insert_at(self, instance_id: int, position: int) -> None:
        order = [i for i in self.get_order() if i != instance_id]
        position = max(0, min(position, len(order)))
        order.insert(position, instance_id)
        self.set_order(order)

    def remove_from_order(self, instance_id: int) -> None:
        self.set_order(i for i in self.get_order() if i != instance_id)

    def _renumber(self) -> None:
        self.set_order(self.get_order())

    # -- boundaries --------------------------------------------------------
    # A boundary is the first shelf position in a box. 'calibrated' rows were set by the user
    # ("this record is first in this box"); 'derived' rows were materialised by the app so that
    # hand placements stay put. Placement treats both the same; only the badge differs.

    def get_boundaries(self) -> dict[str, int]:
        return {
            r["box_id"]: r["first_position"] for r in self.query("SELECT * FROM box_boundaries")
        }

    def calibrated_boxes(self) -> set[str]:
        rows = self.query("SELECT box_id FROM box_boundaries WHERE source='calibrated'")
        return {r["box_id"] for r in rows}

    def set_boundaries(
        self, boundaries: dict[str, int], calibrated: set[str] | None = None
    ) -> None:
        calibrated = calibrated or set()
        with self._lock:
            self._conn.execute("DELETE FROM box_boundaries")
            self._conn.executemany(
                "INSERT INTO box_boundaries(box_id, first_position, source) VALUES(?,?,?)",
                [
                    (b, p, "calibrated" if b in calibrated else "derived")
                    for b, p in boundaries.items()
                ],
            )
            self._conn.commit()

    def set_boundary(self, box_id: str, first_position: int, source: str = "calibrated") -> None:
        self.execute(
            "INSERT INTO box_boundaries(box_id, first_position, source) VALUES(?,?,?) "
            "ON CONFLICT(box_id) DO UPDATE SET first_position=excluded.first_position, "
            "source=excluded.source",
            (box_id, first_position, source),
        )

    def clear_boundary(self, box_id: str) -> None:
        self.execute("DELETE FROM box_boundaries WHERE box_id=?", (box_id,))

    # -- overrides ---------------------------------------------------------

    def get_overrides(self) -> dict[int, Override]:
        out: dict[int, Override] = {}
        for r in self.query("SELECT * FROM overrides"):
            out[r["instance_id"]] = Override(
                instance_id=r["instance_id"],
                section=r["section"],
                sort_key=r["sort_key"],
                excluded=bool(r["excluded"]),
            )
        return out

    def set_override(self, ov: Override) -> None:
        if ov.section is None and ov.sort_key is None and not ov.excluded:
            self.clear_override(ov.instance_id)
            return
        self.execute(
            "INSERT INTO overrides(instance_id, section, sort_key, excluded) VALUES(?,?,?,?) "
            "ON CONFLICT(instance_id) DO UPDATE SET section=excluded.section, "
            "sort_key=excluded.sort_key, excluded=excluded.excluded",
            (ov.instance_id, ov.section, ov.sort_key, int(ov.excluded)),
        )
        if ov.excluded:
            self.remove_from_order(ov.instance_id)

    def clear_override(self, instance_id: int) -> None:
        self.execute("DELETE FROM overrides WHERE instance_id=?", (instance_id,))
