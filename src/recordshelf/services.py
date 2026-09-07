"""Wires the pieces together and holds the operations the API exposes."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from .broadcast import Broadcaster
from .db import Database
from .discogs import DiscogsClient, SyncManager, SyncStatus
from .drivers import Driver, make_driver
from .layout import ResolvedLayout, load_layout, save_layout
from .models import LayoutConfig, Override, Placed, Release, ReleaseOut, Scheme
from .ordering import build_plan, ordered_releases, section_for, section_rank, sort_key
from .render.effects import Fill, Locate, Static, Wipe
from .render.renderer import Renderer
from .render.scenes import SCENES, SceneContext
from .settings import Settings
from .shelf import Located, Placement

log = logging.getLogger(__name__)


class NotFound(Exception):
    pass


class Services:
    def __init__(self, settings: Settings, db: Database | None = None):
        self.settings = settings
        self.db = db or Database(settings.db_path)
        self.broadcaster = Broadcaster()
        self.layout_cfg: LayoutConfig = load_layout(settings.layout_file)
        self.layout = ResolvedLayout(self.layout_cfg)
        self.drivers: dict[str, Driver] = {
            c.id: make_driver(c) for c in self.layout_cfg.controllers
        }
        self.renderer = Renderer(self.layout, self.drivers, self.broadcaster, fps=settings.fps)
        self.renderer.on_change(lambda active: self._publish({"type": "effect", "active": active}))
        self.sync = SyncManager(self.db, self._client_factory, on_change=self._sync_changed)
        self._loop: asyncio.AbstractEventLoop | None = None
        self.current_scene: dict[str, Any] | None = None

    # -- lifecycle ---------------------------------------------------------

    async def start(self) -> None:
        self._loop = asyncio.get_running_loop()
        await self.renderer.start()

    async def stop(self) -> None:
        await self.renderer.stop()
        self.db.close()

    def _client_factory(self) -> DiscogsClient:
        s = self.settings
        return DiscogsClient(s.discogs_username, s.discogs_token, s.user_agent)

    def _sync_changed(self, status: SyncStatus) -> None:
        self._publish({"type": "sync", **status.model_dump()})

    def _publish(self, message: dict[str, Any]) -> None:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = self._loop
            if loop is None:
                return
            loop.call_soon_threadsafe(lambda: loop.create_task(self.broadcaster.publish(message)))
            return
        loop.create_task(self.broadcaster.publish(message))

    # -- collection --------------------------------------------------------

    def releases(self) -> dict[int, Release]:
        return {r.instance_id: r for r in self.db.list_releases()}

    def scheme(self) -> Scheme:
        data = self.db.get_json("scheme")
        return Scheme.model_validate(data) if data else Scheme()

    def set_scheme(self, scheme: Scheme) -> None:
        self.db.set_json("scheme", scheme.model_dump(mode="json"))

    def placement(self) -> Placement:
        return Placement(self.db.get_order(), self.db.get_boundaries(), self.layout)

    def release_out(
        self,
        r: Release,
        placement: Placement,
        scheme: Scheme,
        overrides: dict[int, Override],
    ) -> ReleaseOut:
        ov = overrides.get(r.instance_id)
        loc = placement.locate(r.instance_id)
        placed = None
        if loc is not None:
            placed = Placed(
                position=loc.position,
                box_id=loc.box.id,
                index_in_box=loc.index_in_box,
                count_in_box=loc.count_in_box,
                pixel=loc.pixel,
            )
        return ReleaseOut(
            **r.model_dump(),
            section=section_for(r, scheme, ov),
            on_shelf=loc is not None,
            excluded=bool(ov and ov.excluded),
            placed=placed,
        )

    def all_out(self) -> list[ReleaseOut]:
        placement = self.placement()
        scheme = self.scheme()
        overrides = self.db.get_overrides()
        return [self.release_out(r, placement, scheme, overrides) for r in self.db.list_releases()]

    def status(self) -> dict[str, Any]:
        order = self.db.get_order()
        total = self.db.query("SELECT COUNT(*) AS n FROM releases")[0]["n"]
        overrides = self.db.get_overrides()
        excluded = sum(1 for o in overrides.values() if o.excluded)
        return {
            "name": self.layout_cfg.name,
            "username": self.settings.discogs_username,
            "has_token": bool(self.settings.discogs_token),
            "last_sync": self.db.get_meta("last_sync"),
            "release_count": total,
            "on_shelf": len(order),
            "inbox": len(self.inbox()),
            "skipped": len(self.skipped()),
            "excluded": excluded,
            "effect": self.renderer.active,
            "scene": self.current_scene,
            "controllers": [d.info() for d in self.drivers.values()],
            "sync": self.sync.status.model_dump(),
            "websocket_clients": self.broadcaster.count,
        }

    # -- ordering ----------------------------------------------------------

    def suggest_position(self, instance_id: int) -> int:
        """Where the scheme would put this record among the current shelf order."""
        r = self.db.get_release(instance_id)
        if r is None:
            raise NotFound(f"no release {instance_id}")
        scheme = self.scheme()
        overrides = self.db.get_overrides()
        releases = self.releases()
        key = (
            section_rank(section_for(r, scheme, overrides.get(instance_id)), scheme),
            sort_key(r, scheme, overrides.get(instance_id)),
        )
        order = [i for i in self.db.get_order() if i != instance_id]
        for pos, iid in enumerate(order):
            other = releases.get(iid)
            if other is None:
                continue
            ok = (
                section_rank(section_for(other, scheme, overrides.get(iid)), scheme),
                sort_key(other, scheme, overrides.get(iid)),
            )
            if ok > key:
                return pos
        return len(order)

    def insert_at(
        self,
        instance_id: int,
        position: int,
        box_id: str | None = None,
        into_next_box: bool = False,
    ) -> Placement:
        """Insert a record at `position` and shift stored box boundaries to match.

        Several empty boxes can share the same boundary, so which box receives the record is a
        matter of box index, not position: `box_id` names it explicitly, `into_next_box` makes
        the record the first one in the box that starts at `position`, otherwise it joins the
        box of the record just before it.
        """
        placement = self.placement()
        calibrated = self.db.calibrated_boxes()
        old_pos = placement.position.get(instance_id)
        # Materialise the effective boundaries so this placement sticks instead of being
        # re-estimated from capacities on the next read.
        stored = placement.boundaries
        order = [i for i in placement.order if i != instance_id]
        if old_pos is not None:
            stored = {b: (p - 1 if p > old_pos else p) for b, p in stored.items()}
            placement = Placement(order, stored, self.layout)
        position = max(0, min(position, len(order)))
        boxes = self.layout.record_boxes
        index_of = {b.id: i for i, b in enumerate(boxes)}
        if box_id is not None:
            target = index_of.get(box_id, len(boxes))
        elif into_next_box:
            starts_here = [i for i, r in enumerate(placement.ranges) if r.start == position]
            if starts_here:
                target = starts_here[0]
            else:
                rng = placement.range_for_position(position)
                target = index_of[rng.box.id] if rng else max(0, len(boxes) - 1)
        else:
            rng = placement.range_for_position(position - 1) if position > 0 else None
            target = index_of[rng.box.id] if rng else 0
        order.insert(position, instance_id)
        shifted = {}
        for b, p in stored.items():
            after_target = index_of.get(b, 0) > target
            shifted[b] = p + 1 if (p > position or (p == position and after_target)) else p
        self.db.set_order(order)
        self.db.set_boundaries(shifted, calibrated)
        return self.placement()

    def remove_from_shelf(self, instance_id: int) -> None:
        placement = self.placement()
        pos = placement.position.get(instance_id)
        if pos is None:
            return
        boundaries = {b: (p - 1 if p > pos else p) for b, p in placement.boundaries.items()}
        self.db.remove_from_order(instance_id)
        self.db.set_boundaries(boundaries, self.db.calibrated_boxes())

    def set_boxes(self, boxes: dict[str, list[int]]) -> Placement:
        """Set the whole shelf from explicit per-box contents (drag and drop result)."""
        order: list[int] = []
        boundaries: dict[str, int] = {}
        for box in self.layout.record_boxes:
            boundaries[box.id] = len(order)
            for iid in boxes.get(box.id, []):
                if iid not in order:
                    order.append(iid)
        self.db.set_order(order)
        self.db.set_boundaries(boundaries, self.db.calibrated_boxes())
        return self.placement()

    def plan(self):
        placement = self.placement()
        current = {iid: b.id for iid in placement.order if (b := placement.box_of(iid))}
        return build_plan(
            list(self.releases().values()),
            self.scheme(),
            self.db.get_overrides(),
            self.layout.record_boxes,
            current,
        )

    def apply_plan(self) -> Placement:
        """Make the plan the shelf order. Stored boundaries are cleared: the plan's box split
        is the capacity-proportional estimate, which is exactly what an uncalibrated placement
        computes, so nothing is lost and boxes correctly show as 'estimated' until calibrated."""
        plan = self.plan()
        self.db.set_order(plan.order)
        self.db.set_boundaries({})
        return self.placement()

    def calibrate(self, box_id: str, instance_id: int) -> Placement:
        if box_id not in self.layout.by_id or self.layout.by_id[box_id].kind != "records":
            raise NotFound(f"no record box {box_id}")
        pos = self.placement().position.get(instance_id)
        if pos is None:
            raise NotFound(f"release {instance_id} is not on the shelf")
        self.db.set_boundary(box_id, pos)
        return self.placement()

    def _unplaced(self) -> tuple[list[Release], list[Release]]:
        """Records not on the shelf and not excluded: (eligible by scheme, skipped by scheme)."""
        on_shelf = set(self.db.get_order())
        overrides = self.db.get_overrides()
        scheme = self.scheme()
        candidates = []
        for r in self.db.list_releases():
            ov = overrides.get(r.instance_id)
            if r.instance_id in on_shelf or (ov and ov.excluded):
                continue
            candidates.append(r)
        ranked = [r for r, _ in ordered_releases(candidates, scheme, overrides)[0]]
        eligible_ids = {r.instance_id for r in ranked}
        skipped = sorted(
            (r for r in candidates if r.instance_id not in eligible_ids),
            key=lambda r: (r.artist_sort, r.title.casefold()),
        )
        return ranked, skipped

    def inbox(self) -> list[Release]:
        """New arrivals: on the scheme's shelf list, but not placed yet."""
        return self._unplaced()[0]

    def skipped(self) -> list[Release]:
        """Not placed and not wanted by the scheme (wrong format, folder...)."""
        return self._unplaced()[1]

    # -- lights ------------------------------------------------------------

    def locate(self, instance_id: int, duration: float = 6.0) -> Located:
        loc = self.placement().locate(instance_id)
        if loc is None:
            raise NotFound(f"release {instance_id} is not placed on the shelf")
        self.current_scene = None
        pixels = [loc.pixel] if loc.pixel is not None else []
        self.renderer.play(
            Locate(pixels, bounds=loc.box.pixels, duration=duration),
            name="locate",
            instance_id=instance_id,
            box_id=loc.box.id,
            pixel=loc.pixel,
        )
        return loc

    def light_box(
        self, box_id: str, color=(255, 255, 255), duration: float | None = 5.0, pulse=False
    ) -> None:
        box = self.layout.by_id.get(box_id)
        if box is None:
            raise NotFound(f"no box {box_id}")
        self.current_scene = None
        self.renderer.play(
            Fill([box.pixels], color=color, duration=duration, pulse=pulse),
            name="box",
            box_id=box_id,
        )

    def light_pixel(self, controller: str, index: int, duration: float = 5.0) -> int:
        if controller not in self.layout.controller_offsets:
            raise NotFound(f"no controller {controller}")
        px = self.layout.global_pixel(controller, index)
        self.current_scene = None
        self.renderer.play(
            Fill([range(px, px + 1)], color=(255, 255, 255), duration=duration),
            name="pixel",
            pixel=px,
        )
        return px

    def identify(self, duration: float = 20.0) -> list[dict]:
        """Light the first LED of every box in a distinct color so wiring can be checked."""
        from .render.scenes import PALETTE

        colors: dict[int, tuple[int, int, int]] = {}
        legend = []
        for i, box in enumerate(self.layout.boxes):
            if not box.has_leds:
                continue
            c = PALETTE[i % len(PALETTE)]
            # leftmost LED in reading order; in a reversed box that is the highest index
            first = box.global_start + (box.led_count - 1 if box.reversed else 0)
            colors[first] = c
            legend.append({"box_id": box.id, "color": c, "pixel": first})
        self.current_scene = None
        self.renderer.play(Static(colors, duration=duration), name="identify")
        return legend

    def wipe(self, color=(0, 120, 255), duration: float = 4.0) -> None:
        self.current_scene = None
        self.renderer.play(Wipe(color=color, duration=duration), name="wipe")

    def lights_off(self) -> None:
        self.current_scene = None
        self.renderer.stop_effect()

    def play_scene(self, name: str, duration: float | None = None) -> list[dict]:
        if name not in SCENES:
            raise NotFound(f"no scene {name}")
        title, _, fn = SCENES[name]
        ctx = SceneContext(
            self.releases(), self.placement(), self.scheme(), self.db.get_overrides()
        )
        result = fn(ctx)
        self.renderer.play(Static(result.colors, duration=duration), name="scene", scene=name)
        self.current_scene = {"name": name, "title": title, "legend": result.legend}
        return result.legend

    # -- layout ------------------------------------------------------------

    async def apply_layout(self, cfg: LayoutConfig) -> None:
        save_layout(self.settings.layout_file, cfg)
        self.layout_cfg = cfg
        self.layout = ResolvedLayout(cfg)
        self.drivers = {c.id: make_driver(c) for c in cfg.controllers}
        await self.renderer.reconfigure(self.layout, self.drivers)
        self._publish({"type": "layout", "layout": self.layout.to_dict()})
