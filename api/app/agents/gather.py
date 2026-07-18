"""Data gatherers for multi-agent briefing (Stay22, env, packs, sim context)."""

from __future__ import annotations

import json
import os
import statistics
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import httpx
from innsight_model import benchmarks as B
from innsight_model.friction import friction_score, friction_terms
from innsight_model.sim import Comparison, OptionResult

PACKS_DIR = Path(__file__).resolve().parent / "packs"

SITE_LAT = 43.6476
SITE_LNG = -79.3744
STAY22_BASE = "https://api.stay22.com/v2/accommodations"

# In-process cache only (Stay22 terms: no disk / DB listing storage).
_last_stay22: dict[str, Any] | None = None


def _next_saturday() -> date:
    today = date.today()
    return today + timedelta(days=(5 - today.weekday()) % 7 or 7)


async def _stay22_search(
    client: httpx.AsyncClient, checkin: date, checkout: date
) -> dict[str, Any]:
    response = await client.get(
        STAY22_BASE,
        params={
            "lat": SITE_LAT,
            "lng": SITE_LNG,
            "radius": 3000,
            "checkin": checkin.isoformat(),
            "checkout": checkout.isoformat(),
            "adults": 2,
            "currency": "CAD",
            "pageSize": 20,
        },
        timeout=8.0,
    )
    response.raise_for_status()
    return response.json()


def _summarize_stay22(payload: dict[str, Any]) -> dict[str, Any]:
    results = payload.get("results") or []
    prices: list[float] = []
    for item in results:
        supplier_prices = [
            s["price"]["total"]
            for s in (item.get("suppliers") or {}).values()
            if isinstance(s, dict) and (s.get("price") or {}).get("total")
        ]
        if supplier_prices:
            prices.append(min(supplier_prices))
    return {
        "properties": len(results),
        "priced": len(prices),
        "median_rate": round(statistics.median(prices), 0) if prices else None,
        "min_rate": round(min(prices), 0) if prices else None,
    }


async def fetch_stay22_market(checkin: str | None = None) -> dict[str, Any]:
    """Shared Stay22 pull used by /stay22/market and the briefing gatherer."""
    global _last_stay22

    target_in = date.fromisoformat(checkin) if checkin else _next_saturday()
    target_out = target_in + timedelta(days=1)
    baseline_in = target_in + timedelta(days=28)
    baseline_out = baseline_in + timedelta(days=1)

    try:
        async with httpx.AsyncClient() as client:
            target_raw = await _stay22_search(client, target_in, target_out)
            baseline_raw = await _stay22_search(client, baseline_in, baseline_out)
        target = _summarize_stay22(target_raw)
        baseline = _summarize_stay22(baseline_raw)
        demand_ratio = (
            round(target["median_rate"] / baseline["median_rate"], 3)
            if target["median_rate"] and baseline["median_rate"]
            else None
        )
        result = {
            "source": "live",
            "checkin": target_in.isoformat(),
            "baseline_checkin": baseline_in.isoformat(),
            "target": target,
            "baseline": baseline,
            "demand_ratio": demand_ratio,
            "note": "Live Stay22 demo-mode pull, 3 km around 45 The Esplanade. "
            "No listings are stored.",
        }
        _last_stay22 = result
        return result
    except Exception as exc:
        if _last_stay22 is not None:
            return {
                **_last_stay22,
                "source": "cached",
                "note": (
                    "Live pull failed; serving this session's earlier pull. "
                    "Disclosed as cached in the demo."
                ),
                "error": str(exc),
            }
        return {
            "source": "estimate",
            "checkin": target_in.isoformat(),
            "baseline_checkin": baseline_in.isoformat(),
            "target": {
                "properties": 0,
                "priced": 0,
                "median_rate": None,
                "min_rate": None,
            },
            "baseline": {
                "properties": 0,
                "priced": 0,
                "median_rate": None,
                "min_rate": None,
            },
            "demand_ratio": None,
            "note": f"Stay22 unreachable: {exc}",
            "error": str(exc),
        }


def _load_pack(name: str) -> dict[str, Any]:
    path = PACKS_DIR / name
    return json.loads(path.read_text(encoding="utf-8"))


def load_neighborhood_pack() -> dict[str, Any]:
    return _load_pack("neighborhood.json")


def load_compliance_pack() -> dict[str, Any]:
    return _load_pack("compliance.json")


async def fetch_electricity_maps() -> dict[str, Any]:
    """Optional live carbon intensity for Ontario (CA-ON)."""
    key = os.environ.get("ELECTRICITYMAPS_API_KEY") or ""
    if not key:
        return {
            "source": "benchmark",
            "zone": "CA-ON",
            "carbon_intensity": None,
            "note": "No ELECTRICITYMAPS_API_KEY; using TAF Ontario grid benchmarks.",
        }
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.electricitymaps.com/v3/carbon-intensity/latest",
                params={"zone": "CA-ON"},
                headers={"auth-token": key},
                timeout=8.0,
            )
            response.raise_for_status()
            data = response.json()
        intensity = data.get("carbonIntensity")
        return {
            "source": "live",
            "zone": "CA-ON",
            "carbon_intensity": intensity,
            "datetime": data.get("datetime"),
            "note": "Live Electricity Maps carbon intensity for Ontario.",
            "url": "https://www.electricitymaps.com/",
        }
    except Exception as exc:
        return {
            "source": "benchmark",
            "zone": "CA-ON",
            "carbon_intensity": None,
            "note": f"Electricity Maps unreachable ({exc}); using TAF benchmarks.",
        }


