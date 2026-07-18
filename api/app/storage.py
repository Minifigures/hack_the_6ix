"""MongoDB Atlas persistence for memo runs.

Stores run metadata only (config, results, recommendation), never Stay22
listing data. Degrades to a no-op when MONGODB_URI is absent so the core loop
never depends on the database. The summary endpoint is an aggregation
pipeline, per the Atlas track's preference for Atlas-native features.
"""

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter

from app.mongo import collection

router = APIRouter()


def _runs_collection() -> Any | None:
    return collection("memo_runs")


def record_run(memo: dict[str, Any]) -> None:
    coll = _runs_collection()
    if coll is None:
        return
    try:
        options = memo["options"]
        coll.insert_one(
            {
                "ts": datetime.now(timezone.utc),
                "scenario": memo["scenario"],
                "building_type": options[0]["building_type"],
                "rooms": options[0]["rooms"],
                "recommended": memo["comparison"]["recommended"],
                "abatement_cost": memo["comparison"]["abatement_cost"],
                "tco2e_delta": memo["comparison"]["tco2e_delta"],
                "capex_delta": memo["comparison"]["capex_delta"],
                "narrative_generator": memo["narrative"]["generator"],
            }
        )
    except Exception:
        pass  # persistence must never break the demo path


@router.get("/runs/summary")
def runs_summary() -> dict[str, Any]:
    coll = _runs_collection()
    if coll is None:
        return {"available": False, "note": "MONGODB_URI not configured"}
    pipeline = [
        {
            "$group": {
                "_id": {"building_type": "$building_type", "recommended": "$recommended"},
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
