from recordshelf.discogs import artist_display, sort_name
from recordshelf.models import Override, Scheme
from recordshelf.ordering import build_plan, eligible, ordered_releases, section_for


def test_artist_parsing():
    assert sort_name("The Beatles") == "beatles"
    assert sort_name("Bush (2)") == "bush"
    assert (
        sort_name("...And You Will Know Us By The Trail Of Dead")
        == "and you will know us by the trail of dead"
    )
    assert sort_name("!!!") == "!!!"
    assert sort_name("A Tribe Called Quest") == "tribe called quest"
    assert (
        artist_display(
            [{"name": "Miles Davis", "join": "&"}, {"name": "John Coltrane", "join": ""}]
        )
        == "Miles Davis & John Coltrane"
    )
    assert artist_display([{"name": "A", "join": ","}, {"name": "B", "join": ""}]) == "A, B"


def test_parse_item_shapes(db):
    r = db.get_release(5)
    assert r.artist == "Bush" and r.artist_sort == "bush" and r.year == 1994
    assert r.descriptions == ["LP"] and r.styles == ["Grunge"] and r.catno == "CAT5"


def test_eligibility(db):
    scheme = Scheme()
    rel = {r.instance_id: r for r in db.list_releases()}
    assert eligible(rel[1], scheme, None)
    assert not eligible(rel[9], scheme, None)  # 7" single
    assert not eligible(rel[1], scheme, Override(instance_id=1, excluded=True))
    assert eligible(rel[9], Scheme(include_descriptions=[]), None)


def test_sections(db):
    rel = {r.instance_id: r for r in db.list_releases()}
    scheme = Scheme(
        section_by="genre",
        style_map={"Grunge": "90s Rock"},
        genre_map={"Hip Hop": "Hip-Hop & Soul"},
    )
    assert section_for(rel[1], scheme, None) == "Rock"
    assert section_for(rel[6], scheme, None) == "90s Rock"
    assert section_for(rel[10], scheme, None) == "Hip-Hop & Soul"
    assert section_for(rel[2], scheme, Override(instance_id=2, section="Favorites")) == "Favorites"
    assert section_for(rel[2], Scheme(section_by="decade"), None) == "1950s"


def test_ordered_releases_sections_and_various_last(db):
    scheme = Scheme(section_by="genre", section_order=["Jazz", "Rock"], within=["artist", "year"])
    ordered, excluded = ordered_releases(db.list_releases(), scheme, {})
    assert excluded == 1
    names = [(sec, r.artist) for r, sec in ordered]
    assert names[:2] == [("Jazz", "John Coltrane"), ("Jazz", "Miles Davis")]
    assert names[2:5] == [("Rock", "The Beatles"), ("Rock", "Bush"), ("Rock", "Nirvana")]
    # remaining sections alphabetical: Electronic, Hip Hop, Pop
    assert [s for s, _ in names[5:]] == ["Electronic", "Electronic", "Hip Hop", "Pop"]
    assert names[-1] == ("Pop", "Various")


def test_plan_distributes_by_capacity(db, layout):
    boxes = layout.record_boxes[:3]
    plan = build_plan(db.list_releases(), Scheme(), {}, boxes, current_box_of={1: "r0c2"})
    assert plan.excluded == 1 and plan.unassigned == 0
    assert [b.count for b in plan.boxes] == [3, 3, 3]
    assert [b.first_position for b in plan.boxes] == [0, 3, 6]
    assert len(plan.items) == 9
    assert plan.items[0].box_id == "r0c0"
    assert (
        plan.moved_count == 1
    )  # Beatles claimed to be in r0c2 currently but plan puts them in r0c0
    assert plan.to_dict()["total"] == 9
