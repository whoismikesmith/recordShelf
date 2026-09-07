from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..models import Override, Scheme
from ..services import NotFound, Services
from .deps import not_found, svc

router = APIRouter(tags=["shelf"])


def _order_view(s: Services) -> dict:
    placement = s.placement()
    scheme = s.scheme()
    overrides = s.db.get_overrides()
    releases = s.releases()
    boxes = []
    for rng in placement.ranges:
        items = []
        for iid in placement.order[rng.start : rng.end]:
            r = releases.get(iid)
            if r is not None:
                items.append(s.release_out(r, placement, scheme, overrides).model_dump())
        boxes.append(
            {
                "box_id": rng.box.id,
                "row": rng.box.row,
                "col": rng.box.col,
                "label": rng.box.label,
                "first_position": rng.start,
                "count": rng.count,
                "capacity": rng.box.capacity,
                "calibrated": rng.box.id in s.db.get_boundaries(),
                "has_leds": rng.box.has_leds,
                "items": items,
            }
        )
    inbox = [s.release_out(r, placement, scheme, overrides).model_dump() for r in s.inbox()]
    skipped = [s.release_out(r, placement, scheme, overrides).model_dump() for r in s.skipped()]
    excluded = [
        s.release_out(r, placement, scheme, overrides).model_dump()
        for r in releases.values()
        if (ov := overrides.get(r.instance_id)) and ov.excluded
    ]
    return {
        "boxes": boxes,
        "total": len(placement.order),
        "inbox": inbox,
        "skipped": skipped,
        "excluded": excluded,
    }


@router.get("/order")
async def get_order(s: Services = Depends(svc)) -> dict:
    return _order_view(s)


class OrderBody(BaseModel):
    order: list[int]


@router.put("/order")
async def put_order(body: OrderBody, s: Services = Depends(svc)) -> dict:
    known = s.releases()
    s.db.set_order(i for i in body.order if i in known)
    return _order_view(s)


class BoxesBody(BaseModel):
    boxes: dict[str, list[int]]


@router.put("/order/boxes")
async def put_boxes(body: BoxesBody, s: Services = Depends(svc)) -> dict:
    known = s.releases()
    cleaned = {b: [i for i in ids if i in known] for b, ids in body.boxes.items()}
    s.set_boxes(cleaned)
    return _order_view(s)


class PlaceBody(BaseModel):
    instance_id: int
    position: int | None = None
    box_id: str | None = None
    after: int | None = None


@router.get("/order/suggest/{instance_id}")
async def suggest(instance_id: int, s: Services = Depends(svc)) -> dict:
    try:
        pos = s.suggest_position(instance_id)
    except NotFound as exc:
        raise not_found(exc) from exc
    placement = s.placement()
    rng = placement.range_for_position(pos) or (placement.ranges[-1] if placement.ranges else None)
    if rng is not None and pos >= rng.end and placement.ranges:
        rng = placement.ranges[-1]
    before = placement.order[pos - 1] if 0 < pos <= len(placement.order) else None
    return {"position": pos, "box_id": rng.box.id if rng else None, "after_instance_id": before}


@router.post("/order/place")
async def place(body: PlaceBody, s: Services = Depends(svc)) -> dict:
    if s.db.get_release(body.instance_id) is None:
        raise HTTPException(404, f"no release {body.instance_id}")
    ov = s.db.get_overrides().get(body.instance_id)
    if ov and ov.excluded:
        s.db.set_override(
            Override(
                instance_id=body.instance_id,
                section=ov.section,
                sort_key=ov.sort_key,
                excluded=False,
            )
        )
    placement = s.placement()
    into_next = False
    if body.after is not None:
        pos = placement.position.get(body.after)
        if pos is None:
            raise HTTPException(400, f"release {body.after} is not on the shelf")
        position = pos + 1
    elif body.box_id is not None:
        rng = next((r for r in placement.ranges if r.box.id == body.box_id), None)
        if rng is None:
            raise HTTPException(404, f"no record box {body.box_id}")
        position = rng.end
    elif body.position is not None:
        position = body.position
        into_next = True
    else:
        position = s.suggest_position(body.instance_id)
        into_next = True
    s.insert_at(body.instance_id, position, box_id=body.box_id, into_next_box=into_next)
    return _order_view(s)


