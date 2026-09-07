from recordshelf.distribute import distribute, starts_from_counts
from recordshelf.shelf import Placement


def test_distribute_exact_sums():
    assert distribute([40, 40, 40], 100) == [34, 33, 33]
    assert sum(distribute([40, 20, 40], 501)) == 501
    assert distribute([0, 0], 5) == [3, 2]
    assert distribute([], 5) == []
    assert starts_from_counts([3, 4, 0, 2]) == [0, 3, 7, 7]


def test_placement_without_boundaries(layout):
    order = list(range(1000, 1500))  # 500 records across 25 boxes of capacity 40
    p = Placement(order, {}, layout)
    assert [r.count for r in p.ranges] == [20] * 25
    loc = p.locate(1000)
    assert loc.box.id == "r0c0" and loc.index_in_box == 0 and loc.pixel == 0
    loc = p.locate(1499)
    assert loc.box.id == "r4c4" and loc.index_in_box == 19 and loc.pixel == 499
    assert p.records_in_box("r0c1") == list(range(1020, 1040))
    assert p.locate(9999) is None


def test_placement_with_partial_calibration(layout):
    order = list(range(100))
    boxes = layout.record_boxes
    # calibrate box 2 to start at record 50; boxes 0-1 share [0,50), boxes 2-24 share [50,100)
    p = Placement(order, {boxes[2].id: 50}, layout)
    assert p.ranges[0].start == 0 and p.ranges[1].start == 25 and p.ranges[2].start == 50
    assert p.boundaries[boxes[2].id] == 50
    # boundary out of order is clamped, not honoured
    p2 = Placement(order, {boxes[1].id: 60, boxes[2].id: 50}, layout)
    assert p2.ranges[1].start == 60 and p2.ranges[2].start == 60


def test_pixel_map_first_record_wins(layout):
    order = list(range(40))  # 40 records in box r0c0 of 20 LEDs -> two per LED
    p = Placement(order, {layout.record_boxes[1].id: 40}, layout)
    pm = p.pixel_map()
    assert pm[0] == 0 and pm[1] == 2 and pm[19] == 38
