"""Effects render into a shared frame each tick. Return False when finished."""

from __future__ import annotations

import math
from typing import Protocol

from ..models import RGB

BLACK: RGB = (0, 0, 0)
Frame = list[RGB]


class Effect(Protocol):
    def render(self, frame: Frame, t: float) -> bool: ...


def clear(frame: Frame) -> None:
    for i in range(len(frame)):
        frame[i] = BLACK


def _brighter(a: RGB, b: RGB) -> RGB:
    return (max(a[0], b[0]), max(a[1], b[1]), max(a[2], b[2]))


def _scale(c: RGB, k: float) -> RGB:
    k = max(0.0, min(1.0, k))
    return (int(c[0] * k), int(c[1] * k), int(c[2] * k))


class Locate:
    """Blink the target pixel and sweep a white halo inward towards it, inside its box."""

    def __init__(
        self,
        pixels: list[int],
        bounds: range | None = None,
        duration: float = 6.0,
        color: RGB = (255, 30, 0),
        halo: int = 6,
        sweep_period: float = 0.7,
        blink_hz: float = 4.0,
    ):
        self.pixels = pixels
        self.bounds = bounds
        self.duration = duration
        self.color = color
        self.halo = halo
        self.sweep_period = sweep_period
        self.blink_hz = blink_hz

    def _in_bounds(self, frame: Frame, p: int) -> bool:
        if p < 0 or p >= len(frame):
            return False
        return self.bounds is None or p in self.bounds

    def render(self, frame: Frame, t: float) -> bool:
        clear(frame)
        phase = (t % self.sweep_period) / self.sweep_period
        radius = (1.0 - phase) * (self.halo + 1)
        for p in self.pixels:
            for d in range(1, self.halo + 1):
                k = max(0.0, 1.0 - abs(d - radius) / 1.5)
                if k <= 0:
                    continue
                glow = _scale((255, 255, 255), k * 0.6)
                for q in (p - d, p + d):
                    if self._in_bounds(frame, q):
                        frame[q] = _brighter(frame[q], glow)
            if self._in_bounds(frame, p):
                on = int(t * self.blink_hz * 2) % 2 == 0
                frame[p] = self.color if on else _scale(self.color, 0.15)
        return t < self.duration


class Fill:
    """Light a set of pixel ranges in one color, optionally pulsing."""

    def __init__(
        self,
        ranges: list[range],
        color: RGB = (255, 255, 255),
        duration: float | None = 5.0,
        pulse: bool = False,
    ):
        self.ranges = ranges
        self.color = color
        self.duration = duration
        self.pulse = pulse

    def render(self, frame: Frame, t: float) -> bool:
        clear(frame)
        k = 0.55 + 0.45 * math.sin(t * 2 * math.pi) if self.pulse else 1.0
        c = _scale(self.color, k)
        for r in self.ranges:
            for p in r:
                if 0 <= p < len(frame):
                    frame[p] = c
        return self.duration is None or t < self.duration


class Static:
    """Hold an arbitrary per-pixel picture (scenes). duration=None holds until stopped."""

    def __init__(self, colors: dict[int, RGB], duration: float | None = None):
        self.colors = colors
        self.duration = duration

    def render(self, frame: Frame, t: float) -> bool:
        clear(frame)
        for p, c in self.colors.items():
            if 0 <= p < len(frame):
                frame[p] = c
        return self.duration is None or t < self.duration


class Wipe:
    """Test pattern: sweep a color across every pixel, then fade out."""

    def __init__(self, color: RGB = (0, 120, 255), duration: float = 4.0):
        self.color = color
        self.duration = duration

    def render(self, frame: Frame, t: float) -> bool:
        n = len(frame)
        head = (t / (self.duration * 0.7)) * n
        for i in range(n):
            dist = head - i
            if dist < 0:
                frame[i] = BLACK
            else:
                frame[i] = _scale(self.color, max(0.0, 1.0 - dist / (n * 0.35)))
        return t < self.duration
