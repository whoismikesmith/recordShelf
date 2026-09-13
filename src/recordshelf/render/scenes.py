"""Scenes paint the whole shelf by a record attribute. Each returns pixel colors and a legend.

Rankings and legend counts cover every shelf record (placed, or eligible by the scheme), not
only the ones placed so far, so a top 10 stays put while filing continues. Only placed records
light up. Legend entries name the LED color, the item and its count: "Red · Thou (19)".
"""

from __future__ import annotations

import re
from collections import Counter
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from typing import Any

from ..details import ReleaseDetails
from ..discogs import clean_artist_name
from ..models import RGB, Override, Release, Scheme
from ..ordering import VARIOUS, eligible, section_for
from ..shelf import Placement

Swatch = tuple[str, RGB]

# Ten hues that stay apart on WS2812B LEDs, most distinct first so short lists get the best.
PALETTE: list[Swatch] = [
    ("Red", (255, 0, 0)),
    ("Green", (0, 255, 0)),
    ("Blue", (0, 30, 255)),
    ("Yellow", (255, 180, 0)),
    ("Purple", (150, 0, 255)),
    ("Cyan", (0, 210, 255)),
    ("Orange", (255, 70, 0)),
    ("Pink", (255, 0, 110)),
    ("White", (255, 255, 255)),
    ("Lime", (130, 255, 0)),
]
SWATCH: dict[str, Swatch] = {name: (name, rgb) for name, rgb in PALETTE}
OTHER: Swatch = ("Grey", (40, 40, 40))
MISSING: Swatch = ("Off", (0, 0, 0))


@dataclass
class SceneResult:
    colors: dict[int, RGB]
    legend: list[dict] = field(default_factory=list)
    note: str | None = None


@dataclass
class SceneContext:
    releases: dict[int, Release]
    placement: Placement
    scheme: Scheme
    overrides: dict[int, Override]
    basic: dict[int, dict[str, Any]] = field(default_factory=dict)  # Discogs basic_information
    details: dict[int, ReleaseDetails] = field(default_factory=dict)  # by release_id

    def shelf_records(self) -> list[Release]:
        placed = self.placement.position
        return [
            r
            for r in self.releases.values()
            if r.instance_id in placed
            or eligible(r, self.scheme, self.overrides.get(r.instance_id))
        ]

    def info(self, r: Release) -> dict[str, Any]:
        """Discogs basic_information, or what the Release row alone can say."""
        return self.basic.get(r.instance_id) or {
            "artists": [{"name": r.artist}],
            "labels": [{"name": r.label}] if r.label else [],
            "formats": [{"name": r.format, "descriptions": r.descriptions}],
        }


SceneFn = Callable[[SceneContext], SceneResult]


def entry(swatch: Swatch, item: str, count: int) -> dict:
    name, rgb = swatch
    return {
        "label": f"{name} · {item} ({count})",
        "item": item,
        "color_name": name,
        "color": rgb,
        "count": count,
    }


def _paint(
    ctx: SceneContext, key: Callable[[Release], str], colors: dict[str, RGB]
) -> dict[int, RGB]:
    out: dict[int, RGB] = {}
    for px, iid in ctx.placement.pixel_map().items():
        r = ctx.releases.get(iid)
        if r is None:
            continue
        out[px] = colors.get(key(r), OTHER[1])
    return out


