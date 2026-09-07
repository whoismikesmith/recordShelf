from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import ValidationError

from ..layout import EXAMPLE_YAML, ResolvedLayout
from ..models import LayoutConfig
from ..services import Services
from .deps import svc

router = APIRouter(tags=["layout"])


@router.get("/layout")
async def get_layout(s: Services = Depends(svc)) -> dict:
    return s.layout_cfg.model_dump(mode="json")


@router.put("/layout")
async def put_layout(cfg: LayoutConfig, s: Services = Depends(svc)) -> dict:
    try:
        ResolvedLayout(cfg)
    except (ValueError, KeyError) as exc:
        raise HTTPException(422, str(exc)) from exc
    await s.apply_layout(cfg)
    return s.layout_cfg.model_dump(mode="json")


@router.post("/layout/validate")
async def validate_layout(body: dict) -> dict:
    try:
        cfg = LayoutConfig.model_validate(body)
        ResolvedLayout(cfg)
    except ValidationError as exc:
        return {"ok": False, "errors": [e["msg"] for e in exc.errors()]}
    except (ValueError, KeyError) as exc:
        return {"ok": False, "errors": [str(exc)]}
    return {"ok": True, "errors": []}


@router.get("/layout/resolved")
async def resolved(s: Services = Depends(svc)) -> dict:
    return s.layout.to_dict()


@router.get("/layout/example", response_class=PlainTextResponse)
async def example() -> str:
    return EXAMPLE_YAML
