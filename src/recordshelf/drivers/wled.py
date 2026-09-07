"""WLED over DDP (Distributed Display Protocol, UDP port 4048).

Packet: 10-byte header + RGB bytes.
  byte 0  flags: 0x40 = protocol v1, |0x01 = push (render this frame now)
  byte 1  sequence (0 = unused)
  byte 2  data type: 0x0B = RGB, 8 bits per channel
  byte 3  destination id: 1 = default display
  4..7    byte offset into the pixel buffer (big-endian)
  8..9    payload length in bytes (big-endian)
WLED accepts at most 1440 data bytes (480 pixels) per packet. While packets keep arriving
WLED shows them; once they stop for its "realtime timeout" it resumes its own effect/preset.
"""

from __future__ import annotations

import asyncio
import socket
import struct
from collections.abc import Sequence

import httpx

from ..models import RGB, ControllerConfig
from .base import Driver

DDP_PORT = 4048
DDP_VERSION = 0x40
DDP_PUSH = 0x01
DDP_ID_DISPLAY = 1
MAX_PIXELS_PER_PACKET = 480


def ddp_packets(pixels: Sequence[RGB], data_type: int = 0x0B) -> list[bytes]:
    """Split a frame into DDP packets; only the last one carries the push flag."""
    packets: list[bytes] = []
    n = len(pixels)
    for start in range(0, n, MAX_PIXELS_PER_PACKET):
        chunk = pixels[start : start + MAX_PIXELS_PER_PACKET]
        payload = bytes(c for px in chunk for c in (px[0] & 0xFF, px[1] & 0xFF, px[2] & 0xFF))
        last = start + len(chunk) >= n
        flags = DDP_VERSION | (DDP_PUSH if last else 0)
        header = struct.pack(
            ">BBBBIH", flags, 0, data_type, DDP_ID_DISPLAY, start * 3, len(payload)
        )
        packets.append(header + payload)
    if not packets:
        packets.append(
            struct.pack(">BBBBIH", DDP_VERSION | DDP_PUSH, 0, data_type, DDP_ID_DISPLAY, 0, 0)
        )
    return packets


class WledDriver(Driver):
    def __init__(self, cfg: ControllerConfig):
        super().__init__(cfg)
        self._sock: socket.socket | None = None
        self._addr: tuple[str, int] | None = None

    @property
    def base_url(self) -> str:
        host = self.cfg.host
        return host if host.startswith("http") else f"http://{host}"

    async def start(self) -> None:
        try:
            port = self.cfg.port or DDP_PORT
            ip = await asyncio.get_running_loop().run_in_executor(
                None, socket.gethostbyname, self.cfg.host
            )
            self._addr = (ip, port)
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self._sock.setblocking(False)
            self.connected = True
            self.last_error = None
        except OSError as exc:
            self.connected = False
            self.last_error = f"cannot resolve {self.cfg.host!r}: {exc}"

    async def send(self, pixels: Sequence[RGB]) -> None:
        if self._sock is None or self._addr is None:
            await self.start()
            if self._sock is None or self._addr is None:
                return
        try:
            for pkt in ddp_packets(self.scale(pixels), self.cfg.ddp_type):
                self._sock.sendto(pkt, self._addr)
            self.frames_sent += 1
            self.connected = True
        except OSError as exc:
            self.connected = False
            self.last_error = str(exc)

    async def release(self) -> None:
        # Ending realtime mode explicitly is faster than waiting for WLED's timeout.
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                await client.post(f"{self.base_url}/json/state", json={"live": False})
        except (httpx.HTTPError, OSError):
            pass  # WLED's own realtime timeout will restore its state

    async def stop(self) -> None:
        if self._sock is not None:
            self._sock.close()
            self._sock = None
        self.connected = False

    async def probe(self) -> dict:
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                resp = await client.get(f"{self.base_url}/json/info")
                resp.raise_for_status()
                info = resp.json()
            leds = info.get("leds", {})
            return {
                "ok": True,
                "name": info.get("name"),
                "version": info.get("ver"),
                "led_count": leds.get("count"),
                "configured_led_count": self.cfg.led_count,
                "ip": info.get("ip"),
                "live": info.get("live"),
                "udp_port": info.get("udpport"),
            }
        except (httpx.HTTPError, OSError, ValueError) as exc:
            return {"ok": False, "error": str(exc)}