def _ranked(
    ctx: SceneContext,
    values: Callable[[Release], Iterable[str] | None],
    n: int = len(PALETTE),
    order: list[str] | None = None,
    colors: dict[str, Swatch] | None = None,
    label: Callable[[str], str] = str,
    rest: str = "everything else",
    note: str | None = None,
) -> SceneResult:
    """Color each record by its first value in the top `n`.

    Values count once per record over all shelf records, most common first unless `order` is
    given. A record with several values (a split LP, a co-release) takes the best-ranked one.
    `values` returns None when the data is not there yet: those records stay off and get
    their own legend line.
    """
    per: dict[int, list[str] | None] = {}
    for r in ctx.shelf_records():
        v = values(r)
        per[r.instance_id] = None if v is None else list(dict.fromkeys(v))
    counts = Counter(x for vs in per.values() if vs for x in vs)
    if order is None:
        order = sorted(counts, key=lambda k: (-counts[k], k.casefold()))
    top = [k for k in order if counts.get(k)][:n]
    swatch = {k: (colors or {}).get(k) or PALETTE[i % len(PALETTE)] for i, k in enumerate(top)}
    rank = {k: i for i, k in enumerate(top)}

    def pick(vs: list[str] | None) -> Swatch:
        if vs is None:
            return MISSING
        best = min((rank[x] for x in vs if x in rank), default=None)
        return OTHER if best is None else swatch[top[best]]

    colors_out: dict[int, RGB] = {}
    for px, iid in ctx.placement.pixel_map().items():
        if iid in per:
            colors_out[px] = pick(per[iid])[1]
    legend = [entry(swatch[k], label(k), counts[k]) for k in top]
    others = sum(1 for vs in per.values() if vs is not None and not any(x in rank for x in vs))
    missing = sum(1 for vs in per.values() if vs is None)
    if others:
        legend.append(entry(OTHER, rest, others))
    if missing:
        legend.append(entry(MISSING, "details not fetched yet", missing))
    return SceneResult(colors=colors_out, legend=legend, note=note)


def _gradient(a: RGB, b: RGB, k: float) -> RGB:
    k = max(0.0, min(1.0, k))
    return tuple(int(a[i] + (b[i] - a[i]) * k) for i in range(3))  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# From the synced collection
# ---------------------------------------------------------------------------


def scene_artist(ctx: SceneContext) -> SceneResult:
    def artists(r: Release) -> list[str]:
        names = [a.get("name") or "" for a in ctx.info(r).get("artists") or []]
        return [n for n in names if n and clean_artist_name(n).casefold() not in VARIOUS]

    return _ranked(ctx, artists, n=10, label=clean_artist_name)


def scene_label(ctx: SceneContext) -> SceneResult:
    def labels(r: Release) -> list[str]:
        names = [x.get("name") or "" for x in ctx.info(r).get("labels") or []]
        return [n for n in names if n and not n.casefold().startswith("not on label")]

    return _ranked(ctx, labels, n=10, label=clean_artist_name)


def scene_genre(ctx: SceneContext) -> SceneResult:
    return _ranked(ctx, lambda r: r.genres[:1], n=5)


def scene_style(ctx: SceneContext) -> SceneResult:
    return _ranked(ctx, lambda r: r.styles[:1], n=10)


def scene_year(ctx: SceneContext) -> SceneResult:
    return _ranked(ctx, lambda r: [str(r.year)] if r.year else [], n=10)


# Words in the Discogs format text ("Red Translucent", "Black/Gold Splatter") -> color family.
_VINYL_WORDS = {
    **dict.fromkeys(["clear", "transparent", "crystal", "coke", "cokebottle"], "clear"),
    **dict.fromkeys(["white", "cream", "bone", "beige"], "white"),
    **dict.fromkeys(["red", "maroon", "blood", "oxblood", "burgundy"], "red"),
    **dict.fromkeys(["pink", "magenta", "peach"], "pink"),
    **dict.fromkeys(["orange", "amber", "creamsicle"], "orange"),
    **dict.fromkeys(["yellow", "gold", "mustard"], "yellow"),
    **dict.fromkeys(["green", "mint", "jade", "lime", "teal", "turquoise", "seafoam"], "green"),
    **dict.fromkeys(["blue", "navy", "cyan"], "blue"),
    **dict.fromkeys(["purple", "plum", "violet", "lavender", "lilac"], "purple"),
    **dict.fromkeys(["black", "grey", "gray", "silver", "smoke", "brown", "tan"], "dark"),
}
VINYL: dict[str, tuple[str, Swatch]] = {
    "white": ("white or cream vinyl", SWATCH["White"]),
    "clear": ("clear vinyl", SWATCH["Cyan"]),
    "red": ("red vinyl", SWATCH["Red"]),
    "blue": ("blue vinyl", SWATCH["Blue"]),
    "green": ("green or teal vinyl", SWATCH["Green"]),
    "yellow": ("yellow or gold vinyl", SWATCH["Yellow"]),
    "pink": ("pink vinyl", SWATCH["Pink"]),
    "orange": ("orange vinyl", SWATCH["Orange"]),
    "purple": ("purple vinyl", SWATCH["Purple"]),
}


