"""Plan-shape distribute + estimate modifiers."""

from __future__ import annotations

from innsight_model.shapes import distribute_rooms, modifiers_for
from innsight_model.sim import SCENARIOS, BuildingConfig, compare, run_option


def test_distribute_sums_to_rooms() -> None:
    for shape in ("slab", "l_wing", "courtyard", "podium_tower"):
        for rooms, storeys in ((40, 8), (52, 7), (6, 3), (11, 4)):
            dist = distribute_rooms(rooms, storeys, shape)
            assert len(dist) == storeys
            assert sum(dist) == rooms
            assert all(n >= 0 for n in dist)


def test_courtyard_raises_ops_vs_slab() -> None:
    cfg = BuildingConfig("boutique", 40, "concrete", "central_gas", "A")
    scenario = SCENARIOS["heatwave_full"]
    slab = run_option(cfg, scenario, shape="slab", storeys=8)
    court = run_option(cfg, scenario, shape="courtyard", storeys=8)
    assert court.annual_operating_cost > slab.annual_operating_cost
    assert court.peak_kw > slab.peak_kw
    assert court.shape_modifiers["circulation"] == modifiers_for("courtyard")[
        "circulation"
    ]
    assert court.notes  # estimate disclosure
    assert sum(court.rooms_per_storey) == 40


def test_compare_accepts_shape() -> None:
    a = BuildingConfig("boutique", 40, "concrete", "central_gas", "A")
    b = BuildingConfig("boutique", 40, "mass_timber", "heat_pump", "B")
    result = compare(a, b, SCENARIOS["heatwave_full"], shape="podium_tower", storeys=8)
    assert result.option_a.shape == "podium_tower"
    assert result.option_b.storeys == 8
