"""Stay22 market layer: summary math, pins, calendar scan, fallback chain.

All tests run against fixture payloads or stubbed searches; no live calls.
"""

import asyncio
import sys
from pathlib import Path

API_DIR = Path(__file__).resolve().parents[1]
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

from app.agents import gather


def _listing(
    name: str,
    *,
    prices: list[float] | None = None,
    lat: float | None = 43.65,
    lng: float | None = -79.38,
    stars: int | None = 4,
) -> dict:
    suppliers = {
        f"s{i}": {"price": {"total": p}} for i, p in enumerate(prices or [])
    }
    coords = {"lat": lat, "lng": lng} if lat is not None else {}
    return {
        "name": name,
        "suppliers": suppliers,
        "location": {"coordinates": coords},
        "rating": {"hotelStars": stars},
    }


def test_summarize_prices_and_pins() -> None:
    payload = {
        "results": [
            _listing("Hotel A", prices=[240.0, 199.0]),  # best = min supplier
            _listing("Hotel B", prices=[301.0]),
            _listing("No price", prices=[]),  # pinned, rate None
            _listing("No coords", prices=[150.0], lat=None),  # priced, no pin
        ]
    }
    s = gather._summarize_stay22(payload)
    assert s["properties"] == 4
    assert s["priced"] == 3
    assert s["min_rate"] == 150.0
    assert s["median_rate"] == 199.0
    pins = s["pins"]
    assert [p["name"] for p in pins] == ["Hotel A", "Hotel B", "No price"]
    assert pins[0]["rate"] == 199.0
    assert pins[2]["rate"] is None
    assert pins[0]["stars"] == 4
    assert set(pins[0]) == {"name", "lat", "lng", "rate", "stars"}


def test_summarize_caps_pins_for_map_layer() -> None:
    payload = {
        "results": [_listing(f"H{i}", prices=[100.0 + i]) for i in range(20)]
    }
    s = gather._summarize_stay22(payload)
    assert s["properties"] == 20
    assert len(s["pins"]) == 14


def test_summarize_empty_payload() -> None:
    s = gather._summarize_stay22({})
    assert s["properties"] == 0
    assert s["median_rate"] is None
    assert s["pins"] == []


def test_search_sends_hub_key_header(monkeypatch) -> None:
    seen: dict = {}

    class _Res:
        def raise_for_status(self) -> None:
            pass

        def json(self) -> dict:
            return {"results": []}

    class _Client:
        async def get(self, url, *, params, headers, timeout):
            seen["headers"] = headers
            return _Res()

    from datetime import date

    monkeypatch.setenv("STAY22_API_KEY", "stay22_test_key")
    asyncio.run(
        gather._stay22_search(
            _Client(), date(2026, 8, 22), date(2026, 8, 23), lat=43.65, lng=-79.38
        )
    )
    assert seen["headers"] == {"X-API-KEY": "stay22_test_key"}

    monkeypatch.delenv("STAY22_API_KEY")
    asyncio.run(
        gather._stay22_search(
            _Client(), date(2026, 8, 22), date(2026, 8, 23), lat=43.65, lng=-79.38
        )
    )
    assert seen["headers"] == {}


def _stub_search(medians_by_checkin: dict[str, float], calls: list[str]):
    async def stub(client, checkin, checkout, *, lat, lng):
        calls.append(checkin.isoformat())
        median = medians_by_checkin.get(checkin.isoformat(), 200.0)
        return {"results": [_listing("H", prices=[median])]}

    return stub


def test_calendar_picks_peak_weekend_and_caches(monkeypatch) -> None:
    monkeypatch.setenv("STAY22_API_KEY", "stay22_test_key")
    monkeypatch.setattr(gather, "_calendar_cache", {})
    first = gather._next_saturday()
    saturdays = [
        (first + gather.timedelta(days=7 * i)).isoformat() for i in range(6)
    ]
    medians = {d: 200.0 + i for i, d in enumerate(saturdays)}
    medians[saturdays[2]] = 783.0  # the market's peak weekend
    calls: list[str] = []
    monkeypatch.setattr(gather, "_stay22_search", _stub_search(medians, calls))

    out = asyncio.run(gather.fetch_stay22_calendar(43.65, -79.38))
    assert out["source"] == "live"
    assert len(out["weekends"]) == 6
    assert out["peak"]["checkin"] == saturdays[2]
    assert out["peak"]["median_rate"] == 783.0

    again = asyncio.run(gather.fetch_stay22_calendar(43.65, -79.38))
    assert again is out  # in-process day-cache, no second scan
    assert len(calls) == 6


def test_calendar_demo_mode_scans_fewer_weekends(monkeypatch) -> None:
    monkeypatch.delenv("STAY22_API_KEY", raising=False)
    monkeypatch.setattr(gather, "_calendar_cache", {})
    calls: list[str] = []
    monkeypatch.setattr(gather, "_stay22_search", _stub_search({}, calls))

    out = asyncio.run(gather.fetch_stay22_calendar(43.65, -79.38))
    assert len(out["weekends"]) == 3  # demo request budget
    assert len(calls) == 3


def test_market_estimate_when_unreachable(monkeypatch) -> None:
    async def boom(client, checkin, checkout, *, lat, lng):
        raise RuntimeError("stay22 down")

    monkeypatch.setattr(gather, "_stay22_search", boom)
    monkeypatch.setattr(gather, "_last_stay22", {})
    out = asyncio.run(gather.fetch_stay22_market(lat=43.65, lng=-79.38))
    assert out["source"] == "estimate"
    assert "stay22 down" in out["error"]
    assert out["target"]["median_rate"] is None


def test_market_serves_session_cache_after_outage(monkeypatch) -> None:
    calls: list[str] = []
    monkeypatch.setattr(gather, "_last_stay22", {})
    monkeypatch.setattr(
        gather, "_stay22_search", _stub_search({}, calls)
    )
    live = asyncio.run(gather.fetch_stay22_market(lat=43.65, lng=-79.38))
    assert live["source"] == "live"
    assert live["demand_ratio"] is not None

    async def boom(client, checkin, checkout, *, lat, lng):
        raise RuntimeError("stay22 down")

    monkeypatch.setattr(gather, "_stay22_search", boom)
    cached = asyncio.run(gather.fetch_stay22_market(lat=43.65, lng=-79.38))
    assert cached["source"] == "cached"
    assert cached["target"] == live["target"]
