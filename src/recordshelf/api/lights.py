from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from ..models import RGB
from ..search import best_match
from ..services import NotFound, Services
from ..shelf import Located
from .deps import not_found, svc

router = APIRouter(tags=["lights"])


def _located(s: Services, loc: Located) -> dict:
    r = s.db.get_release(loc.instance_id)
    return {
        "instance_id": loc.instance_id,
        "artist": r.artist if r else None,
        "title": r.title if r else None,
        "position": loc.position,
        "box_id": loc.box.id,
        "row": loc.box.row,
        "col": loc.box.col,
        "index_in_box": loc.index_in_box,
        "count_in_box": loc.count_in_box,
        "pixel": loc.pixel,
        "has_leds": loc.box.has_leds,
    }


@router.post("/locate/{instance_id}")
async def locate(
    instance_id: int, duration: float = Query(6.0, gt=0, le=120), s: Services = Depends(svc)
) -> dict:
    try:
        return _located(s, s.locate(instance_id, duration))
    except NotFound as exc:
        raise not_found(exc) from exc


def _locate_query(s: Services, q: str, duration: float) -> dict:
    if not q.strip():
        raise HTTPException(400, "q is required")
    r = best_match([x for x in s.db.list_releases()], q)
    if r is None:
        raise HTTPException(404, f"nothing matches {q!r}")
    try:
        return _located(s, s.locate(r.instance_id, duration))
    except NotFound as exc:
        raise HTTPException(
            404, f"{r.artist} - {r.title} matched but is not placed on the shelf"
        ) from exc


@router.post("/locate")
async def locate_by_query(
    q: str, duration: float = Query(6.0, gt=0, le=120), s: Services = Depends(svc)
) -> dict:
    return _locate_query(s, q, duration)


class Color(BaseModel):
    color: RGB = (255, 255, 255)


class BoxBody(Color):
    duration: float | None = Field(5.0, gt=0, le=3600)
    pulse: bool = False


@router.post("/lights/box/{box_id}")
async def light_box(box_id: str, body: BoxBody | None = None, s: Services = Depends(svc)) -> dict:
    body = body or BoxBody()
    try:
        s.light_box(box_id, color=body.color, duration=body.duration, pulse=body.pulse)
    except NotFound as exc:
        raise not_found(exc) from exc
    return {"ok": True, "box_id": box_id}


class PixelBody(BaseModel):
    controller: str
    index: int = Field(ge=0)
    duration: float = Field(5.0, gt=0, le=600)


@router.post("/lights/pixel")
async def light_pixel(body: PixelBody, s: Services = Depends(svc)) -> dict:
    try:
        px = s.light_pixel(body.controller, body.index, body.duration)
    except NotFound as exc:
        raise not_found(exc) from exc
    return {"ok": True, "pixel": px}


class WipeBody(Color):
    color: RGB = (0, 120, 255)
    duration: float = Field(4.0, gt=0, le=60)


@router.post("/lights/wipe")
async def wipe(body: WipeBody | None = None, s: Services = Depends(svc)) -> dict:
    body = body or WipeBody()
    s.wipe(color=body.color, duration=body.duration)
    return {"ok": True}


@router.post("/lights/identify")
async def identify(duration: float = Query(20.0, gt=0, le=600), s: Services = Depends(svc)) -> dict:
    return {"ok": True, "boxes": s.identify(duration)}


@router.post("/lights/off")
async def off(s: Services = Depends(svc)) -> dict:
    s.lights_off()
    return {"ok": True}


@router.get("/scenes")
async def scenes(s: Services = Depends(svc)) -> dict:
    """Every scene with a preview legend computed from the current collection and details."""
    return {"scenes": s.scenes(), "active": s.current_scene}


class SceneBody(BaseModel):
    duration: float | None = Field(None, gt=0, le=86400)


@router.post("/scenes/{name}")
async def play_scene(name: str, body: SceneBody | None = None, s: Services = Depends(svc)) -> dict:
    body = body or SceneBody()
    try:
        legend = s.play_scene(name, body.duration)
    except NotFound as exc:
        raise not_found(exc) from exc
    return {"ok": True, "name": name, "legend": legend}


# --- GET hooks for Homebridge / Siri Shortcuts / anything that can only do a plain URL ----


@router.get("/hooks/locate")
async def hook_locate(
    q: str, duration: float = Query(6.0, gt=0, le=120), s: Services = Depends(svc)
) -> dict:
    return _locate_query(s, q, duration)


@router.get("/hooks/scene/{name}")
async def hook_scene(
    name: str, duration: float | None = Query(None, gt=0, le=86400), s: Services = Depends(svc)
) -> dict:
    try:
        legend = s.play_scene(name, duration)
    except NotFound as exc:
        raise not_found(exc) from exc
    return {"ok": True, "name": name, "legend": legend}


@router.get("/hooks/box/{box_id}")
async def hook_box(
    box_id: str, duration: float | None = Query(None, gt=0, le=86400), s: Services = Depends(svc)
) -> dict:
    try:
        s.light_box(box_id, duration=duration)
    except NotFound as exc:
        raise not_found(exc) from exc
    return {"ok": True}


@router.get("/hooks/off")
async def hook_off(s: Services = Depends(svc)) -> dict:
    s.lights_off()
    return {"ok": True}


@router.get("/hooks/state")
async def hook_state(s: Services = Depends(svc)) -> dict:
    active = s.renderer.active
    return {"on": active is not None, "effect": active, "scene": s.current_scene}
