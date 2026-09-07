from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect

from ..services import Services
from .deps import svc

router = APIRouter(tags=["system"])


@router.get("/status")
async def status(s: Services = Depends(svc)) -> dict:
    return s.status()


@router.get("/sync")
async def sync_status(s: Services = Depends(svc)) -> dict:
    return s.sync.status.model_dump()


@router.post("/sync", status_code=202)
async def start_sync(s: Services = Depends(svc)) -> dict:
    if not s.settings.discogs_username:
        raise HTTPException(400, "Set DISCOGS_USERNAME (and ideally DISCOGS_TOKEN) in .env first")
    if not s.sync.start():
        raise HTTPException(409, "A sync is already running")
    return s.sync.status.model_dump()


@router.post("/controllers/{controller_id}/probe")
async def probe(controller_id: str, s: Services = Depends(svc)) -> dict:
    d = s.drivers.get(controller_id)
    if d is None:
        raise HTTPException(404, f"no controller {controller_id}")
    return await d.probe()


async def websocket_endpoint(ws: WebSocket) -> None:
    s: Services = ws.app.state.services
    await s.broadcaster.connect(ws)
    try:
        await ws.send_json(
            {
                "type": "hello",
                "layout": s.layout.to_dict(),
                "effect": s.renderer.active,
                "scene": s.current_scene,
                "sync": s.sync.status.model_dump(),
            }
        )
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        s.broadcaster.disconnect(ws)
