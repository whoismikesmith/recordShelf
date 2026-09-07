import json

import httpx
import pytest

from recordshelf.db import Database
from recordshelf.discogs import DiscogsClient, DiscogsError, SyncManager
from tests.conftest import SAMPLE, item


def make_client(handler, token="t") -> DiscogsClient:
    transport = httpx.MockTransport(handler)
    http = httpx.AsyncClient(base_url="https://api.discogs.com", transport=transport)
    c = DiscogsClient("tester", token, "test-agent", client=http)
    c._min_interval = 0
    return c


def paged(items, per_page):
    pages = max(1, -(-len(items) // per_page))

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["User-Agent"] == "test-agent"
        assert request.headers["Authorization"] == "Discogs token=t"
        page = int(request.url.params.get("page", "1"))
        chunk = items[(page - 1) * per_page : page * per_page]
        body = {
            "pagination": {"page": page, "pages": pages, "per_page": per_page, "items": len(items)},
            "releases": chunk,
        }
        return httpx.Response(200, json=body)

    return handler


async def test_sync_paginates_and_reports(tmp_path):
    db = Database(":memory:")
    statuses = []
    mgr = SyncManager(
        db,
        lambda: make_client(paged(SAMPLE, 4)),
        on_change=lambda st: statuses.append(st.model_copy()),
    )
    assert mgr.start() is True
    assert mgr.start() is False  # already running
    status = await mgr.wait()
    assert status.state == "done"
    assert (status.added, status.updated, status.removed) == (10, 0, 0)
    assert status.pages == 3 and status.fetched == 10
    assert db.get_meta("last_sync") == status.last_sync
    assert len(db.list_releases()) == 10
    assert statuses[0].state == "running" and statuses[-1].state == "done"

    # second sync: one record gone, one changed title, one new
    changed = [i for i in SAMPLE if i["instance_id"] != 3]
    changed[0] = json.loads(json.dumps(changed[0]))
    changed[0]["basic_information"]["title"] = "Abbey Road (Remaster)"
    changed.append(item(11, "Portishead", "Dummy", 1994, ["Electronic"], ["Trip Hop"]))
    db.set_order([1, 2, 3, 4])
    mgr = SyncManager(db, lambda: make_client(paged(changed, 100)))
    mgr.start()
    status = await mgr.wait()
    assert (status.added, status.updated, status.removed) == (1, 9, 1)
    assert db.get_release(1).title == "Abbey Road (Remaster)"
    assert db.get_release(3) is None
    assert db.get_order() == [1, 2, 4]  # removed record dropped from the shelf order too


async def test_rate_limit_retry_then_success():
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] == 1:
            return httpx.Response(429, headers={"Retry-After": "0"}, json={"message": "slow down"})
        return paged(SAMPLE[:2], 100)(request)

    c = make_client(handler)
    pages = [p async for p in c.collection_pages()]
    await c.aclose()
    assert calls["n"] == 2 and len(pages) == 1 and len(pages[0][2]) == 2


async def test_api_error_surfaces_message():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"message": "User does not exist"})

    db = Database(":memory:")
    mgr = SyncManager(db, lambda: make_client(handler))
    mgr.start()
    status = await mgr.wait()
    assert status.state == "error" and "User does not exist" in status.error
    assert db.list_releases() == []


def test_missing_username_is_an_error():
    with pytest.raises(DiscogsError):
        DiscogsClient("", "")
