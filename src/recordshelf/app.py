from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from . import __version__
from .api import router
from .api.system import websocket_endpoint
from .db import Database
from .services import Services
from .settings import Settings

log = logging.getLogger(__name__)


def create_app(settings: Settings | None = None, db: Database | None = None) -> FastAPI:
    settings = settings or Settings()
    services = Services(settings, db)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        await services.start()
        try:
            yield
        finally:
            await services.stop()

    app = FastAPI(title="recordShelf", version=__version__, lifespan=lifespan)
    app.state.services = services
    app.include_router(router)
    app.add_api_websocket_route("/ws", websocket_endpoint)

    dist: Path = settings.web_dist
    if dist.is_dir() and (dist / "index.html").is_file():
        log.info("serving web UI from %s", dist)
        if (dist / "assets").is_dir():
            app.mount("/assets", StaticFiles(directory=dist / "assets"), name="assets")

        @app.get("/{path:path}", include_in_schema=False)
        async def spa(path: str) -> FileResponse:
            candidate = dist / path
            if path and candidate.is_file():
                return FileResponse(candidate)
            return FileResponse(dist / "index.html")

    else:
        log.warning(
            "web UI not found at %s (run `npm run build` in web/, or set RECORDSHELF_WEB_DIST)",
            dist,
        )

        @app.get("/", include_in_schema=False)
        async def no_ui() -> dict:
            return {
                "app": "recordShelf",
                "version": __version__,
                "hint": "Web UI not built. Run `npm run build` in web/, or use /docs for the API.",
                "looked_in": str(dist),
            }

    return app
