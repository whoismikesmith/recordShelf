from __future__ import annotations

from collections.abc import Sequence

from ..models import RGB, ControllerConfig


class Driver:
    """Sends full frames to one controller. Subclasses implement send/release."""

    def __init__(self, cfg: ControllerConfig):
        self.cfg = cfg
        self.connected = False
        self.last_error: str | None = None
        self.frames_sent = 0

    @property
    def id(self) -> str:
        return self.cfg.id

    def scale(self, pixels: Sequence[RGB]) -> list[RGB]:
        b = self.cfg.brightness
        if b >= 1.0:
            return list(pixels)
        return [(int(r * b), int(g * b), int(bl * b)) for r, g, bl in pixels]

    async def start(self) -> None:
        self.connected = True

    async def send(self, pixels: Sequence[RGB]) -> None:
        raise NotImplementedError

    async def release(self) -> None:
        """Called when an effect ends: let the controller go back to its own state."""

    async def stop(self) -> None:
        self.connected = False

    async def probe(self) -> dict:
        return {"ok": True, "type": self.cfg.type}

    def info(self) -> dict:
        return {
            "id": self.cfg.id,
            "type": self.cfg.type,
            "host": self.cfg.host,
            "led_count": self.cfg.led_count,
            "connected": self.connected,
            "error": self.last_error,
            "frames_sent": self.frames_sent,
        }


class NullDriver(Driver):
    """No hardware. The virtual shelf in the browser still shows the frames."""

    async def send(self, pixels: Sequence[RGB]) -> None:
        self.frames_sent += 1
