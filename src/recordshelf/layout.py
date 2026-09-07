"""Resolve the YAML layout config into boxes with LED ranges."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from .models import LayoutConfig

EXAMPLE_YAML = """\
# recordShelf layout. Edit here or in the web app (Layout page).
version: 1
name: Living room Kallax
rows: 5
cols: 5
capacity_default: 40        # estimated records per box, used until you calibrate
record_order: row-major     # how records flow through boxes: row-major | column-major | explicit

controllers:
  # type: wled  -> GLEDOPTO / any WLED board, driven over DDP (UDP 4048)
  # type: opc   -> legacy Fadecandy server (Open Pixel Control)
  # type: none  -> no hardware, use the virtual shelf in the browser
  - id: wled-a
    type: none
    host: 192.168.1.50
    led_count: 400
  - id: wled-b
    type: none
    host: 192.168.1.51
    led_count: 100

# One entry per physical strip. `boxes` lists the boxes in the order the LEDs pass
# them, so a strip wired right-to-left just lists its boxes right-to-left.
# WLED presents every output on a board as one continuous LED index space, so a board with
# four outputs of 100 LEDs is indices 0-399; `start` picks where each strip begins.
strips:
  - {id: row0, controller: wled-a, start: 0,   count: 100, boxes: [[0,0],[0,1],[0,2],[0,3],[0,4]]}
  - {id: row1, controller: wled-a, start: 100, count: 100, boxes: [[1,0],[1,1],[1,2],[1,3],[1,4]]}
  - {id: row2, controller: wled-a, start: 200, count: 100, boxes: [[2,0],[2,1],[2,2],[2,3],[2,4]]}
  - {id: row3, controller: wled-a, start: 300, count: 100, boxes: [[3,0],[3,1],[3,2],[3,3],[3,4]]}
  - {id: row4, controller: wled-b, start: 0,   count: 100, boxes: [[4,0],[4,1],[4,2],[4,3],[4,4]]}

# Boxes default to kind: records. Override the ones that hold something else.
boxes:
  # - {at: [0,0], kind: other, label: Turntable}
  # - {at: [4,4], kind: empty}
  # - {at: [2,2], capacity: 30}
"""


@dataclass(frozen=True)
class Box:
    id: str
    row: int
    col: int
    kind: str
    label: str
    capacity: int
    controller: str | None
    led_start: int
    led_count: int
    reversed: bool
    global_start: int

    @property
    def has_leds(self) -> bool:
        return self.controller is not None and self.led_count > 0

    @property
    def pixels(self) -> range:
        if not self.has_leds:
            return range(0)
        return range(self.global_start, self.global_start + self.led_count)

    def pixel_for(self, index_in_box: int, count_in_box: int) -> int | None:
        """Map the n-th of m records in this box to a global pixel index."""
        if not self.has_leds:
            return None
        if count_in_box <= 0:
            k = 0
        else:
            frac = (index_in_box + 0.5) / count_in_box
            k = min(self.led_count - 1, max(0, int(frac * self.led_count)))
        if self.reversed:
            k = self.led_count - 1 - k
        return self.global_start + k

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "row": self.row,
            "col": self.col,
            "kind": self.kind,
            "label": self.label,
            "capacity": self.capacity,
            "controller": self.controller,
            "led_start": self.led_start,
            "led_count": self.led_count,
            "reversed": self.reversed,
            "global_start": self.global_start,
        }


def box_id(row: int, col: int) -> str:
    return f"r{row}c{col}"


class ResolvedLayout:
    def __init__(self, cfg: LayoutConfig):
        self.cfg = cfg
        self.controller_offsets: dict[str, int] = {}
        offset = 0
        for c in cfg.controllers:
            self.controller_offsets[c.id] = offset
            offset += c.led_count
        self.total_pixels = offset

        assigned: dict[tuple[int, int], tuple[str, int, int, bool]] = {}
        for strip in cfg.strips:
            n = len(strip.boxes)
            base, rem = divmod(strip.count, n)
            cursor = strip.start
            for i, (r, c) in enumerate(strip.boxes):
                count = base + (1 if i < rem else 0)
                rev = False
                if n > 1:
                    nxt = strip.boxes[i + 1] if i + 1 < n else None
                    prev = strip.boxes[i - 1] if i > 0 else None
                    if nxt is not None and nxt[0] == r:
                        rev = nxt[1] < c
                    elif prev is not None and prev[0] == r:
                        rev = prev[1] > c
                assigned[(r, c)] = (strip.controller, cursor, count, rev)
                cursor += count

        overrides = {tuple(b.at): b for b in cfg.boxes}
        self.boxes: list[Box] = []
        for r in range(cfg.rows):
            for c in range(cfg.cols):
                ov = overrides.get((r, c))
                la = assigned.get((r, c))
                rev = la[3] if la else False
                if ov is not None and ov.reversed is not None:
                    rev = ov.reversed
                self.boxes.append(
                    Box(
                        id=box_id(r, c),
                        row=r,
                        col=c,
                        kind=ov.kind if ov else "records",
                        label=(ov.label if ov else "") or "",
                        capacity=(ov.capacity if ov and ov.capacity else cfg.capacity_default),
                        controller=la[0] if la else None,
                        led_start=la[1] if la else 0,
                        led_count=la[2] if la else 0,
                        reversed=rev,
                        global_start=(self.controller_offsets[la[0]] + la[1]) if la else -1,
                    )
                )
        self.by_id: dict[str, Box] = {b.id: b for b in self.boxes}

        if cfg.record_order == "row-major":
            ordered = self.boxes
        elif cfg.record_order == "column-major":
            ordered = sorted(self.boxes, key=lambda b: (b.col, b.row))
        else:
            ordered = [self.by_id[box_id(r, c)] for r, c in cfg.record_box_order]
        self.record_boxes: list[Box] = [b for b in ordered if b.kind == "records"]

    def controller_slice(self, controller_id: str) -> tuple[int, int]:
        offset = self.controller_offsets[controller_id]
        count = next(c.led_count for c in self.cfg.controllers if c.id == controller_id)
        return offset, count

    def global_pixel(self, controller_id: str, index: int) -> int:
        return self.controller_offsets[controller_id] + index

    def to_dict(self) -> dict:
        return {
            "name": self.cfg.name,
            "rows": self.cfg.rows,
            "cols": self.cfg.cols,
            "total_pixels": self.total_pixels,
            "controllers": [
                {
                    "id": c.id,
                    "type": c.type,
                    "host": c.host,
                    "led_count": c.led_count,
                    "offset": self.controller_offsets[c.id],
                }
                for c in self.cfg.controllers
            ],
            "boxes": [b.to_dict() for b in self.boxes],
            "record_boxes": [b.id for b in self.record_boxes],
        }


def load_layout(path: Path, create_default: bool = True) -> LayoutConfig:
    if not path.exists():
        if not create_default:
            raise FileNotFoundError(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(EXAMPLE_YAML)
    data = yaml.safe_load(path.read_text()) or {}
    return LayoutConfig.model_validate(data)


def save_layout(path: Path, cfg: LayoutConfig) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = cfg.model_dump(mode="json", exclude_defaults=False)
    path.write_text(yaml.safe_dump(data, sort_keys=False))
