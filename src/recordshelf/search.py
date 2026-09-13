"""Text search over releases, plus a best-match picker for voice/hook requests."""

from __future__ import annotations

import unicodedata

from .models import Release


def fold(text: str) -> str:
    """Case- and accent-insensitive form, so 'sigur ros' finds 'Sigur Rós'."""
    decomposed = unicodedata.normalize("NFKD", text.casefold())
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))


def haystack(r: Release) -> str:
    parts = [
        r.artist,
        r.title,
        r.label or "",
        r.catno or "",
        str(r.year or ""),
        *r.genres,
        *r.styles,
    ]
    return fold(" ".join(parts))


def matches(r: Release, q: str) -> bool:
    tokens = fold(q).split()
    if not tokens:
        return True
    hay = haystack(r)
    return all(t in hay for t in tokens)


def score(r: Release, q: str) -> float:
    qf = fold(q).strip()
    if not qf:
        return 0.0
    artist, title = fold(r.artist), fold(r.title)
    s = 0.0
    if qf == title or qf == f"{artist} {title}" or qf == f"{title} {artist}":
        s += 100
    if title.startswith(qf) or artist.startswith(qf):
        s += 20
    for t in qf.split():
        if t in title:
            s += 5
        if t in artist:
            s += 4
        if t in haystack(r):
            s += 1
    return s


def best_match(releases: list[Release], q: str) -> Release | None:
    scored = [(score(r, q), r) for r in releases]
    scored = [(s, r) for s, r in scored if s > 0]
    if not scored:
        return None
    scored.sort(key=lambda t: (-t[0], t[1].artist_sort, t[1].title))
    return scored[0][1]
