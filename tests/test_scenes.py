from recordshelf.db import Database
from recordshelf.details import parse_details
from recordshelf.discogs import parse_item
from recordshelf.models import Override, Scheme
from recordshelf.render.scenes import (
    MISSING,
    OTHER,
    PALETTE,
    SCENES,
    SceneContext,
    list_scenes,
    vinyl_color,
)
from recordshelf.shelf import Placement
from tests.conftest import item


def record(iid, artist, *, artists=(), labels=(), text=None, descriptions=("LP",), **kw):
    it = item(iid, artist, f"Record {iid}", descriptions=descriptions, **kw)
    info = it["basic_information"]
    if artists:
        info["artists"] = [{"name": a, "join": "/"} for a in artists]
    if labels:
        info["labels"] = [{"name": n, "catno": ""} for n in labels]
    if text:
        info["formats"][0]["text"] = text
    return it


def context(items, layout, placed=(), overrides=None, details=None) -> SceneContext:
    db = Database(":memory:")
    db.replace_collection(parse_item(i) for i in items)
    releases = {r.instance_id: r for r in db.list_releases()}
    return SceneContext(
        releases,
        Placement(list(placed), {}, layout),
        Scheme(),
        overrides or {},
        basic=db.basic_info(),
        details=details or {},
    )


def labels(result) -> list[str]:
    return [e["label"] for e in result.legend]


def pixel(ctx: SceneContext, iid: int) -> int:
    loc = ctx.placement.locate(iid)
    assert loc is not None and loc.pixel is not None
    return loc.pixel


def test_palette_has_ten_named_distinct_colors():
    assert len(PALETTE) == 10
    assert len({n for n, _ in PALETTE}) == 10 and len({c for _, c in PALETTE}) == 10
    assert OTHER[1] not in {c for _, c in PALETTE}


def test_top_artists_rank_every_shelf_record_not_just_placed(layout):
    items = [record(i, "Thou") for i in range(1, 4)]  # three LPs, none placed yet
    items += [record(4, "Queen"), record(5, "Queen", added="2021-01-01T00:00:00-08:00")]
    items += [record(i, "Radiohead", descriptions=['7"']) for i in range(6, 10)]  # not shelf
    items += [record(10, "Various"), record(11, "Hive Rituals", artists=["Hive Rituals", "Thou"])]
    items += [record(12, "Bush (2)")]
    ctx = context(items, layout, placed=[4, 12, 6])
    result = SCENES["artist"][2](ctx)
    # Thou: 3 LPs plus the split; the placed 7" counts because it is on the shelf; Various never
    assert labels(result) == [
        "Red · Thou (4)",
        "Green · Queen (2)",
        "Blue · Bush (1)",
        "Yellow · Hive Rituals (1)",
        "Purple · Radiohead (1)",
        "Grey · everything else (1)",
    ]
    assert result.legend[0] | {"item": "Thou", "color_name": "Red", "count": 4} == result.legend[0]
    # only placed records light up
    assert set(result.colors) == {pixel(ctx, 4), pixel(ctx, 12), pixel(ctx, 6)}
    assert result.colors[pixel(ctx, 4)] == PALETTE[1][1]
    # filing more records doesn't change the ranking
    later = context(items, layout, placed=[4, 12, 6, 1, 2, 11])
    assert labels(SCENES["artist"][2](later)) == labels(result)


def test_excluded_records_leave_the_counts(layout):
    items = [record(1, "Thou"), record(2, "Thou"), record(3, "Queen")]
    ctx = context(items, layout, overrides={1: Override(instance_id=1, excluded=True)})
    assert labels(SCENES["artist"][2](ctx))[0] == "Red · Queen (1)"


def test_top_n_folds_the_rest_into_everything_else(layout):
    items = [record(i, f"Artist {i:02}", year=1990 + i) for i in range(1, 13)]
    items += [record(20, "Artist 01", year=1991), record(21, "No Year")]
    ctx = context(items, layout, placed=[1, 12, 21])
    result = SCENES["year"][2](ctx)
    assert len(result.legend) == 11
    assert result.legend[0]["label"] == "Red · 1991 (2)"
    assert result.legend[-1]["label"] == "Grey · everything else (3)"  # 2 years + unknown year
    assert result.colors[pixel(ctx, 1)] == PALETTE[0][1]
    assert result.colors[pixel(ctx, 12)] == OTHER[1]
    assert result.colors[pixel(ctx, 21)] == OTHER[1]
    genre = SCENES["genre"][2](context([record(1, "A", genres=["Rock"])], layout))
    assert labels(genre) == ["Red · Rock (1)"]


def test_labels_credit_every_label_and_skip_not_on_label(layout):
    items = [
        record(1, "A", labels=["Topshelf Records (2)", "Polyvinyl Record Company"]),
        record(2, "B", labels=["Polyvinyl Record Company"]),
        record(3, "C", labels=["Not On Label (Thou Self-released)"]),
    ]
    assert labels(SCENES["label"][2](context(items, layout))) == [
        "Red · Polyvinyl Record Company (2)",
        "Green · Topshelf Records (1)",
        "Grey · everything else (1)",
    ]


