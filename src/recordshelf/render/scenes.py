"""Scenes paint the whole shelf by a record attribute. Each returns pixel colors and a legend."""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass, field

from ..models import RGB, Override, Release, Scheme
from ..ordering import section_for
from ..shelf import Placement

PALETTE: list[RGB] = [
    (255, 60, 40),
    (255, 150, 0),
    (250, 220, 0),
    (120, 220, 40),
    (0, 200, 120),
    (0, 190, 230),
    (40, 100, 255),
    (150, 70, 255),
    (255, 60, 200),
    (255, 120, 120),
    (180, 220, 255),
    (200, 160, 90),
]
OTHER: RGB = (70, 70, 70)


@dataclass
class SceneResult:
    colors: dict[int, RGB]
    legend: list[dict] = field(default_factory=list)


@dataclass
class SceneContext:
    releases: dict[int, Release]
    placement: Placement
    scheme: Scheme
    overrides: dict[int, Override]


SceneFn = Callable[[SceneContext], SceneResult]


def _paint(
    ctx: SceneContext, key: Callable[[Release], str], colors: dict[str, RGB]
) -> dict[int, RGB]:
    out: dict[int, RGB] = {}
    for px, iid in ctx.placement.pixel_map().items():
        r = ctx.releases.get(iid)
        if r is None:
            continue
        out[px] = colors.get(key(r), OTHER)
    return out


def _categorical(
    ctx: SceneContext, key: Callable[[Release], str], ordered: list[str] | None = None
) -> SceneResult:
    on_shelf = [ctx.releases[i] for i in ctx.placement.order if i in ctx.releases]
    counts = Counter(key(r) for r in on_shelf)
    if ordered is None:
        ordered = [k for k, _ in counts.most_common()]
    top = ordered[: len(PALETTE)]
    colors = {k: PALETTE[i] for i, k in enumerate(top)}
    legend = [{"label": k, "color": colors[k], "count": counts.get(k, 0)} for k in top]
    rest = sum(c for k, c in counts.items() if k not in colors)
    if rest:
        legend.append({"label": "Other", "color": OTHER, "count": rest})
    return SceneResult(colors=_paint(ctx, key, colors), legend=legend)


def _gradient(a: RGB, b: RGB, k: float) -> RGB:
    k = max(0.0, min(1.0, k))
    return tuple(int(a[i] + (b[i] - a[i]) * k) for i in range(3))  # type: ignore[return-value]


def scene_decade(ctx: SceneContext) -> SceneResult:
    on_shelf = [ctx.releases[i] for i in ctx.placement.order if i in ctx.releases]
    years = [r.year for r in on_shelf if r.year]
    if not years:
        return SceneResult(colors={}, legend=[])
    lo, hi = (min(years) // 10) * 10, (max(years) // 10) * 10
    decades = list(range(lo, hi + 1, 10))
    colors: dict[str, RGB] = {}
    for i, d in enumerate(decades):
        k = i / max(1, len(decades) - 1)
        colors[f"{d}s"] = _gradient((60, 40, 255), (255, 200, 0), k)
    colors["Unknown"] = OTHER
    counts = Counter(r.decade for r in on_shelf)
    legend = [
        {"label": d, "color": colors[d], "count": counts.get(d, 0)} for d in colors if counts.get(d)
    ]
    return SceneResult(colors=_paint(ctx, lambda r: r.decade, colors), legend=legend)


def scene_genre(ctx: SceneContext) -> SceneResult:
    return _categorical(ctx, lambda r: r.genres[0] if r.genres else "Unknown")


def scene_style(ctx: SceneContext) -> SceneResult:
    return _categorical(ctx, lambda r: r.styles[0] if r.styles else "Unknown")


def scene_section(ctx: SceneContext) -> SceneResult:
    def key(r: Release) -> str:
        return section_for(r, ctx.scheme, ctx.overrides.get(r.instance_id)) or "All"

    order = list(ctx.scheme.section_order) if ctx.scheme.section_order else None
    if order:
        seen = {key(ctx.releases[i]) for i in ctx.placement.order if i in ctx.releases}
        order = [s for s in order if s in seen] + sorted(seen - set(order))
    return _categorical(ctx, key, order)


def scene_label(ctx: SceneContext) -> SceneResult:
    return _categorical(ctx, lambda r: r.label or "Unknown")


def scene_rating(ctx: SceneContext) -> SceneResult:
    colors = {str(n): _gradient((40, 40, 60), (255, 215, 0), n / 5) for n in range(6)}
    colors["0"] = OTHER
    counts = Counter(str(ctx.releases[i].rating) for i in ctx.placement.order if i in ctx.releases)
    legend = [
        {
            "label": f"{n} star" + ("s" if n != 1 else ""),
            "color": colors[str(n)],
            "count": counts.get(str(n), 0),
        }
        for n in range(5, -1, -1)
        if counts.get(str(n))
    ]
    return SceneResult(colors=_paint(ctx, lambda r: str(r.rating), colors), legend=legend)


def scene_recent(ctx: SceneContext) -> SceneResult:
    on_shelf = sorted(
        (ctx.releases[i] for i in ctx.placement.order if i in ctx.releases),
        key=lambda r: r.date_added or "",
    )
    n = len(on_shelf)
    rank = {r.instance_id: i for i, r in enumerate(on_shelf)}
    out: dict[int, RGB] = {}
    for px, iid in ctx.placement.pixel_map().items():
        if iid in rank:
            out[px] = _gradient((20, 20, 40), (0, 255, 160), rank[iid] / max(1, n - 1))
    legend = [
        {"label": "Oldest additions", "color": (20, 20, 40), "count": 0},
        {"label": "Newest additions", "color": (0, 255, 160), "count": 0},
    ]
    return SceneResult(colors=out, legend=legend)


SCENES: dict[str, tuple[str, str, SceneFn]] = {
    "decade": (
        "By decade",
        "Cool blues for the oldest records through warm gold for the newest.",
        scene_decade,
    ),
    "genre": ("By genre", "One color per Discogs genre, most common first.", scene_genre),
    "style": ("By style", "One color per Discogs style, most common first.", scene_style),
    "section": ("By section", "Colors follow the sections in your ordering scheme.", scene_section),
    "label": ("By label", "Your most common labels get a color each.", scene_label),
    "rating": ("By rating", "Dim for unrated, gold for five stars.", scene_rating),
    "recent": ("Recently added", "Bright green for the newest arrivals.", scene_recent),
}


def list_scenes() -> list[dict]:
    return [{"name": k, "title": t, "description": d} for k, (t, d, _) in SCENES.items()]