def vinyl_color(info: dict[str, Any]) -> str | None:
    """The first bright color named in the format text; clear only if nothing else is."""
    for f in info.get("formats") or []:
        words = re.findall(r"[a-z]+", (f.get("text") or "").casefold())
        hits = [_VINYL_WORDS[w] for w in words if w in _VINYL_WORDS]
        if not hits:
            continue
        bright = [h for h in hits if h in VINYL and h != "clear"]
        return bright[0] if bright else ("clear" if "clear" in hits else None)
    return None


def scene_vinyl(ctx: SceneContext) -> SceneResult:
    def color(r: Release) -> list[str]:
        c = vinyl_color(ctx.info(r))
        return [c] if c else []

    return _ranked(
        ctx,
        color,
        colors={k: sw for k, (_, sw) in VINYL.items()},
        label=lambda k: VINYL[k][0],
        rest="black, grey, brown or not noted",
    )


# First match wins, so a numbered repress counts as numbered.
PRESSINGS: list[tuple[str, frozenset[str]]] = [
    ("test pressing, promo or white label", frozenset({"Test Pressing", "Promo", "White Label"})),
    ("picture disc", frozenset({"Picture Disc"})),
    ("Record Store Day", frozenset({"Record Store Day"})),
    ("numbered", frozenset({"Numbered"})),
    ("etched or single-sided", frozenset({"Etched", "Single Sided"})),
    ("unofficial release", frozenset({"Unofficial Release"})),
    (
        "limited, special or deluxe edition",
        frozenset({"Limited Edition", "Special Edition", "Deluxe Edition"}),
    ),
    ("club edition", frozenset({"Club Edition"})),
    ("repress", frozenset({"Repress"})),
    ("reissue or remaster", frozenset({"Reissue", "Remastered"})),
]


def scene_pressing(ctx: SceneContext) -> SceneResult:
    def kind(r: Release) -> list[str]:
        tags = {d for f in ctx.info(r).get("formats") or [] for d in f.get("descriptions") or []}
        return next(([name] for name, want in PRESSINGS if want & tags), [])

    return _ranked(ctx, kind, order=[name for name, _ in PRESSINGS], rest="no pressing notes")


