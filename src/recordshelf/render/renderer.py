"""One asyncio task owns the frame, runs the active effect, and pushes to drivers."""

from __future__ import annotations

import asyncio
import contextlib
import logging
import time
from collections.abc import Callable
from typing import Any

from ..broadcast import Broadcaster
from ..drivers import Driver
from ..layout import ResolvedLayout
from ..models import RGB
from .effects import BLACK, Effect, Frame, clear

log = logging.getLogger(__name__)


class Renderer:
    def __init__(
        self,
        layout: ResolvedLayout,
        drivers: dict[str, Driver],
        broadcaster: Broadcaster | None = None,
        fps: int = 30,
        broadcast_fps: int = 20,
    ):
        self.layout = layout
        self.drivers = drivers
        self.broadcaster = broadcaster
        self.fps = fps
        self.broadcast_fps = broadcast_fps
        self.frame: Frame = [BLACK] * layout.total_pixels
        self._effect: Effect | None = None
        self._meta: dict[str, Any] | None = None
        self._started = 0.0
        self._wake = asyncio.Event()
        self._task: asyncio.Task | None = None
        self._last_broadcast = 0.0
        self._on_change: list[Callable[[dict | None], Any]] = []

    # -- lifecycle ---------------------------------------------------------

    async def start(self) -> None:
        for d in self.drivers.values():
            await d.start()
        self._task = asyncio.create_task(self._run(), name="renderer")

    async def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
            self._task = None
        for d in self.drivers.values():
            await d.stop()

    async def reconfigure(self, layout: ResolvedLayout, drivers: dict[str, Driver]) -> None:
        await self.stop()
        self.layout = layout
        self.drivers = drivers
        self.frame = [BLACK] * layout.total_pixels
        self._effect = None
        self._meta = None
        await self.start()

    # -- control -----------------------------------------------------------

    @property
    def active(self) -> dict[str, Any] | None:
        if self._effect is None or self._meta is None:
            return None
        return {**self._meta, "elapsed": round(time.monotonic() - self._started, 2)}

    def play(self, effect: Effect, **meta: Any) -> None:
        self._effect = effect
        self._meta = {"name": meta.pop("name", type(effect).__name__.lower()), **meta}
        self._started = time.monotonic()
        self._wake.set()
        self._changed()

    def stop_effect(self) -> None:
        if self._effect is not None:
            self._effect = None
            self._meta = None
            self._wake.set()
            self._changed()

    def on_change(self, fn: Callable[[dict | None], Any]) -> None:
        self._on_change.append(fn)

    def _changed(self) -> None:
        for fn in self._on_change:
            try:
                fn(self.active)
            except Exception:  # pragma: no cover
                log.exception("renderer listener failed")

    # -- loop --------------------------------------------------------------

    async def _run(self) -> None:
        interval = 1.0 / self.fps
        try:
            while True:
                effect = self._effect
                if effect is None:
                    self._wake.clear()
                    await self._wake.wait()
                    continue
                t0 = time.monotonic()
                keep = effect.render(self.frame, t0 - self._started)
                await self._push()
                if not keep and self._effect is effect or self._effect is None:
                    await self._finish()
                elapsed = time.monotonic() - t0
                await asyncio.sleep(max(0.0, interval - elapsed))
        except asyncio.CancelledError:
            clear(self.frame)
            await self._push(force_broadcast=True)
            raise

    async def _finish(self) -> None:
        self._effect = None
        self._meta = None
        clear(self.frame)
        await self._push(force_broadcast=True)
        await asyncio.gather(*(d.release() for d in self.drivers.values()), return_exceptions=True)
        self._changed()

    async def _push(self, force_broadcast: bool = False) -> None:
        sends = []
        for cid, driver in self.drivers.items():
            offset, count = self.layout.controller_slice(cid)
            sends.append(driver.send(self.frame[offset : offset + count]))
        if sends:
            await asyncio.gather(*sends, return_exceptions=True)
        if self.broadcaster is not None:
            now = time.monotonic()
            if force_broadcast or now - self._last_broadcast >= 1.0 / self.broadcast_fps:
                self._last_broadcast = now
                await self.broadcaster.publish({"type": "frame", "hex": frame_hex(self.frame)})


def frame_hex(frame: list[RGB]) -> str:
    return bytes(c & 0xFF for px in frame for c in px).hex()
