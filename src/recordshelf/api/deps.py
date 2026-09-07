from __future__ import annotations

from fastapi import HTTPException, Request

from ..services import NotFound, Services


def svc(request: Request) -> Services:
    return request.app.state.services


def not_found(exc: NotFound) -> HTTPException:
    return HTTPException(status_code=404, detail=str(exc))
