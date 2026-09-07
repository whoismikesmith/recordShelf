from __future__ import annotations

from collections import Counter

from fastapi import APIRouter, Depends, HTTPException, Query

from ..models import ReleaseOut
from ..search import matches
from ..services import Services
from .deps import svc

router = APIRouter(tags=["releases"])


def _sorted(items: list[ReleaseOut], sort: str) -> list[ReleaseOut]:
    if sort == "artist":
        return sorted(items, key=lambda r: (r.artist_sort, r.year or 9999, r.title.casefold()))
    if sort == "title":
        return sorted(items, key=lambda r: r.title.casefold())
    if sort == "year":
        return sorted(items, key=lambda r: (r.year or 9999, r.artist_sort))
    if sort == "added":
        return sorted(items, key=lambda r: r.date_added or "", reverse=True)
    if sort == "rating":
        return sorted(items, key=lambda r: (-r.rating, r.artist_sort))
    # position: shelf first in shelf order, then inbox alphabetically
    return sorted(
        items,
        key=lambda r: (
            (0, r.placed.position, "") if r.placed else (1, 0, r.artist_sort + r.title.casefold())
        ),
    )


@router.get("/releases")
async def list_releases(
    q: str = "",
    description: str | None = None,
    genre: str | None = None,
    style: str | None = None,
    decade: str | None = None,
    section: str | None = None,
    box: str | None = None,
    folder: int | None = None,
    on_shelf: bool | None = None,
    sort: str = Query("position", pattern="^(position|artist|title|year|added|rating)$"),
    limit: int = Query(5000, ge=1, le=5000),
    offset: int = Query(0, ge=0),
    s: Services = Depends(svc),
) -> dict:
    items = s.all_out()
    if q:
        items = [r for r in items if matches(r, q)]
    if description:
        items = [r for r in items if description in r.descriptions]
    if genre:
        items = [r for r in items if genre in r.genres]
    if style:
        items = [r for r in items if style in r.styles]
    if decade:
        items = [r for r in items if r.decade == decade]
    if section is not None:
        items = [r for r in items if r.section == section]
    if box:
        items = [r for r in items if r.placed and r.placed.box_id == box]
    if folder is not None:
        items = [r for r in items if r.folder_id == folder]
    if on_shelf is not None:
        items = [r for r in items if r.on_shelf == on_shelf]
    items = _sorted(items, sort)
    total = len(items)
    return {"items": [r.model_dump() for r in items[offset : offset + limit]], "total": total}


@router.get("/releases/{instance_id}")
async def get_release(instance_id: int, s: Services = Depends(svc)) -> dict:
    r = s.db.get_release(instance_id)
    if r is None:
        raise HTTPException(404, f"no release {instance_id}")
    return s.release_out(r, s.placement(), s.scheme(), s.db.get_overrides()).model_dump()


@router.get("/facets")
async def facets(s: Services = Depends(svc)) -> dict:
    items = s.all_out()

    def count(values) -> list[dict]:
        c = Counter(values)
        return [
            {"value": v, "count": n} for v, n in sorted(c.items(), key=lambda t: (-t[1], str(t[0])))
        ]

    return {
        "descriptions": count(d for r in items for d in r.descriptions),
        "genres": count(g for r in items for g in r.genres),
        "styles": count(st for r in items for st in r.styles),
        "decades": sorted(count(r.decade for r in items), key=lambda d: d["value"]),
        "labels": count(r.label for r in items if r.label)[:40],
        "sections": count(r.section for r in items if r.section),
        "folders": count(r.folder_id for r in items if r.folder_id is not None),
        "boxes": count(r.placed.box_id for r in items if r.placed),
    }
