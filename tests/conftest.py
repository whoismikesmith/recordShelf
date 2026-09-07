from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from recordshelf.db import Database
from recordshelf.discogs import parse_item
from recordshelf.layout import EXAMPLE_YAML, ResolvedLayout
from recordshelf.models import LayoutConfig


def item(
    iid: int,
    artist: str,
    title: str,
    year: int | None = None,
    genres=(),
    styles=(),
    descriptions=("LP",),
    label="Some Label",
    added="2020-01-01T00:00:00-08:00",
    rating=0,
    folder=1,
):
    return {
        "id": iid * 10,
        "instance_id": iid,
        "folder_id": folder,
        "rating": rating,
        "date_added": added,
        "basic_information": {
            "id": iid * 10,
            "master_id": iid * 100,
            "title": title,
            "year": year or 0,
            "thumb": "",
            "cover_image": "",
            "artists": [{"name": artist, "join": ""}],
            "labels": [{"name": label, "catno": f"CAT{iid}"}],
            "formats": [{"name": "Vinyl", "qty": "1", "descriptions": list(descriptions)}],
            "genres": list(genres),
            "styles": list(styles),
        },
    }


SAMPLE = [
    item(1, "The Beatles", "Abbey Road", 1969, ["Rock"], ["Pop Rock"]),
    item(2, "Miles Davis", "Kind of Blue", 1959, ["Jazz"], ["Modal"]),
    item(3, "Aphex Twin", "Selected Ambient Works 85-92", 1992, ["Electronic"], ["Ambient", "IDM"]),
    item(
        4,
        "Various",
        "Now That's What I Call Music",
        1990,
        ["Pop"],
        [],
        descriptions=["LP", "Compilation"],
    ),
    item(5, "Bush (2)", "Sixteen Stone", 1994, ["Rock"], ["Grunge"]),
    item(6, "Nirvana", "Nevermind", 1991, ["Rock"], ["Grunge"]),
    item(7, "John Coltrane", "A Love Supreme", 1965, ["Jazz"], ["Free Jazz"]),
    item(8, "Boards of Canada", "Music Has the Right to Children", 1998, ["Electronic"], ["IDM"]),
    item(
        9, "Radiohead", "Creep", 1992, ["Rock"], ["Alternative Rock"], descriptions=['7"', "Single"]
    ),
    item(10, "A Tribe Called Quest", "The Low End Theory", 1991, ["Hip Hop"], ["Jazzy Hip-Hop"]),
]


@pytest.fixture
def layout_cfg() -> LayoutConfig:
    return LayoutConfig.model_validate(yaml.safe_load(EXAMPLE_YAML))


@pytest.fixture
def layout(layout_cfg) -> ResolvedLayout:
    return ResolvedLayout(layout_cfg)


@pytest.fixture
def db() -> Database:
    d = Database(":memory:")
    d.replace_collection(parse_item(i) for i in SAMPLE)
    return d


@pytest.fixture
def layout_file(tmp_path: Path) -> Path:
    p = tmp_path / "shelf.yaml"
    p.write_text(EXAMPLE_YAML)
    return p
