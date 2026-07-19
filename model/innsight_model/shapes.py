"""Plan-shape catalog: room distribution + labelled estimate modifiers.

Mirrors web/lib/building-shape.ts. GFA remains rooms × sqft; shapes only
redistribute rooms and apply estimate multipliers (facade / circulation /
embodied).
"""

from __future__ import annotations

import math
from typing import Literal

ShapeId = Literal["slab", "l_wing", "courtyard", "podium_tower"]

SHAPE_IDS: tuple[ShapeId, ...] = (
    "slab",
    "l_wing",
    "courtyard",
    "podium_tower",
)

# Relative to slab=1.0. All estimates — not metered envelope physics.
SHAPE_MODIFIERS: dict[str, dict[str, float]] = {
    "slab": {"facade_area": 1.0, "circulation": 1.0, "embodied": 1.0},
    "l_wing": {"facade_area": 1.08, "circulation": 1.04, "embodied": 1.03},
    "courtyard": {"facade_area": 1.18, "circulation": 1.12, "embodied": 1.06},
    "podium_tower": {"facade_area": 1.12, "circulation": 1.08, "embodied": 1.05},
}


def normalize_shape(shape: str | None) -> str:
    if shape in SHAPE_MODIFIERS:
        return shape
    return "slab"


def modifiers_for(shape: str | None) -> dict[str, float]:
    return dict(SHAPE_MODIFIERS[normalize_shape(shape)])


def distribute_rooms(rooms: int, storeys: int, shape: str | None = "slab") -> list[int]:
    """Integer rooms per storey; sum equals rooms."""
    n = max(1, int(storeys))
    rooms = max(0, int(rooms))
    sid = normalize_shape(shape)

    if sid == "slab" or sid == "courtyard":
        return _even(rooms, n)
    if sid == "l_wing":
        return _weighted(
            rooms,
            n,
            lambda level: 1.15 - (level / max(1, n - 1)) * 0.35,
        )
    # podium_tower
    podium_end = max(1, math.ceil(n * 0.4))

    def weight(level: int) -> float:
        return 1.45 if level < podium_end else 0.75

    return _weighted(rooms, n, weight)


def _even(rooms: int, n: int) -> list[int]:
    base = rooms // n
    rem = rooms - base * n
    out: list[int] = []
    for _ in range(n):
        extra = 1 if rem > 0 else 0
        if rem > 0:
            rem -= 1
        out.append(base + extra)
    return out


def _weighted(rooms: int, n: int, weight_at) -> list[int]:
    if rooms <= 0:
        return [0] * n
    raw = [float(weight_at(i)) for i in range(n)]
    sum_w = sum(raw) or 1.0
    ideal = [rooms * w / sum_w for w in raw]
    floors = [int(x) for x in ideal]
    rem = rooms - sum(floors)
    order = sorted(
        range(n),
        key=lambda i: ideal[i] - floors[i],
        reverse=True,
    )
    k = 0
    while rem > 0:
        floors[order[k % n]] += 1
        rem -= 1
        k += 1
    return floors
