import pytest
from fastapi.testclient import TestClient

from recordshelf.app import create_app
from recordshelf.settings import Settings


@pytest.fixture
def client(db, layout_file, tmp_path):
    settings = Settings(
        discogs_username="tester",
        discogs_token="",
        data_dir=tmp_path / "data",
        layout_file=layout_file,
        web_dist=tmp_path / "nope",
        _env_file=None,
    )
    app = create_app(settings, db)
    with TestClient(app) as c:
        yield c


def test_status_and_inbox(client):
    st = client.get("/api/status").json()
    assert (
        st["release_count"] == 10
        and st["on_shelf"] == 0
        and st["inbox"] == 9
        and st["skipped"] == 1
    )
    assert [c["id"] for c in st["controllers"]] == ["wled-a", "wled-b"]


def test_releases_search_and_facets(client):
    r = client.get("/api/releases", params={"q": "blue"}).json()
    assert r["total"] == 1 and r["items"][0]["title"] == "Kind of Blue"
    r = client.get("/api/releases", params={"genre": "Rock", "sort": "year"}).json()
    assert [x["year"] for x in r["items"]] == [1969, 1991, 1992, 1994]
    f = client.get("/api/facets").json()
    assert f["genres"][0] == {"value": "Rock", "count": 4}
    assert client.get("/api/releases/999").status_code == 404


def test_plan_apply_locate_and_calibrate(client):
    client.put("/api/scheme", json={"section_by": "genre", "section_order": ["Jazz", "Rock"]})
    plan = client.post("/api/plan").json()
    assert plan["total"] == 9 and plan["excluded"] == 1
    assert plan["items"][0]["artist"] == "John Coltrane"
    client.post("/api/plan/apply")
    order = client.get("/api/order").json()
    assert order["total"] == 9 and order["inbox"] == []
    # 9 records across 25 equal boxes: most boxes hold none, first 9 hold one each
    assert [b["count"] for b in order["boxes"][:10]] == [1] * 9 + [0]
    loc = client.post("/api/locate/2").json()  # Miles Davis, second in Jazz section
    assert loc["box_id"] == "r0c1" and loc["pixel"] == 30 and loc["artist"] == "Miles Davis"
    assert client.get("/api/status").json()["effect"]["name"] == "locate"
    # voice-style lookup
    loc = client.post("/api/locate", params={"q": "nevermind"}).json()
    assert loc["title"] == "Nevermind"
    # calibration: say Beatles are the first record in box r0c1
    resp = client.post("/api/calibrate", json={"box_id": "r0c1", "instance_id": 1}).json()
    assert resp["stored"]["r0c1"] == 2
    assert client.post("/api/locate/2").json()["box_id"] == "r0c0"
    client.post("/api/lights/off")
    assert client.get("/api/hooks/state").json()["on"] is False


def test_place_from_inbox_and_remove(client):
    client.post("/api/plan/apply")
    client.post("/api/order/remove", json={"instance_id": 6, "exclude": True})
    assert client.get("/api/status").json()["excluded"] == 1
    client.post("/api/order/place", json={"instance_id": 6})  # back onto the shelf, suggested slot
    order = client.get("/api/order").json()
    ids = [i["instance_id"] for b in order["boxes"] for i in b["items"]]
    assert ids.index(6) == ids.index(2) + 1  # Nirvana slots in after Miles Davis alphabetically
    assert client.get("/api/status").json()["excluded"] == 0
    # the 7" single is skipped by the scheme, not in the inbox; it can still be forced into a box
    view = client.get("/api/order").json()
    assert view["inbox"] == [] and [i["instance_id"] for i in view["skipped"]] == [9]
    client.post("/api/order/place", json={"instance_id": 9, "box_id": "r4c4"})
    order = client.get("/api/order").json()
    assert order["boxes"][-1]["items"][-1]["instance_id"] == 9


def test_put_boxes_and_suggest(client):
    client.put("/api/order/boxes", json={"boxes": {"r0c0": [2, 7], "r0c1": [1, 5, 6]}})
    order = client.get("/api/order").json()
    assert order["boxes"][0]["count"] == 2 and order["boxes"][1]["count"] == 3
    s = client.get("/api/order/suggest/3").json()  # Aphex Twin sorts first alphabetically
    assert s["position"] == 0 and s["box_id"] == "r0c0"


def test_scenes_and_lights(client):
    client.post("/api/plan/apply")
    scenes = client.get("/api/scenes").json()["scenes"]
    assert {s["name"] for s in scenes} >= {"decade", "genre", "section", "rating", "recent"}
    r = client.post("/api/scenes/genre").json()
    assert r["legend"][0]["label"] == "Rock"
    assert client.get("/api/status").json()["scene"]["name"] == "genre"
    assert (
        client.post("/api/lights/box/r2c2", json={"color": [0, 255, 0], "duration": 1}).status_code
        == 200
    )
    assert client.post("/api/lights/box/nope").status_code == 404
    assert client.post("/api/lights/identify").json()["boxes"][0]["box_id"] == "r0c0"
    assert client.get("/api/hooks/scene/decade").status_code == 200
    assert client.get("/api/hooks/off").json()["ok"]


def test_layout_roundtrip_and_validation(client, layout_file):
    cfg = client.get("/api/layout").json()
    cfg["name"] = "Renamed"
    cfg["boxes"] = [{"at": [0, 0], "kind": "other", "label": "Turntable"}]
    assert client.put("/api/layout", json=cfg).json()["name"] == "Renamed"
    assert "Renamed" in layout_file.read_text()
    resolved = client.get("/api/layout/resolved").json()
    assert resolved["boxes"][0]["kind"] == "other" and len(resolved["record_boxes"]) == 24
    bad = dict(
        cfg,
        strips=cfg["strips"]
        + [{"id": "dup", "controller": "wled-b", "count": 5, "boxes": [[0, 0]]}],
    )
    assert client.put("/api/layout", json=bad).status_code == 422
    assert client.post("/api/layout/validate", json=bad).json()["ok"] is False


def test_websocket_hello(client):
    with client.websocket_connect("/ws") as ws:
        msg = ws.receive_json()
        assert msg["type"] == "hello" and msg["layout"]["total_pixels"] == 500
