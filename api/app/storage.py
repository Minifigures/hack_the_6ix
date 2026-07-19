"""MongoDB Atlas persistence for memo / briefing runs.

Stores run metadata plus a reopenable `report` blob (memo / briefs / matrix)
so Past runs can restore the stress + memo UI. Exact `fingerprint` keys let
/briefing and /briefing/year reuse a prior report (skip Gemini) when the same
pin + A/B config already ran. Never stores Stay22 listing data. Degrades to a
no-op when MONGODB_URI is absent so the core loop never depends on the
database. The summary endpoint is an aggregation pipeline, per the Atlas
track's preference for Atlas-native features.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, HTTPException, Query

from app.mongo import collection

router = APIRouter()

HONESTY_NOTE = (
    "sim deterministic; LLM narrative over computed figures; "
    "no Stay22 listings stored"
)

# ~11 m at the equator — same parcel for cache hits, not city-wide.
COORD_DECIMALS = 4
_INDEXES_READY = False

CACHE_NOTE = (
    "Reused prior Mongo run with matching fingerprint "
    "(site + building config); Gemini agents not re-invoked"
)


def _runs_collection() -> Any | None:
    return collection("memo_runs")


def run_fingerprint(
    *,
    kind: str,
    building_type: str,
    rooms: int,
    structure_a: str,
    hvac_a: str,
    structure_b: str,
    hvac_b: str,
    lat: float | None = None,
    lng: float | None = None,
    scenario: str | None = None,
    storeys: int | None = None,
    shape: str | None = None,
) -> str:
    """Stable key for identical stress/agent inputs (not semantic similarity)."""
    from app.agents.gather import DEFAULT_SITE_LAT, DEFAULT_SITE_LNG

    lat_r = round(DEFAULT_SITE_LAT if lat is None else float(lat), COORD_DECIMALS)
    lng_r = round(DEFAULT_SITE_LNG if lng is None else float(lng), COORD_DECIMALS)
    parts = [
        kind,
        building_type,
        str(int(rooms)),
        structure_a,
        hvac_a,
        structure_b,
        hvac_b,
        f"{lat_r:.{COORD_DECIMALS}f}",
        f"{lng_r:.{COORD_DECIMALS}f}",
        scenario or "",
        "" if storeys is None else str(int(storeys)),
        shape or "slab",
    ]
    raw = "|".join(parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]


def ensure_run_indexes() -> None:
    """Idempotent indexes for past-runs list + fingerprint cache lookup."""
    global _INDEXES_READY
    if _INDEXES_READY:
        return
    coll = _runs_collection()
    if coll is None:
        return
    try:
        coll.create_index([("fingerprint", 1), ("auth0_sub", 1), ("ts", -1)])
        coll.create_index([("auth0_sub", 1), ("ts", -1)])
        _INDEXES_READY = True
    except Exception:
        pass


def find_cached_run(
    fingerprint: str,
    *,
    auth0_sub: str | None = None,
) -> dict[str, Any] | None:
    """Latest run with this fingerprint and a reopenable report blob.

    Scoped by auth0_sub when signed in; anonymous requests only reuse
    anonymous runs (auth0_sub null/missing) so signed-in reports stay private.
    """
    coll = _runs_collection()
    if coll is None:
        return None
    ensure_run_indexes()
    query: dict[str, Any] = {
        "fingerprint": fingerprint,
        "report.kind": {"$exists": True},
    }
    if auth0_sub:
        query["auth0_sub"] = auth0_sub
    else:
        query["auth0_sub"] = None
    try:
        return coll.find_one(query, sort=[("ts", -1)])
    except Exception:
        return None


def cached_payload_from_doc(doc: dict[str, Any]) -> dict[str, Any] | None:
    """Rebuild a briefing / year-pack API body from a stored report."""
    report = doc.get("report")
    if not isinstance(report, dict) or not report.get("kind"):
        return None
    kind = report["kind"]
    base = {
        "from_cache": True,
        "cached_run_id": str(doc.get("_id")),
        "cache_note": CACHE_NOTE,
        "fingerprint": doc.get("fingerprint"),
    }
    if kind == "year_pack":
        return {
            **base,
            "scenarios": report.get("scenarios") or {},
            "matrix_summary": report.get("matrix_summary") or {},
            "briefs": report.get("briefs") or {},
            "synthesis": report.get("synthesis") or {},
            "memo": report.get("memo") or {},
            "generator": report.get("generator") or doc.get("briefing_generator") or "cached",
            "fallback_reason": report.get("fallback_reason")
            or doc.get("briefing_fallback_reason"),
            "comparison": report.get("comparison") or {},
            "climate": report.get("climate"),
            "ai_energy": report.get("ai_energy"),
        }
    if kind == "briefing":
        return {
            **base,
            "comparison": report.get("comparison") or {},
            "briefs": report.get("briefs") or {},
            "synthesis": report.get("synthesis") or {},
            "generator": report.get("generator") or doc.get("briefing_generator") or "cached",
            "fallback_reason": report.get("fallback_reason")
            or doc.get("briefing_fallback_reason"),
            "ai_energy": report.get("ai_energy"),
        }
    return None


def _list_item(doc: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(doc.get("_id")),
        "ts": doc.get("ts").isoformat()
        if hasattr(doc.get("ts"), "isoformat")
        else doc.get("ts"),
        "scenario": doc.get("scenario"),
        "building_type": doc.get("building_type"),
        "rooms": doc.get("rooms"),
        "structure_a": doc.get("structure_a"),
        "hvac_a": doc.get("hvac_a"),
        "structure_b": doc.get("structure_b"),
        "hvac_b": doc.get("hvac_b"),
        "recommended": doc.get("recommended"),
        "abatement_cost": doc.get("abatement_cost"),
        "tco2e_delta": doc.get("tco2e_delta"),
        "capex_delta": doc.get("capex_delta"),
        "narrative_generator": doc.get("narrative_generator"),
        "fallback_reason": doc.get("fallback_reason"),
        "briefing_generator": doc.get("briefing_generator"),
        "briefing_fallback_reason": doc.get("briefing_fallback_reason"),
        "agent_source_statuses": doc.get("agent_source_statuses") or [],
        "honesty_note": doc.get("honesty_note") or HONESTY_NOTE,
        "kind": doc.get("kind") or "memo",
        "has_report": isinstance(doc.get("report"), dict) and bool(doc.get("report")),
        "flip_scenarios": doc.get("flip_scenarios") or [],
        "worst_peak_scenario": doc.get("worst_peak_scenario"),
        "fingerprint": doc.get("fingerprint"),
    }


def _site_point(lat: float | None, lng: float | None) -> dict[str, Any] | None:
    if lat is None or lng is None:
        return None
    return {
        "type": "Point",
        "coordinates": [float(lng), float(lat)],
    }


def record_run(
    memo: dict[str, Any],
    *,
    auth0_sub: str | None = None,
    briefing_generator: str | None = None,
    briefing_fallback_reason: str | None = None,
    agent_source_statuses: list[str] | None = None,
    structure_a: str | None = None,
    hvac_a: str | None = None,
    structure_b: str | None = None,
    hvac_b: str | None = None,
    report: dict[str, Any] | None = None,
    lat: float | None = None,
    lng: float | None = None,
    storeys: int | None = None,
    shape: str | None = None,
) -> None:
    coll = _runs_collection()
    if coll is None:
        return
    try:
        ensure_run_indexes()
        options = memo["options"]
        sa = structure_a or options[0].get("structure")
        ha = hvac_a or options[0].get("hvac")
        sb = structure_b or (
            options[1].get("structure") if len(options) > 1 else None
        )
        hb = hvac_b or (options[1].get("hvac") if len(options) > 1 else None)
        bt = options[0]["building_type"]
        rooms = options[0]["rooms"]
        scenario = memo["scenario"]
        fp = run_fingerprint(
            kind="memo",
            building_type=bt,
            rooms=rooms,
            structure_a=sa or "concrete",
            hvac_a=ha or "central_gas",
            structure_b=sb or "mass_timber",
            hvac_b=hb or "heat_pump",
            lat=lat,
            lng=lng,
            scenario=scenario,
            storeys=storeys,
            shape=shape,
        )
        doc: dict[str, Any] = {
            "ts": datetime.now(timezone.utc),
            "scenario": scenario,
            "building_type": bt,
            "rooms": rooms,
            "structure_a": sa,
            "hvac_a": ha,
            "structure_b": sb,
            "hvac_b": hb,
            "recommended": memo["comparison"]["recommended"],
            "abatement_cost": memo["comparison"]["abatement_cost"],
            "tco2e_delta": memo["comparison"]["tco2e_delta"],
            "capex_delta": memo["comparison"]["capex_delta"],
            "narrative_generator": memo.get("narrative", {}).get("generator"),
            "fallback_reason": memo.get("narrative", {}).get("fallback_reason"),
            "briefing_generator": briefing_generator,
            "briefing_fallback_reason": briefing_fallback_reason,
            "agent_source_statuses": agent_source_statuses or [],
            "honesty_note": HONESTY_NOTE,
            "kind": "memo",
            "fingerprint": fp,
            "storeys": storeys,
            "shape": shape or "slab",
        }
        point = _site_point(lat, lng)
        if point:
            doc["location"] = point
            doc["lat"] = lat
            doc["lng"] = lng
        if report:
            doc["report"] = report
        doc["auth0_sub"] = auth0_sub
        coll.insert_one(doc)
    except Exception:
        pass  # persistence must never break the demo path


def record_briefing_run(
    *,
    comparison: dict[str, Any],
    generator: str,
    fallback_reason: str | None,
    briefs: dict[str, Any],
    auth0_sub: str | None = None,
    report: dict[str, Any] | None = None,
    lat: float | None = None,
    lng: float | None = None,
    storeys: int | None = None,
    shape: str | None = None,
    scenario: str | None = None,
    structure_a: str | None = None,
    hvac_a: str | None = None,
    structure_b: str | None = None,
    hvac_b: str | None = None,
    building_type: str | None = None,
    rooms: int | None = None,
) -> None:
    """Persist a briefing-only summary when memo is not yet available."""
    coll = _runs_collection()
    if coll is None:
        return
    try:
        ensure_run_indexes()
        option_a = comparison.get("option_a") or {}
        option_b = comparison.get("option_b") or {}
        cfg_a = option_a.get("config") or {}
        cfg_b = option_b.get("config") or {}
        statuses: list[str] = []
        for brief in briefs.values():
            sources = brief.get("sources") if isinstance(brief, dict) else []
            for src in sources or []:
                status = src.get("status") if isinstance(src, dict) else None
                if status:
                    statuses.append(str(status))
        sa = structure_a or cfg_a.get("structure") or "concrete"
        ha = hvac_a or cfg_a.get("hvac") or "central_gas"
        sb = structure_b or cfg_b.get("structure") or "mass_timber"
        hb = hvac_b or cfg_b.get("hvac") or "heat_pump"
        bt = building_type or cfg_a.get("building_type") or "boutique"
        rm = int(rooms if rooms is not None else cfg_a.get("rooms") or 0)
        scen = scenario or comparison.get("scenario_name") or "heatwave_full"
        fp = run_fingerprint(
            kind="briefing",
            building_type=bt,
            rooms=rm,
            structure_a=sa,
            hvac_a=ha,
            structure_b=sb,
            hvac_b=hb,
            lat=lat,
            lng=lng,
            scenario=scen,
            storeys=storeys,
            shape=shape,
        )
        doc: dict[str, Any] = {
            "ts": datetime.now(timezone.utc),
            "scenario": scen,
            "building_type": bt,
            "rooms": rm,
            "structure_a": sa,
            "hvac_a": ha,
            "structure_b": sb,
            "hvac_b": hb,
            "recommended": comparison.get("recommended"),
            "abatement_cost": comparison.get("abatement_cost"),
            "tco2e_delta": comparison.get("tco2e_delta"),
            "capex_delta": comparison.get("capex_delta"),
            "briefing_generator": generator,
            "briefing_fallback_reason": fallback_reason,
            "agent_source_statuses": sorted(set(statuses)),
            "honesty_note": HONESTY_NOTE,
            "kind": "briefing",
            "fingerprint": fp,
            "storeys": storeys,
            "shape": shape or "slab",
        }
        point = _site_point(lat, lng)
        if point:
            doc["location"] = point
            doc["lat"] = lat
            doc["lng"] = lng
        if report:
            doc["report"] = report
        doc["auth0_sub"] = auth0_sub
        coll.insert_one(doc)
    except Exception:
        pass


def record_year_pack_run(
    *,
    memo: dict[str, Any],
    matrix_summary: dict[str, Any],
    generator: str,
    fallback_reason: str | None,
    briefs: dict[str, Any],
    auth0_sub: str | None = None,
    structure_a: str | None = None,
    hvac_a: str | None = None,
    structure_b: str | None = None,
    hvac_b: str | None = None,
    report: dict[str, Any] | None = None,
    lat: float | None = None,
    lng: float | None = None,
    storeys: int | None = None,
    shape: str | None = None,
    building_type: str | None = None,
    rooms: int | None = None,
) -> None:
    """Persist year-pack summary + reopenable report (kind=year_pack)."""
    coll = _runs_collection()
    if coll is None:
        return
    try:
        ensure_run_indexes()
        options = memo.get("options") or []
        statuses: list[str] = []
        for brief in briefs.values():
            sources = brief.get("sources") if isinstance(brief, dict) else []
            for src in sources or []:
                status = src.get("status") if isinstance(src, dict) else None
                if status:
                    statuses.append(str(status))
        comparison = memo.get("comparison") or {}
        sa = structure_a or (options[0].get("structure") if options else None) or "concrete"
        ha = hvac_a or (options[0].get("hvac") if options else None) or "central_gas"
        sb = (
            structure_b
            or (options[1].get("structure") if len(options) > 1 else None)
            or "mass_timber"
        )
        hb = (
            hvac_b
            or (options[1].get("hvac") if len(options) > 1 else None)
            or "heat_pump"
        )
        bt = building_type or (
            options[0].get("building_type") if options else None
        ) or "boutique"
        rm = int(
            rooms
            if rooms is not None
            else (options[0].get("rooms") if options else 0) or 0
        )
        fp = run_fingerprint(
            kind="year_pack",
            building_type=bt,
            rooms=rm,
            structure_a=sa,
            hvac_a=ha,
            structure_b=sb,
            hvac_b=hb,
            lat=lat,
            lng=lng,
            scenario=None,
            storeys=storeys,
            shape=shape,
        )
        doc: dict[str, Any] = {
            "ts": datetime.now(timezone.utc),
            "scenario": memo.get("scenario") or "Year pack (5 extreme weekends)",
            "building_type": bt,
            "rooms": rm,
            "structure_a": sa,
            "hvac_a": ha,
            "structure_b": sb,
            "hvac_b": hb,
            "recommended": comparison.get("recommended")
            or matrix_summary.get("baseline_recommended"),
            "abatement_cost": comparison.get("abatement_cost"),
            "tco2e_delta": comparison.get("tco2e_delta"),
            "capex_delta": comparison.get("capex_delta"),
            "narrative_generator": (memo.get("narrative") or {}).get("generator"),
            "fallback_reason": (memo.get("narrative") or {}).get("fallback_reason")
            or fallback_reason,
            "briefing_generator": generator,
            "briefing_fallback_reason": fallback_reason,
            "agent_source_statuses": sorted(set(statuses)),
            "honesty_note": HONESTY_NOTE,
            "kind": "year_pack",
            "flip_scenarios": matrix_summary.get("flip_scenarios") or [],
            "worst_peak_scenario": matrix_summary.get("worst_peak_scenario"),
            "fingerprint": fp,
            "storeys": storeys,
            "shape": shape or "slab",
        }
        point = _site_point(lat, lng)
        if point:
            doc["location"] = point
            doc["lat"] = lat
            doc["lng"] = lng
        if report:
            doc["report"] = report
        doc["auth0_sub"] = auth0_sub
        coll.insert_one(doc)
    except Exception:
        pass


@router.get("/runs/summary")
def runs_summary() -> dict[str, Any]:
    coll = _runs_collection()
    if coll is None:
        return {"available": False, "note": "MONGODB_URI not configured"}
    pipeline = [
        {
            "$group": {
                "_id": {
                    "building_type": "$building_type",
                    "recommended": "$recommended",
                },
                "runs": {"$sum": 1},
                "avg_abatement": {"$avg": "$abatement_cost"},
                "avg_tco2e_saved": {"$avg": "$tco2e_delta"},
            }
        },
        {"$sort": {"runs": -1}},
    ]
    rows = [
        {
            "building_type": r["_id"]["building_type"],
            "recommended": r["_id"]["recommended"],
            "runs": r["runs"],
            "avg_abatement": r["avg_abatement"],
            "avg_tco2e_saved": r["avg_tco2e_saved"],
        }
        for r in coll.aggregate(pipeline)
    ]
    return {"available": True, "by_config": rows}


@router.get("/runs/mine")
def runs_mine(
    auth0_sub: str = Query(min_length=3),
    limit: int = Query(default=20, ge=1, le=50),
) -> dict[str, Any]:
    """List recent runs for a signed-in user.

    v1 trusts the client-provided auth0_sub (Auth0 UI gate). Production should
    verify the Auth0 JWT server-side before relying on this endpoint.
    """
    coll = _runs_collection()
    if coll is None:
        return {"available": False, "runs": [], "note": "MONGODB_URI not configured"}
    try:
        cursor = (
            coll.find({"auth0_sub": auth0_sub})
            .sort("ts", -1)
            .limit(limit)
        )
        runs = [_list_item(doc) for doc in cursor]
        return {"available": True, "runs": runs}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"runs query failed: {exc}") from exc


@router.get("/runs/{run_id}")
def run_detail(
    run_id: str,
    auth0_sub: str = Query(min_length=3),
) -> dict[str, Any]:
    """Return one run with its reopenable report blob (if stored).

    Scoped by auth0_sub (same trust model as /runs/mine). Older metadata-only
    runs return has_report=false and report=null.
    """
    coll = _runs_collection()
    if coll is None:
        raise HTTPException(status_code=503, detail="MONGODB_URI not configured")
    try:
        oid = ObjectId(run_id)
    except InvalidId as exc:
        raise HTTPException(status_code=400, detail="invalid run id") from exc
    try:
        doc = coll.find_one({"_id": oid, "auth0_sub": auth0_sub})
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"runs query failed: {exc}") from exc
    if doc is None:
        raise HTTPException(status_code=404, detail="run not found")
    item = _list_item(doc)
    report = doc.get("report") if isinstance(doc.get("report"), dict) else None
    return {**item, "report": report}
