"""Pydantic models shared by the database layer, the API, and the layout config."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

RGB = tuple[int, int, int]


# ---------------------------------------------------------------------------
# Collection
# ---------------------------------------------------------------------------


class Release(BaseModel):
    """One item in the Discogs collection (a collection *instance*, not a release id)."""

    instance_id: int
    release_id: int
    master_id: int | None = None
    title: str
    artist: str
    artist_sort: str
    year: int | None = None
    label: str | None = None
    catno: str | None = None
    format: str | None = None
    descriptions: list[str] = Field(default_factory=list)
    genres: list[str] = Field(default_factory=list)
    styles: list[str] = Field(default_factory=list)
    rating: int = 0
    date_added: str | None = None
    folder_id: int | None = None
    thumb: str | None = None
    cover: str | None = None

    @property
    def decade(self) -> str:
        return f"{self.year // 10 * 10}s" if self.year else "Unknown"


class Override(BaseModel):
    """Per-record user overrides for ordering and shelf membership."""

    instance_id: int
    section: str | None = None
    sort_key: str | None = None
    excluded: bool = False


# ---------------------------------------------------------------------------
# Ordering scheme
# ---------------------------------------------------------------------------

SortKey = Literal["artist", "title", "year", "added", "rating", "label", "catno"]
SectionBy = Literal["none", "genre", "style", "decade", "label", "format", "folder"]


class Scheme(BaseModel):
    """How the collection is meant to be ordered on the shelf."""

    section_by: SectionBy = "none"
    section_order: list[str] = Field(default_factory=list)
    style_map: dict[str, str] = Field(default_factory=dict)
    genre_map: dict[str, str] = Field(default_factory=dict)
    within: list[SortKey] = Field(default_factory=lambda: ["artist", "year", "title"])
    include_descriptions: list[str] = Field(default_factory=lambda: ["LP", '12"'])
    include_folders: list[int] = Field(default_factory=list)
    various_last: bool = True


# ---------------------------------------------------------------------------
# Layout config (config/shelf.yaml)
# ---------------------------------------------------------------------------

ControllerType = Literal["wled", "opc", "none"]
BoxKind = Literal["records", "other", "empty"]
RecordOrder = Literal["row-major", "column-major", "explicit"]


class ControllerConfig(BaseModel):
    id: str
    type: ControllerType = "wled"
    host: str = ""
    port: int | None = None
    led_count: int = Field(gt=0)
    ddp_type: int = 0x0B
    brightness: float = Field(default=1.0, ge=0.0, le=1.0)


class StripConfig(BaseModel):
    """A run of LEDs on one controller output, listed in the order the LEDs pass the boxes."""

    id: str
    controller: str
    start: int = Field(default=0, ge=0)
    count: int = Field(gt=0)
    boxes: list[tuple[int, int]] = Field(min_length=1)


class BoxOverride(BaseModel):
    at: tuple[int, int]
    kind: BoxKind = "records"
    label: str = ""
    capacity: int | None = Field(default=None, gt=0)
    reversed: bool | None = None


class LayoutConfig(BaseModel):
    version: int = 1
    name: str = "My shelf"
    rows: int = Field(default=5, gt=0, le=50)
    cols: int = Field(default=5, gt=0, le=50)
    capacity_default: int = Field(default=40, gt=0)
    record_order: RecordOrder = "row-major"
    record_box_order: list[tuple[int, int]] = Field(default_factory=list)
    controllers: list[ControllerConfig] = Field(default_factory=list)
    strips: list[StripConfig] = Field(default_factory=list)
    boxes: list[BoxOverride] = Field(default_factory=list)

    @field_validator("controllers", "strips", "boxes", "record_box_order", mode="before")
    @classmethod
    def _none_is_empty(cls, v):
        return [] if v is None else v

    @field_validator("controllers")
    @classmethod
    def _unique_controller_ids(cls, v: list[ControllerConfig]) -> list[ControllerConfig]:
        ids = [c.id for c in v]
        if len(ids) != len(set(ids)):
            raise ValueError("controller ids must be unique")
        return v

    @model_validator(mode="after")
    def _check_refs(self) -> LayoutConfig:
        ctrl = {c.id: c for c in self.controllers}
        seen: set[tuple[int, int]] = set()
        for s in self.strips:
            if s.controller not in ctrl:
                raise ValueError(f"strip {s.id!r} references unknown controller {s.controller!r}")
            if s.start + s.count > ctrl[s.controller].led_count:
                raise ValueError(
                    f"strip {s.id!r} needs LEDs {s.start}..{s.start + s.count - 1} "
                    f"but controller {s.controller!r} only has {ctrl[s.controller].led_count}"
                )
            for r, c in s.boxes:
                if not (0 <= r < self.rows and 0 <= c < self.cols):
                    raise ValueError(f"strip {s.id!r} covers box ({r},{c}) outside the grid")
                if (r, c) in seen:
                    raise ValueError(f"box ({r},{c}) is covered by more than one strip")
                seen.add((r, c))
        for b in self.boxes:
            r, c = b.at
            if not (0 <= r < self.rows and 0 <= c < self.cols):
                raise ValueError(f"box override at ({r},{c}) is outside the grid")
        if self.record_order == "explicit" and not self.record_box_order:
            raise ValueError("record_order 'explicit' needs record_box_order")
        return self


# ---------------------------------------------------------------------------
# API shapes
# ---------------------------------------------------------------------------


class Placed(BaseModel):
    position: int
    box_id: str
    index_in_box: int
    count_in_box: int
    pixel: int | None


class ReleaseOut(Release):
    section: str = ""
    on_shelf: bool = False
    excluded: bool = False
    placed: Placed | None = None
