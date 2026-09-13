import sqlite3

import httpx
import pytest

from recordshelf.db import Database
from recordshelf.details import (
    PRICES,
    RELEASE,
    DetailsStore,
    EnrichManager,
    enrich_targets,
    parse_details,
    split_roles,
)
from recordshelf.models import Override, Scheme
from tests.test_discogs import make_client


def release_json(rid: int, **extra) -> dict:
    return {
        "id": rid,
        "country": "US",
        "extraartists": [
            {
                "name": "Steve Albini",
                "anv": "S. Albini",
                "role": "Recorded By, Mixed By [Assistant]",
            },
            {"name": "Bob Weston", "role": "Mastered By"},
        ],
        "tracklist": [
            {"title": "A1", "extraartists": [{"name": "Steve Albini", "role": "Mixed By"}]},
            {"title": "A2", "extraartists": [{"name": "Jane Doe (2)", "role": "Cello"}]},
        ],
        "companies": [
            {"name": "United Record Pressing", "entity_type_name": "Pressed By"},
            {"name": "Chicago Mastering Service", "entity_type_name": "Mastered At"},
        ],
        "community": {"have": 120, "want": 300, "rating": {"average": 4.5, "count": 20}},
        "lowest_price": 18.5,
        "num_for_sale": 4,
        **extra,
    }


def test_split_roles_keeps_bracket_commas():
    assert split_roles("Producer, Mixed By [Tracks A1, B2]") == ["Producer", "Mixed By"]
    assert split_roles("Guitar [12-String], Vocals") == ["Guitar", "Vocals"]
    assert split_roles("") == []


def test_parse_details_counts_people_once_per_role():
    prices = {"Very Good Plus (VG+)": {"currency": "USD", "value": 22.0}}
    d = parse_details(7, release_json(7), prices, "USD")
    assert d.credits["Mixed By"] == {"Steve Albini"}
    assert d.credits["Cello"] == {"Jane Doe (2)"}
    assert d.companies["Pressed By"] == {"United Record Pressing"}
    assert (d.country, d.have, d.want, d.rating, d.lowest_price) == ("US", 120, 300, 4.5, 18.5)
    assert d.suggested == {"Very Good Plus (VG+)": 22.0} and d.suggested_currency == "USD"


def test_enrich_targets_shelf_first_and_unique(db):
    releases = db.list_releases()
    scheme = Scheme()  # LP / 12" only: the Radiohead 7" (instance 9) is not a shelf record
    targets = enrich_targets(releases, scheme, {2: Override(instance_id=2, excluded=True)})
    assert len(targets) == 10 and len({t.release_id for t in targets}) == 10
    assert [t.shelf for t in targets] == [True] * 8 + [False] * 2
    assert {t.release_id for t in targets if not t.shelf} == {20, 90}
    # placing a record by hand makes it a shelf record even if the scheme skips it
    placed = enrich_targets(releases, scheme, {}, placed=[9])
    assert all(t.shelf for t in placed)


def discogs_api(calls: list[str], price_status: int = 200):
    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        calls.append(path)
        if path == "/users/tester":
            return httpx.Response(200, json={"curr_abbr": "GBP"})
        if path.startswith("/releases/"):
            rid = int(path.rsplit("/", 1)[1])
            if rid == 404:
                return httpx.Response(404, json={"message": "Release not found."})
            assert request.url.params["curr_abbr"] == "GBP"
            return httpx.Response(200, json=release_json(rid))
        if path.startswith("/marketplace/price_suggestions/"):
            if price_status != 200:
                return httpx.Response(price_status, json={"message": "Fill out seller settings"})
            return httpx.Response(200, json={"Mint (M)": {"currency": "GBP", "value": 30}})
        return httpx.Response(500)

    return handler


async def test_enrich_fetches_caches_and_resumes(db):
    store = DetailsStore(":memory:")
    targets = enrich_targets(db.list_releases(), Scheme(), {})[:3]
    calls: list[str] = []
    mgr = EnrichManager(store, lambda: make_client(discogs_api(calls)))
    mgr.start(targets)
    st = await mgr.wait()
    assert (st.state, st.fetched, st.prices, st.cached, st.errors) == ("done", 3, 3, 0, 0)
    assert store.counts() == {RELEASE: 3, PRICES: 3, "failed": 0}
    rid = targets[0].release_id
    details = store.details()[rid]
    assert details.currency == "GBP" and details.suggested == {"Mint (M)": 30.0}

    calls.clear()
    mgr = EnrichManager(store, lambda: make_client(discogs_api(calls)))
    mgr.start(targets)
    st = await mgr.wait()
    assert (st.fetched, st.cached) == (0, 3) and calls == ["/users/tester"]

    mgr = EnrichManager(store, lambda: make_client(discogs_api(calls)))
    mgr.start(targets[:1], refresh_days=0)
    assert (await mgr.wait()).fetched == 1


async def test_enrich_skips_refused_prices_and_stores_not_found(db):
    store = DetailsStore(":memory:")
    targets = enrich_targets(db.list_releases(), Scheme(), {})[:2]
    targets.insert(1, type(targets[0])(404, "Gone - Deleted", True))
    calls: list[str] = []
    mgr = EnrichManager(store, lambda: make_client(discogs_api(calls, price_status=422)))
    mgr.start(targets)
    st = await mgr.wait()
    assert st.state == "done" and st.fetched == 2 and st.prices == 0
    assert "seller settings" in (st.prices_skipped or "")
    assert sum(p.startswith("/marketplace") for p in calls) == 1  # asked once, then stopped
    assert store.counts() == {RELEASE: 2, PRICES: 0, "failed": 1}
    assert 404 in store.fetched_at(RELEASE)  # not asked again on the next run


async def test_enrich_stops_after_repeated_failures(db):
    store = DetailsStore(":memory:")
    targets = enrich_targets(db.list_releases(), Scheme(), {})
    mgr = EnrichManager(
        store,
        lambda: make_client(lambda r: httpx.Response(503), token=""),
        max_consecutive_errors=3,
    )
    mgr.start(targets)
    st = await mgr.wait()
    assert st.state == "error" and st.errors == 3 and store.counts()[RELEASE] == 0
    assert st.prices_skipped == "price suggestions need a Discogs token"


def test_readonly_database_refuses_writes(tmp_path):
    path = tmp_path / "shelf.sqlite"
    Database(path).set_order([3, 1, 2])
    ro = Database(path, readonly=True)
    assert ro.get_order() == [3, 1, 2]
    with pytest.raises(sqlite3.OperationalError):
        ro.set_order([1])
    assert Database(path).get_order() == [3, 1, 2]