def scene_decade(ctx: SceneContext) -> SceneResult:
    shelf = ctx.shelf_records()
    years = [r.year for r in shelf if r.year]
    if not years:
        return SceneResult(colors={}, legend=[])
    lo, hi = (min(years) // 10) * 10, (max(years) // 10) * 10
    decades = list(range(lo, hi + 1, 10))
    colors: dict[str, RGB] = {}
    for i, d in enumerate(decades):
        k = i / max(1, len(decades) - 1)
        colors[f"{d}s"] = _gradient((60, 40, 255), (255, 200, 0), k)
    colors["Unknown"] = OTHER[1]
    counts = Counter(r.decade for r in shelf)
    legend = [
        {"label": d, "color": colors[d], "count": counts.get(d, 0)} for d in colors if counts.get(d)
    ]
    return SceneResult(colors=_paint(ctx, lambda r: r.decade, colors), legend=legend)


def scene_section(ctx: SceneContext) -> SceneResult:
    def key(r: Release) -> str:
        return section_for(r, ctx.scheme, ctx.overrides.get(r.instance_id)) or "All"

    order = None
    if ctx.scheme.section_order:
        seen = {key(r) for r in ctx.shelf_records()}
        order = [s for s in ctx.scheme.section_order if s in seen] + sorted(
            seen - set(ctx.scheme.section_order)
        )
    return _ranked(ctx, lambda r: [key(r)], order=order)


def scene_rating(ctx: SceneContext) -> SceneResult:
    colors = {str(n): _gradient((40, 40, 60), (255, 215, 0), n / 5) for n in range(6)}
    colors["0"] = OTHER[1]
    counts = Counter(str(r.rating) for r in ctx.shelf_records())
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


# ---------------------------------------------------------------------------
# From fetched release details (`recordshelf enrich`)
# ---------------------------------------------------------------------------


# Words that make a Discogs role a performance ("Backing Vocals", "Guitar", "Double Bass").
_PERFORMANCE = frozenset(
    re.findall(
        r"\w+",
        """performer musician instruments vocals voice choir chorus rap guitar bass drums
        percussion keyboards piano organ synthesizer moog mellotron rhodes wurlitzer clavinet
        harpsichord violin viola cello strings fiddle horn horns trumpet trombone tuba saxophone
        sax flute clarinet oboe bassoon harmonica banjo mandolin ukulele harp accordion
        glockenspiel vibraphone xylophone marimba bells timpani tambourine congas bongos cymbal
        tabla sitar theremin melodica turntables sampler electronics handclaps whistling""",
    )
)


def _is_performance(role: str) -> bool:
    return bool(set(re.findall(r"[a-z]+", role.casefold())) & _PERFORMANCE)


PRODUCTION = frozenset({"Producer", "Co-producer", "Recorded By", "Engineer", "Mixed By"})
MASTERING = frozenset({"Mastered By", "Lacquer Cut By", "Remastered By"})


def _people(ctx: SceneContext, r: Release, roles: Callable[[str], bool]) -> list[str] | None:
    d = ctx.details.get(r.release_id)
    if d is None:
        return None
    # A band credited as its own producer is not an outside producer.
    own = {a.get("name") for a in ctx.info(r).get("artists") or []}
    names = {n for role, ns in d.credits.items() if roles(role) for n in ns}
    return sorted(names - own)


def _credited(roles: frozenset[str]) -> SceneFn:
    def scene(ctx: SceneContext) -> SceneResult:
        people = lambda r: _people(ctx, r, roles.__contains__)  # noqa: E731
        return _ranked(ctx, people, n=10, label=clean_artist_name)

    return scene


scene_producers = _credited(PRODUCTION)
scene_mastering = _credited(MASTERING)


def scene_musicians(ctx: SceneContext) -> SceneResult:
    """Players credited across different artists' records, so one band's members don't fill
    the list: ranked by how many artists they play for, then by records."""
    per = {r.instance_id: _people(ctx, r, _is_performance) for r in ctx.shelf_records()}
    records: Counter[str] = Counter()
    artists: dict[str, set[str]] = {}
    for r in ctx.shelf_records():
        main = (ctx.info(r).get("artists") or [{}])[0].get("name") or r.artist
        for p in per[r.instance_id] or []:
            records[p] += 1
            artists.setdefault(p, set()).add(main)
    order = sorted(
        (p for p in records if len(artists[p]) > 1),
        key=lambda p: (-len(artists[p]), -records[p], p.casefold()),
    )
    return _ranked(
        ctx,
        lambda r: per.get(r.instance_id),
        n=10,
        order=order,
        label=lambda p: f"{clean_artist_name(p)} · {len(artists[p])} artists",
    )


def scene_plants(ctx: SceneContext) -> SceneResult:
    def plants(r: Release) -> list[str] | None:
        d = ctx.details.get(r.release_id)
        return None if d is None else sorted(d.companies.get("Pressed By", ()))

    return _ranked(ctx, plants, n=10, label=clean_artist_name, rest="everything else or not noted")


VG_PLUS = "Very Good Plus (VG+)"
_SYMBOLS = {"USD": "$", "GBP": "£", "EUR": "€", "JPY": "¥", "CAD": "CA$", "AUD": "A$"}


def money(v: float, currency: str) -> str:
    sym = _SYMBOLS.get(currency, f"{currency} ")
    return f"{sym}{v:,.0f}"


def scene_value(ctx: SceneContext) -> SceneResult:
    shelf = ctx.shelf_records()
    prices = {
        r.instance_id: d.suggested[VG_PLUS]
        for r in shelf
        if (d := ctx.details.get(r.release_id)) and VG_PLUS in d.suggested
    }
    currencies = Counter(d.suggested_currency for d in ctx.details.values() if d.suggested_currency)
    cur = currencies.most_common(1)[0][0] if currencies else "USD"
    bounds = [100, 60, 35, 20, 10, 0]
    names = [f"{money(100, cur)} and up"] + [
        f"{money(lo, cur)}–{money(hi, cur)}" for hi, lo in zip(bounds, bounds[1:-1], strict=False)
    ]
    names.append(f"under {money(10, cur)}")
    hues = ["Red", "Orange", "Yellow", "Green", "Cyan", "Blue"]

    def tier(r: Release) -> list[str] | None:
        if r.release_id not in ctx.details:
            return None
        p = prices.get(r.instance_id)
        if p is None:
            return []
        return [next(n for lo, n in zip(bounds, names, strict=True) if p >= lo)]

    total = sum(prices.values())
    note = (
        f"Discogs suggests {money(total, cur)} for the {len(prices)} priced shelf records in VG+"
        if prices
        else None
    )
    return _ranked(
        ctx,
        tier,
        order=names,
        colors={n: SWATCH[h] for n, h in zip(names, hues, strict=True)},
        rest="no price suggestion",
        note=note,
    )


def scene_wanted(ctx: SceneContext) -> SceneResult:
    tiers = [
        (2.0, "2+ wants per owner", "Red"),
        (1.0, "1–2 wants per owner", "Orange"),
        (0.5, "0.5–1 wants per owner", "Yellow"),
    ]

    def tier(r: Release) -> list[str] | None:
        d = ctx.details.get(r.release_id)
        if d is None:
            return None
        ratio = d.want / max(1, d.have)
        return next(([name] for lo, name, _ in tiers if ratio >= lo), [])

    return _ranked(
        ctx,
        tier,
        order=[name for _, name, _ in tiers],
        colors={name: SWATCH[hue] for _, name, hue in tiers},
        rest="under 0.5 wants per owner",
    )


SCENES: dict[str, tuple[str, str, SceneFn]] = {
    "artist": ("Top 10 artists", "Every credited artist, splits included.", scene_artist),
    "label": (
        "Top 10 labels",
        "Every label a record came out on, co-releases included.",
        scene_label,
    ),
    "genre": ("Top 5 genres", "Each record's main Discogs genre.", scene_genre),
    "year": ("Top 10 years", "The years your pressings came out.", scene_year),
    "style": ("Top 10 styles", "Each record's first Discogs style.", scene_style),
    "vinyl": ("Vinyl color", "The LED matches the color of the wax.", scene_vinyl),
    "pressing": (
        "Special pressings",
        "Test pressings, picture discs, RSD, numbered, etched, limited, represses.",
        scene_pressing,
    ),
    "decade": (
        "By decade",
        "Cool blues for the oldest records through warm gold for the newest.",
        scene_decade,
    ),
    "section": ("By section", "Colors follow the sections in your ordering scheme.", scene_section),
    "rating": ("By rating", "Dim for unrated, gold for five stars.", scene_rating),
    "recent": ("Recently added", "Bright green for the newest arrivals.", scene_recent),
    "producers": (
        "Top producers & engineers",
        "Who recorded, produced or mixed the most of your records.",
        scene_producers,
    ),
    "mastering": (
        "Top mastering engineers",
        "Who mastered or cut the lacquers.",
        scene_mastering,
    ),
    "musicians": (
        "Top session musicians",
        "Players credited on records by the most different artists.",
        scene_musicians,
    ),
    "plants": ("Top pressing plants", "Where the vinyl was pressed.", scene_plants),
    "value": ("Market value", "Discogs suggested VG+ price, cool to hot.", scene_value),
    "wanted": ("Most wanted", "Discogs users who want it per user who has it.", scene_wanted),
}

DETAIL_SCENES = frozenset({"producers", "mastering", "musicians", "plants", "value", "wanted"})


def list_scenes(ctx: SceneContext | None = None) -> list[dict]:
    """Scene metadata, plus a preview legend and note for each when a context is given."""
    out = []
    for name, (title, description, fn) in SCENES.items():
        item: dict[str, Any] = {
            "name": name,
            "title": title,
            "description": description,
            "needs_details": name in DETAIL_SCENES,
        }
        if ctx is not None:
            result = fn(ctx)
            item["legend"], item["note"] = result.legend, result.note
        out.append(item)
    return out
