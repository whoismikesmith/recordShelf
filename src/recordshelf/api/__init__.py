from fastapi import APIRouter

from . import layout, lights, releases, shelf, system

router = APIRouter(prefix="/api")
router.include_router(system.router)
router.include_router(releases.router)
router.include_router(shelf.router)
router.include_router(lights.router)
router.include_router(layout.router)

__all__ = ["router"]
