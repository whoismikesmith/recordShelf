"""Placement: where each record physically is, from the shelf order plus box boundaries."""

from __future__ import annotations

from dataclasses import dataclass

from .distribute import distribute, starts_from_counts
from .layout import Box, ResolvedLayout


@dataclass(frozen=True)
class Located:
    instance_id: int
    position: int
    box: Box
    index_in_box: int
    count_in_box: int
    pixel: int | None


@dataclass(frozen=True)
class BoxRange:
    box: Box
    start: int
    end: int  # exclusive

    @property
    def count(self) -> int:
        return self.end - self.start


def _fill_boundaries(boxes: list[Box], known: dict[str, int], total: int) -> list[int]:
    """Return a first_position per record box.

    Known boundaries (from calibration) are kept, clamped, and made monotonic. Gaps between
    known boundaries are filled by spreading that span across the boxes in proportion to
    their capacities. The first record box always starts at position 0.
    """
    n = len(boxes)
    if n == 0:
        return []
    firsts: list[int | None] = [known.get(b.id) for b in boxes]
    firsts[0] = 0
    prev = 0
    for i in range(n):
        v = firsts[i]
        if v is not None:
            v = max(prev, min(v, total))
            firsts[i] = v
            prev = v
    i = 1
    while i < n:
        if firsts[i] is not None:
            i += 1
            continue
        j = i
        while j < n and firsts[j] is None:
            j += 1
        lo = firsts[i - 1]
        hi = firsts[j] if j < n else total
        assert lo is not None and hi is not None
        span = boxes[i - 1 : j]
        counts = distribute([b.capacity for b in span], hi - lo)
        starts = starts_from_counts(counts, lo)
        for k in range(i, j):
            firsts[k] = starts[k - (i - 1)]
        i = j
    out = [int(v) if v is not None else total for v in firsts]
    for k in range(1, n):
        out[k] = max(out[k], out[k - 1])
    return out


class Placement:
    def __init__(self, order: list[int], boundaries: dict[str, int], layout: ResolvedLayout):
        self.order = order
        self.position = {iid: i for i, iid in enumerate(order)}
        self.layout = layout
        boxes = layout.record_boxes
        firsts = _fill_boundaries(boxes, boundaries, len(order))
        self.ranges: list[BoxRange] = []
        for i, box in enumerate(boxes):
            start = firsts[i]
            end = firsts[i + 1] if i + 1 < len(boxes) else len(order)
            self.ranges.append(BoxRange(box, start, max(start, end)))
        self._range_by_box = {r.box.id: r for r in self.ranges}

    @property
    def boundaries(self) -> dict[str, int]:
        return {r.box.id: r.start for r in self.ranges}

    def range_for_position(self, pos: int) -> BoxRange | None:
        for r in self.ranges:
            if r.start <= pos < r.end:
                return r
        return None

    def box_of(self, instance_id: int) -> Box | None:
        pos = self.position.get(instance_id)
        if pos is None:
            return None
        r = self.range_for_position(pos)
        return r.box if r else None

    def locate(self, instance_id: int) -> Located | None:
        pos = self.position.get(instance_id)
        if pos is None:
            return None
        r = self.range_for_position(pos)
        if r is None:
            return None
        idx = pos - r.start
        return Located(
            instance_id=instance_id,
            position=pos,
            box=r.box,
            index_in_box=idx,
            count_in_box=r.count,
            pixel=r.box.pixel_for(idx, r.count),
        )

    def records_in_box(self, box_id: str) -> list[int]:
        r = self._range_by_box.get(box_id)
        if r is None:
            return []
        return self.order[r.start : r.end]

    def pixel_map(self) -> dict[int, int]:
        """Map global pixel -> first instance_id that lands on it (for scene painting)."""
        out: dict[int, int] = {}
        for r in self.ranges:
            for idx in range(r.count):
                px = r.box.pixel_for(idx, r.count)
                if px is not None and px not in out:
                    out[px] = self.order[r.start + idx]
        return out
