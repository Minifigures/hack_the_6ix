"""Area briefing: live climate + elevation for a lat/lng (Open-Meteo, no key)."""

from __future__ import annotations

import asyncio
import time
from typing import Any

import httpx
from fastapi import APIRouter, HTTPException, Query

router = APIRouter(tags=["area"])

FORECAST = "https://api.open-meteo.com/v1/forecast"
ELEVATION = "https://api.open-meteo.com/v1/elevation"
USER_AGENT = "INNSIGHT/0.1 (Hack the 6ix)"

# Round to ~1 km so nearby clicks share a cache entry.
_CACHE: dict[str, tuple[float, dict[str, Any]]] = {}
_CACHE_TTL_S = 300.0
_CACHE_MAX = 100


def _cache_key(lat: float, lng: float) -> str:
    return f"{round(lat, 2)},{round(lng, 2)}"


def _cache_get(key: str) -> dict[str, Any] | None:
    hit = _CACHE.get(key)
    if not hit:
        return None
    expires, value = hit
    if time.time() > expires:
        _CACHE.pop(key, None)
        return None
    return value


def _cache_set(key: str, value: dict[str, Any]) -> None:
    if len(_CACHE) >= _CACHE_MAX:
        for k, _ in sorted(_CACHE.items(), key=lambda kv: kv[1][0])[:25]:
            _CACHE.pop(k, None)
    _CACHE[key] = (time.time() + _CACHE_TTL_S, value)

_WMO = {
    0: "Clear",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    61: "Rain",
    63: "Rain",
    65: "Heavy rain",
    71: "Snow",
    80: "Rain showers",
    95: "Thunderstorm",
}


def _weather_label(code: int | None) -> str:
    if code is None:
        return "Unknown"
    return _WMO.get(int(code), f"Code {code}")


@router.get("/area/brief")
async def area_brief(
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
) -> dict[str, Any]:
    key = _cache_key(lat, lng)
    cached = _cache_get(key)
    if cached is not None:
        return {**cached, "lat": lat, "lng": lng}

    params = {
        "latitude": lat,
        "longitude": lng,
        "current": (
            "temperature_2m,relative_humidity_2m,apparent_temperature,"
            "precipitation,weather_code,wind_speed_10m"
        ),
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
        "timezone": "auto",
        "forecast_days": 3,
    }
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            forecast_res, elev_res = await asyncio.gather(
                client.get(
                    FORECAST, params=params, headers={"User-Agent": USER_AGENT}
                ),
                client.get(
                    ELEVATION,
                    params={"latitude": lat, "longitude": lng},
                    headers={"User-Agent": USER_AGENT},
                ),
            )
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"climate upstream: {exc}") from exc

    if forecast_res.status_code != 200:
        raise HTTPException(
            status_code=502, detail=f"forecast status {forecast_res.status_code}"
        )

    data = forecast_res.json()
    current = data.get("current") or {}
    daily = data.get("daily") or {}
    elevation_m = None
    if elev_res.status_code == 200:
        elevs = (elev_res.json() or {}).get("elevation") or []
        if elevs:
            elevation_m = elevs[0]

    code = current.get("weather_code")
    payload = {
        "lat": lat,
        "lng": lng,
        "timezone": data.get("timezone"),
        "elevation_m": elevation_m,
        "climate": {
            "temp_c": current.get("temperature_2m"),
            "feels_like_c": current.get("apparent_temperature"),
            "humidity_pct": current.get("relative_humidity_2m"),
            "precip_mm": current.get("precipitation"),
            "wind_kmh": current.get("wind_speed_10m"),
            "weather": _weather_label(code),
            "weather_code": code,
        },
        "outlook_3d": {
            "dates": daily.get("time") or [],
            "tmax_c": daily.get("temperature_2m_max") or [],
            "tmin_c": daily.get("temperature_2m_min") or [],
            "precip_mm": daily.get("precipitation_sum") or [],
        },
        "source": "Open-Meteo (live)",
        "note": "Live weather for this coordinate. Land parcels still come from OSM.",
    }
    _cache_set(key, payload)
    return payload