def _option_snapshot(result: OptionResult) -> dict[str, Any]:
    config = result.config
    return {
        "label": config.label,
        "building_type": config.building_type,
        "rooms": config.rooms,
        "structure": config.structure,
        "hvac": config.hvac,
        "peak_kw": result.peak_kw,
        "strain_class": result.strain_class,
        "strain_ratio": result.strain_ratio,
        "tco2e_total": result.tco2e_total,
        "tco2e_operational": result.tco2e_operational,
        "tco2e_embodied_amortized": result.tco2e_embodied_amortized,
        "construction_cost": result.construction_cost,
        "annual_operating_cost": result.annual_operating_cost,
        "friction_score": friction_score(config, result),
        "friction_terms": friction_terms(config, result),
    }


def comparison_context(comparison: Comparison) -> dict[str, Any]:
    return {
        "scenario_name": comparison.scenario_name,
        "recommended": comparison.recommended,
        "capex_delta": comparison.capex_delta,
        "annual_cost_delta": comparison.annual_cost_delta,
        "tco2e_delta": comparison.tco2e_delta,
        "abatement_cost": comparison.abatement_cost,
        "abatement_threshold": comparison.abatement_threshold,
        "payback_years": comparison.payback_years,
        "reasoning": list(comparison.reasoning),
        "option_a": _option_snapshot(comparison.option_a),
        "option_b": _option_snapshot(comparison.option_b),
    }


def environment_context(live_grid: dict[str, Any]) -> dict[str, Any]:
    return {
        "heatwave_peak_c": B.HEATWAVE_EVENT_PEAK_C.value,
        "heatwave_source": B.HEATWAVE_EVENT_PEAK_C.source,
        "grid_intensity_avg_g_per_kwh": B.GRID_INTENSITY_AVG.value,
        "grid_intensity_peak_g_per_kwh": B.GRID_INTENSITY_PEAK.value,
        "grid_avg_source": B.GRID_INTENSITY_AVG.source,
        "grid_peak_source": B.GRID_INTENSITY_PEAK.source,
        "live_grid": live_grid,
    }


def green_ratio_context(comparison: Comparison) -> dict[str, Any]:
    """Relative greenness vs a neighborhood hospitality carbon proxy."""
    # Estimate: CBECS hotel elec intensity x ~350 sqft/room x TAF grid avg.
    # Gas omitted on purpose so the proxy stays conservative and labelled.
    avg = B.GRID_INTENSITY_AVG.value  # gCO2e/kWh
    hotel_elec = B.HOTEL_ELEC_INTENSITY.value  # kWh/sqft/yr
    sqft_per_room = 350.0
    life = B.BUILDING_LIFE_YEARS.value
    kwh_per_room = hotel_elec * sqft_per_room
    neighborhood_proxy_tco2e_per_room_yr = round(kwh_per_room * avg / 1_000_000.0, 3)
    a = comparison.option_a
    b = comparison.option_b
    a_per_room = a.tco2e_total / max(a.config.rooms, 1)
    b_per_room = b.tco2e_total / max(b.config.rooms, 1)
    return {
        "neighborhood_proxy_tco2e_per_room_yr": neighborhood_proxy_tco2e_per_room_yr,
        "proxy_status": "estimate",
        "proxy_note": (
            "Neighborhood green ratio uses a CBECS/TAF-derived hospitality "
            "electricity proxy (~350 sqft/room), not metered nearby buildings."
        ),
        "option_a_tco2e_per_room": round(a_per_room, 3),
        "option_b_tco2e_per_room": round(b_per_room, 3),
        "option_a_vs_proxy": round(a_per_room / neighborhood_proxy_tco2e_per_room_yr, 2)
        if neighborhood_proxy_tco2e_per_room_yr
        else None,
        "option_b_vs_proxy": round(b_per_room / neighborhood_proxy_tco2e_per_room_yr, 2)
        if neighborhood_proxy_tco2e_per_room_yr
        else None,
        "building_life_years": life,
        "embodied_a": a.tco2e_embodied_amortized,
        "embodied_b": b.tco2e_embodied_amortized,
    }


async def gather_all(comparison: Comparison) -> dict[str, Any]:
    market, live_grid = await _gather_async()
    return {
        "comparison": comparison_context(comparison),
        "market": market,
        "environment": environment_context(live_grid),
        "neighborhood": load_neighborhood_pack(),
        "compliance": load_compliance_pack(),
        "green_ratio": green_ratio_context(comparison),
        "friction": {
            "formula": "model/friction.md",
            "label": "documented heuristic, not survey data",
            "option_a": {
                "score": friction_score(
                    comparison.option_a.config, comparison.option_a
                ),
                "terms": friction_terms(
                    comparison.option_a.config, comparison.option_a
                ),
            },
            "option_b": {
                "score": friction_score(
                    comparison.option_b.config, comparison.option_b
                ),
                "terms": friction_terms(
                    comparison.option_b.config, comparison.option_b
                ),
            },
        },
    }


async def _gather_async() -> tuple[dict[str, Any], dict[str, Any]]:
    import asyncio

    return await asyncio.gather(fetch_stay22_market(), fetch_electricity_maps())