def test_vinyl_color_reads_the_format_text():
    def color(text):
        return vinyl_color({"formats": [{"name": "Vinyl", "text": text}]})

    assert color("Red Translucent") == "red"
    assert color("Black/Gold Splatter") == "yellow"
    assert color("Crystal Clear With Black & White Splatter") == "white"
    assert color("Coke Bottle Clear") == "clear"
    assert color("Grey Marbled") is None and color("180g, Gatefold") is None


def test_vinyl_and_pressing_scenes(layout):
    items = [
        record(1, "A", text="Clear"),
        record(2, "B", text="Red/Black Splatter"),
        record(3, "C", text="Transparent Red"),
        record(4, "D", descriptions=["LP", "Limited Edition", "Numbered", "Repress"]),
        record(5, "E", descriptions=["LP", "Reissue"]),
    ]
    ctx = context(items, layout, placed=[1, 2])
    vinyl = SCENES["vinyl"][2](ctx)
    assert labels(vinyl) == [
        "Red · red vinyl (2)",
        "Cyan · clear vinyl (1)",
        "Grey · black, grey, brown or not noted (2)",
    ]
    assert vinyl.colors[pixel(ctx, 1)] == vinyl.legend[1]["color"]
    assert labels(SCENES["pressing"][2](ctx)) == [
        "Red · numbered (1)",
        "Green · reissue or remaster (1)",
        "Grey · no pressing notes (3)",
    ]


def details_json(credits=(), pressed_by=(), have=10, want=5):
    return {
        "extraartists": [{"name": n, "role": role} for n, role in credits],
        "companies": [{"name": n, "entity_type_name": "Pressed By"} for n in pressed_by],
        "community": {"have": have, "want": want},
    }


def test_detail_scenes_wait_for_details(layout):
    items = [record(1, "A"), record(2, "B")]
    ctx = context(items, layout, placed=[1])
    for name in ("producers", "mastering", "musicians", "plants", "value", "wanted"):
        result = SCENES[name][2](ctx)
        assert labels(result) == ["Off · details not fetched yet (2)"], name
        assert result.colors == {pixel(ctx, 1): MISSING[1]}


def test_credit_scenes(layout):
    items = [
        record(1, "Converge"),
        record(2, "Converge"),
        record(3, "Thou"),
        record(4, "Old Man Gloom"),
        record(5, "Unfetched"),
    ]
    raw = {
        10: details_json(
            [
                ("Kurt Ballou", "Producer, Mixed By"),
                ("Converge", "Producer"),
                ("Nate Newton", "Bass"),
            ],
            ["United Record Pressing"],
            have=100,
            want=300,
        ),
        20: details_json([("Kurt Ballou", "Recorded By"), ("Nate Newton", "Bass, Vocals")]),
        30: details_json([("Carl Saff", "Mastered By"), ("Jane Doe (2)", "Cello")]),
        40: details_json([("Nate Newton", "Guitar [Baritone]"), ("Carl Saff", "Lacquer Cut By")]),
    }
    details = {rid: parse_details(rid, data) for rid, data in raw.items()}
    ctx = context(items, layout, placed=[1, 5], details=details)
    assert labels(SCENES["producers"][2](ctx)) == [
        "Red · Kurt Ballou (2)",  # Converge producing itself is not counted
        "Grey · everything else (2)",
        "Off · details not fetched yet (1)",
    ]
    assert labels(SCENES["mastering"][2](ctx))[0] == "Red · Carl Saff (2)"
    musicians = labels(SCENES["musicians"][2](ctx))
    # Nate Newton plays for two artists; Jane Doe for only one, so she is not a session player
    assert musicians[0] == "Red · Nate Newton · 2 artists (3)"
    assert not any("Jane Doe" in m for m in musicians)
    assert labels(SCENES["plants"][2](ctx))[0] == "Red · United Record Pressing (1)"
    assert labels(SCENES["wanted"][2](ctx))[:2] == [
        "Red · 2+ wants per owner (1)",
        "Yellow · 0.5–1 wants per owner (3)",
    ]


def test_value_tiers_and_total(layout):
    items = [record(i, f"A{i}") for i in range(1, 5)]
    prices = {
        10: 150.0,
        20: 12.0,
        30: 11.5,
    }
    details = {
        rid: parse_details(
            rid, details_json(), {"Very Good Plus (VG+)": {"currency": "USD", "value": v}}
        )
        for rid, v in prices.items()
    }
    details[40] = parse_details(40, details_json())
    result = SCENES["value"][2](context(items, layout, details=details))
    assert labels(result) == [
        "Red · $100 and up (1)",
        "Cyan · $10–$20 (2)",
        "Grey · no price suggestion (1)",
    ]
    assert result.note == "Discogs suggests $174 for the 3 priced shelf records in VG+"


def test_list_scenes_previews_every_legend(layout):
    ctx = context([record(1, "Thou", genres=["Rock"])], layout)
    scenes = {s["name"]: s for s in list_scenes(ctx)}
    assert set(scenes) == set(SCENES)
    assert scenes["artist"]["legend"][0]["label"] == "Red · Thou (1)"
    assert scenes["value"]["needs_details"] and not scenes["artist"]["needs_details"]
    assert "legend" not in list_scenes()[0]
