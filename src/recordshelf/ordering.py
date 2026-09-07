"""Turn a Scheme into a target shelf order and a box assignment (the 'plan')."""

from __future__ import annotations

from dataclasses import dataclass, field

from .distribute import distribute, starts_from_counts
from .layout import Box
from .models import Override, Release, Scheme

VARIOUS = ("various", "various artists", "v/a", "va")


def eligible(release: Release, scheme: Scheme, override: Override | None) -> bool:
    """Should this record live on the shelf at all?"""
    if override is not None and override.excluded:
        return False
    if scheme.include_folders and release.folder_id not in scheme.include_folders:
        return False
    if scheme.include_descriptions:
        wanted = {d.casefold() for d in scheme.include_descriptions}
        have = {d.casefold() for d in release.descriptions}
        if not (wanted & have):
            return False
    return True


def section_for(release: Release, scheme: Scheme, override: Override | None) -> str:
    if override is not None and override.section:
        return override.section
    by = scheme.section_by
    if by == "none":
        return ""
    if by in ("genre", "style"):
        for s in release.styles:
            if s in scheme.style_map:
                return scheme.style_map[s]
        for g in release.genres:
            if g in scheme.genre_map:
                return scheme.genre_map[g]
        if by == "style" and release.styles:
            return release.styles[0]
        return release.genres[0] if release.genres else "Other"
    if by == "decade":
        return release.decade
    if by == "label":
        return release.label or "Unknown"
    if by == "format":
        return release.descriptions[0] if release.descriptions else (release.format or "Unknown")
    if by == "folder":
        return str(release.folder_id or 0)
    return ""


def section_rank(section: str, scheme: Scheme) -> tuple[int, str]:
    try:
        return scheme.section_order.index(section), ""
    except ValueError:
        return len(scheme.section_order), section.casefold()


def is_various(release: Release) -> bool:
    return release.artist_sort in VARIOUS or release.artist.casefold() in VARIOUS


def sort_key(release: Release, scheme: Scheme, override: Override | None) -> tuple:
    key: list = []
    if override is not None and override.sort_key:
        key.append(override.sort_key.casefold())
    for k in scheme.within:
        if k == "artist":
            key.append(
                (1 if (scheme.various_last and is_various(release)) else 0, release.artist_sort)
            )
        elif k == "title":
            key.append(release.title.casefold())
        elif k == "year":
            key.append(release.year or 9999)
        elif k == "added":
            key.append(release.date_added or "")
        elif k == "rating":
            key.append(-release.rating)
        elif k == "label":
            key.append((release.label or "").casefold())
        elif k == "catno":
            key.append((release.catno or "").casefold())
    key.append(release.instance_id)
    return tuple(key)


@dataclass
class PlanItem:
    instance_id: int
    position: int
    section: str
    box_id: str | None
    current_box_id: str | None = None

    @property
    def moved(self) -> bool:
        return self.current_box_id is not None and self.current_box_id != self.box_id


@dataclass
class PlanBox:
    box_id: str
    first_position: int
    count: int
    capacity: int
    sections: list[str] = field(default_factory=list)

    @property
    def overflow(self) -> bool:
        return self.count > self.capacity


@dataclass
class Plan:
    items: list[PlanItem]
    boxes: list[PlanBox]
    unassigned: int
    excluded: int

    @property
    def order(self) -> list[int]:
        return [i.instance_id for i in self.items]

    @property
    def boundaries(self) -> dict[str, int]:
        return {b.box_id: b.first_position for b in self.boxes}

    @property
    def moved_count(self) -> int:
        return sum(1 for i in self.items if i.moved)

    def to_dict(self) -> dict:
        return {
            "items": [
                {
                    "instance_id": i.instance_id,
                    "position": i.position,
                    "section": i.section,
                    "box_id": i.box_id,
                    "current_box_id": i.current_box_id,
                    "moved": i.moved,
                }
                for i in self.items
            ],
            "boxes": [
                {
                    "box_id": b.box_id,
                    "first_position": b.first_position,
                    "count": b.count,
                    "capacity": b.capacity,
                    "sections": b.sections,
                    "overflow": b.overflow,
                }
                for b in self.boxes
            ],
            "unassigned": self.unassigned,
            "excluded": self.excluded,
            "moved_count": self.moved_count,
            "total": len(self.items),
        }


def ordered_releases(
    releases: list[Release], scheme: Scheme, overrides: dict[int, Override]
) -> tuple[list[tuple[Release, str]], int]:
    """Sort eligible releases by the scheme. Returns ([(release, section)], excluded_count)."""
    keep: list[tuple[tuple, Release, str]] = []
    excluded = 0
    for r in releases:
        ov = overrides.get(r.instance_id)
        if not eligible(r, scheme, ov):
            excluded += 1
            continue
        sec = section_for(r, scheme, ov)
        keep.append(((section_rank(sec, scheme), sort_key(r, scheme, ov)), r, sec))
    keep.sort(key=lambda t: t[0])
    return [(r, sec) for _, r, sec in keep], excluded


def build_plan(
    releases: list[Release],
    scheme: Scheme,
    overrides: dict[int, Override],
    record_boxes: list[Box],
    current_box_of: dict[int, str] | None = None,
) -> Plan:
    ordered, excluded = ordered_releases(releases, scheme, overrides)
    current_box_of = current_box_of or {}
    items: list[PlanItem] = []
    boxes: list[PlanBox] = []
    total = len(ordered)

    counts = distribute([b.capacity for b in record_boxes], total)
    starts = starts_from_counts(counts)
    for box, start, count in zip(record_boxes, starts, counts, strict=True):
        pb = PlanBox(box_id=box.id, first_position=start, count=count, capacity=box.capacity)
        for pos in range(start, start + count):
            r, sec = ordered[pos]
            items.append(
                PlanItem(r.instance_id, pos, sec, box.id, current_box_of.get(r.instance_id))
            )
            if sec and sec not in pb.sections:
                pb.sections.append(sec)
        boxes.append(pb)

    unassigned = 0
    if not record_boxes:
        for pos, (r, sec) in enumerate(ordered):
            items.append(PlanItem(r.instance_id, pos, sec, None, current_box_of.get(r.instance_id)))
            unassigned += 1

    return Plan(items=items, boxes=boxes, unassigned=unassigned, excluded=excluded)
