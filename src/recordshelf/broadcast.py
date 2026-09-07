"""Fan-out of JSON messages to connected websocket clients."""

from __future__ import annotations

import json
from typing import Any

from fastapi import WebSocket


class Broadcaster:
    def __init__(self) -> None:
        self._clients: set[WebSocket] = set()

    @property
    def count(self) -> int:
        return len(self._clients)

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self._clients.add(ws)

    def disconnect(self, ws: WebSocket) -> None:
        self._clients.discard(ws)

    async def publish(self, message: dict[str, Any]) -> None:
        if not self._clients:
            return
        text = json.dumps(message)
        dead: list[WebSocket] = []
        for ws in list(self._clients):
            try:
                await ws.send_text(text)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)
