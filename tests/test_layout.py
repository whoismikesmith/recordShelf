import pytest

from recordshelf.layout import ResolvedLayout
from recordshelf.models import LayoutConfig


def test_example_resolves(layout):
    assert layout.total_pixels == 500
    assert layout.controller_offsets == {"wled-a": 0, "wled-b": 400}
    assert len(layout.boxes) == 25
    assert len(layout.record_boxes) == 25
    b = layout.by_id["r0c1"]
    assert (b.controller, b.led_start, b.led_count, b.global_start) == ("wled-a", 20, 20, 20)
    b = layout.by_id["r4c0"]
    assert (b.controller, b.led_start, b.global_start) == ("wled-b", 0, 400)
    assert layout.controller_slice("wled-b") == (400, 100)


def test_reversed_strip_and_pixel_mapping():
    cfg = LayoutConfig(
        rows=1,
        cols=2,
        controllers=[{"id": "c", "type": "none", "led_count": 40}],
        strips=[{"id": "s", "controller": "c", "count": 40, "boxes": [[0, 1], [0, 0]]}],
    )
    lay = ResolvedLayout(cfg)
    right, left = lay.by_id["r0c1"], lay.by_id["r0c0"]
    assert right.led_start == 0 and left.led_start == 20
    assert right.reversed and left.reversed
    # 10 records over 20 LEDs: each record spans two LEDs and lights the centre of its span.
    # The first record is leftmost, and in a reversed box the leftmost LED has the highest index.
    assert left.pixel_for(0, 10) == 20 + 18
    assert left.pixel_for(9, 10) == 20 + 0
    assert right.pixel_for(0, 1) == 9  # a lone record sits in the middle of its box


def test_uneven_split_distributes_remainder():
    cfg = LayoutConfig(
        rows=1,
        cols=3,
        controllers=[{"id": "c", "type": "none", "led_count": 10}],
        strips=[{"id": "s", "controller": "c", "count": 10, "boxes": [[0, 0], [0, 1], [0, 2]]}],
    )
    lay = ResolvedLayout(cfg)
    assert [lay.by_id[f"r0c{i}"].led_count for i in range(3)] == [4, 3, 3]
    assert [lay.by_id[f"r0c{i}"].led_start for i in range(3)] == [0, 4, 7]


def test_box_overrides_and_orders():
    cfg = LayoutConfig(
        rows=2,
        cols=2,
        capacity_default=10,
        record_order="column-major",
        controllers=[{"id": "c", "type": "none", "led_count": 8}],
        strips=[
            {"id": "s", "controller": "c", "count": 8, "boxes": [[0, 0], [0, 1], [1, 0], [1, 1]]}
        ],
        boxes=[
            {"at": [0, 0], "kind": "other", "label": "Turntable"},
            {"at": [1, 1], "capacity": 3},
        ],
    )
    lay = ResolvedLayout(cfg)
    assert [b.id for b in lay.record_boxes] == ["r1c0", "r0c1", "r1c1"]
    assert lay.by_id["r0c0"].kind == "other" and lay.by_id["r0c0"].label == "Turntable"
    assert lay.by_id["r1c1"].capacity == 3 and lay.by_id["r0c1"].capacity == 10


def test_validation_errors():
    with pytest.raises(ValueError, match="more than one strip"):
        LayoutConfig(
            rows=1,
            cols=2,
            controllers=[{"id": "c", "type": "none", "led_count": 40}],
            strips=[
                {"id": "a", "controller": "c", "count": 20, "boxes": [[0, 0]]},
                {"id": "b", "controller": "c", "start": 20, "count": 20, "boxes": [[0, 0]]},
            ],
        )
    with pytest.raises(ValueError, match="only has"):
        LayoutConfig(
            rows=1,
            cols=1,
            controllers=[{"id": "c", "type": "none", "led_count": 10}],
            strips=[{"id": "a", "controller": "c", "count": 20, "boxes": [[0, 0]]}],
        )
    with pytest.raises(ValueError, match="unknown controller"):
        LayoutConfig(
            rows=1, cols=1, strips=[{"id": "a", "controller": "x", "count": 2, "boxes": [[0, 0]]}]
        )
