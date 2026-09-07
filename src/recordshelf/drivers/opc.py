"""Open Pixel Control over TCP, for the original Fadecandy setup.

Message: channel (1 byte), command 0 = set pixels (1 byte), length (2 bytes BE), RGB bytes.
"""

from __future__ import annotations

import asyncio
import struct
from collections.abc import Sequence

from ..models import RGB, ControllerConfig
from .base import Driver

OPC_PORT = 7890


def opc_message(pixels: Sequence[RGB], channel: int = 0) -> bytes:
    payload = bytes(c for px in pixels for c in (px[0] & 0xFF, px[1] & 0xFF, px[2] & 0xFF))
    return struct.pack(">BBH", channel, 0, len(payload)) + payload


class OpcDriver(Driver):
    def __init__(self, cfg: ControllerConfig):
        super().__init__(cfg)
        self._writer: asyncio.StreamWriter | None = None

    async def start(self) -> None:
        await self._connect()

    async def _connect(self) -> None:
        try:
            _, writer = await asyncio.wait_for(
                asyncio.open_connection(self.cfg.host, self.cfg.port or OPC_PORT), timeout=2.0
            )
            self._writer = writer
            self.connected = True
            self.last_error = None
        except (TimeoutError, OSError) as exc:
            self._writer = None
            self.connected = False
            self.last_error = str(exc)

    async def send(self, pixels: Sequence[RGB]) -> None:
        if self._writer is None:
            await self._connect()
            if self._writer is None:
                return
        try:
            self._writer.write(opc_message(self.scale(pixels)))
            await self._writer.drain()
            self.frames_sent += 1
        except (OSError, ConnectionError) as exc:
            self.connected = False
            self.last_error = str(exc)
            self._writer = None

    async def release(self) -> None:
        await self.send([(0, 0, 0)] * self.cfg.led_count)

    async def stop(self) -> None:
        if self._writer is not None:
            self._writer.close()
            self._writer = None
        self.connected = False
