"""Spread N records across boxes in proportion to each box's capacity."""

from __future__ import annotations


def distribute(capacities: list[int], total: int) -> list[int]:
    """Return a count per box summing to `total`, proportional to capacity.

    Uses largest-remainder rounding so the sum is exact. A box with capacity 0 gets nothing
    unless every box is 0, in which case the records are split evenly.
    """
    n = len(capacities)
    if n == 0:
        return []
    total = max(0, total)
    weights = [max(0, c) for c in capacities]
    if sum(weights) == 0:
        weights = [1] * n
    wsum = sum(weights)
    raw = [w / wsum * total for w in weights]
    counts = [int(x) for x in raw]
    remainder = total - sum(counts)
    order = sorted(range(n), key=lambda i: raw[i] - counts[i], reverse=True)
    for i in order[:remainder]:
        counts[i] += 1
    return counts


def starts_from_counts(counts: list[int], offset: int = 0) -> list[int]:
    out: list[int] = []
    cursor = offset
    for c in counts:
        out.append(cursor)
        cursor += c
    return out
