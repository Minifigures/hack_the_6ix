"""Fingerprint cache keys + payload rebuild (no Mongo required)."""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

API_ROOT = Path(__file__).resolve().parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.storage import (
    CACHE_NOTE,
    cached_payload_from_doc,
    run_fingerprint,
)


def _base_kwargs() -> dict:
    return {
        "kind": "year_pack",
        "building_type": "boutique",
        "rooms": 40,
        "structure_a": "concrete",
        "hvac_a": "central_gas",
        "structure_b": "mass_timber",
        "hvac_b": "heat_pump",
        "lat": 43.6476,
        "lng": -79.3742,
        "storeys": 4,
        "shape": "slab",
    }


def test_fingerprint_stable_for_same_inputs() -> None:
    a = run_fingerprint(**_base_kwargs())
    b = run_fingerprint(**_base_kwargs())
    assert a == b
    assert len(a) == 32


def test_fingerprint_rounds_coords() -> None:
    base = _base_kwargs()
    near = {**base, "lat": 43.64761, "lng": -79.37421}
    far = {**base, "lat": 43.6486, "lng": -79.3742}
    assert run_fingerprint(**base) == run_fingerprint(**near)
    assert run_fingerprint(**base) != run_fingerprint(**far)


def test_fingerprint_changes_with_config() -> None:
    base = _base_kwargs()
    other = {**base, "rooms": 80}
    assert run_fingerprint(**base) != run_fingerprint(**other)
    assert run_fingerprint(**base) != run_fingerprint(
        **{**base, "kind": "briefing", "scenario": "heatwave_full"}
    )


def test_cached_payload_from_year_pack_doc() -> None:
    doc = {
        "_id": "abc123",
        "fingerprint": "deadbeef",
        "briefing_generator": "gemini",
        "report": {
            "kind": "year_pack",
            "scenarios": {"heatwave_full": {"recommended": "B"}},
            "matrix_summary": {"flip_scenarios": []},
            "briefs": {"market": {"title": "Market"}},
            "synthesis": {"summary": "ok"},
            "memo": {"scenario": "Year pack"},
            "generator": "gemini",
            "fallback_reason": None,
            "comparison": {"recommended": "B"},
            "climate": {"source": "open-meteo"},
            "ai_energy": {"call_count": 0},
        },
    }
    payload = cached_payload_from_doc(doc)
    assert payload is not None
    assert payload["from_cache"] is True
    assert payload["cached_run_id"] == "abc123"
    assert payload["cache_note"] == CACHE_NOTE
    assert payload["comparison"]["recommended"] == "B"
    assert payload["climate"]["source"] == "open-meteo"
    assert payload["generator"] == "gemini"


def test_list_item_includes_fingerprint() -> None:
    from app.storage import _list_item

    ts = datetime(2026, 7, 18, 12, 0, tzinfo=timezone.utc)
    item = _list_item(
        {
            "_id": "abc",
            "ts": ts,
            "scenario": "Year pack",
            "building_type": "boutique",
            "rooms": 40,
            "recommended": "B",
            "kind": "year_pack",
            "fingerprint": "abc",
            "report": {"kind": "year_pack"},
        }
    )
    assert item["fingerprint"] == "abc"
    assert item["has_report"] is True