class RemoveBody(BaseModel):
    instance_id: int
    exclude: bool = False


@router.post("/order/remove")
async def remove(body: RemoveBody, s: Services = Depends(svc)) -> dict:
    s.remove_from_shelf(body.instance_id)
    if body.exclude:
        ov = s.db.get_overrides().get(body.instance_id) or Override(instance_id=body.instance_id)
        s.db.set_override(
            Override(
                instance_id=body.instance_id,
                section=ov.section,
                sort_key=ov.sort_key,
                excluded=True,
            )
        )
    return _order_view(s)


@router.get("/boundaries")
async def get_boundaries(s: Services = Depends(svc)) -> dict:
    return {"stored": s.db.get_boundaries(), "effective": s.placement().boundaries}


class BoundariesBody(BaseModel):
    boundaries: dict[str, int]


@router.put("/boundaries")
async def put_boundaries(body: BoundariesBody, s: Services = Depends(svc)) -> dict:
    valid = {b.id for b in s.layout.record_boxes}
    s.db.set_boundaries({k: v for k, v in body.boundaries.items() if k in valid})
    return {"stored": s.db.get_boundaries(), "effective": s.placement().boundaries}


class CalibrateBody(BaseModel):
    box_id: str
    instance_id: int


@router.post("/calibrate")
async def calibrate(body: CalibrateBody, s: Services = Depends(svc)) -> dict:
    try:
        s.calibrate(body.box_id, body.instance_id)
    except NotFound as exc:
        raise not_found(exc) from exc
    return {"stored": s.db.get_boundaries(), "effective": s.placement().boundaries}


@router.delete("/calibrate/{box_id}")
async def uncalibrate(box_id: str, s: Services = Depends(svc)) -> dict:
    s.db.clear_boundary(box_id)
    return {"stored": s.db.get_boundaries(), "effective": s.placement().boundaries}


@router.get("/scheme")
async def get_scheme(s: Services = Depends(svc)) -> dict:
    return s.scheme().model_dump()


@router.put("/scheme")
async def put_scheme(scheme: Scheme, s: Services = Depends(svc)) -> dict:
    s.set_scheme(scheme)
    return scheme.model_dump()


@router.post("/plan")
async def plan(s: Services = Depends(svc)) -> dict:
    p = s.plan()
    releases = s.releases()
    out = p.to_dict()
    for item in out["items"]:
        r = releases.get(item["instance_id"])
        if r is not None:
            item["artist"] = r.artist
            item["title"] = r.title
            item["year"] = r.year
    return out


@router.post("/plan/apply")
async def apply_plan(s: Services = Depends(svc)) -> dict:
    placement = s.apply_plan()
    return {"ok": True, "total": len(placement.order), "boundaries": placement.boundaries}


@router.get("/overrides")
async def get_overrides(s: Services = Depends(svc)) -> dict:
    return {str(k): v.model_dump() for k, v in s.db.get_overrides().items()}


class OverrideBody(BaseModel):
    section: str | None = None
    sort_key: str | None = None
    excluded: bool = False


@router.put("/overrides/{instance_id}")
async def put_override(instance_id: int, body: OverrideBody, s: Services = Depends(svc)) -> dict:
    if s.db.get_release(instance_id) is None:
        raise HTTPException(404, f"no release {instance_id}")
    ov = Override(instance_id=instance_id, **body.model_dump())
    if ov.excluded:
        s.remove_from_shelf(instance_id)
    s.db.set_override(ov)
    return ov.model_dump()


@router.delete("/overrides/{instance_id}")
async def delete_override(instance_id: int, s: Services = Depends(svc)) -> dict:
    s.db.clear_override(instance_id)
    return {"ok": True}
