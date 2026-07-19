"""Find empty build sites near a point via OpenStreetMap Overpass.

Prefers OSM land uses that are typically undeveloped (brownfield, grass,
parking, etc.). Never queries buildings or highways as candidates.
Falls back to approximate offset pads if Overpass is down.
"""

from __future__ import annotations

import math
from typing import Any

import httpx
from fastapi import APIRouter, Query

router = APIRouter(tags=["sites"])

# Endpoint order and timeouts follow live testing (Jul 2026): the fr instance
# is fastest and most consistent but filters User-Agents (app name + real
# contact passes); overpass-api.de is the slower, rate-limited fallback.
OVERPASS_URLS = (
    ("https://overpass.openstreetmap.fr/api/interpreter", 8.0),
    ("https://overpass-api.de/api/interpreter", 15.0),
)
USER_AGENT = "INNSIGHT/0.1 (contact minifiguresgt@gmail.com)"

# One round trip returns candidate parcels AND building footprints (~440 KB,
# ~2 s live-tested downtown), so parcel filtering and the 3D context layer
# share a single Overpass call.
_COMBINED_QUERY = """
[out:json][timeout:20];
(
  way["amenity"="parking"]["parking"="surface"](around:{radius},{lat},{lng});
  way["landuse"~"^(brownfield|greenfield|construction|vacant)$"](around:{radius},{lat},{lng});
)->.parcels;
way["building"](around:{radius},{lat},{lng})->.buildings;
.parcels out geom;
.buildings out geom;
"""

# Must cover Query(limit) max (8). A 5-letter string caused IndexError once
# Overpass returned 6+ parcels, silently falling through to curated pads.
_LABELS = "ABCDEFGH"

# Curated real parcels near the demo site, corners traced from the City of
# Toronto 2025 orthophoto (8 cm). Used when Overpass is unreachable so the
# venue demo never shows pads on rooftops.
_CURATED_TORONTO: list[dict[str, Any]] = [
    {
        # 55 Lake Shore Blvd E block (Freeland–Cooper), south of Lake Shore /
        # rail corridor — full vacant pad visible on 2025 ortho (not a NW scrap).
        "label": "Gravel lot south of rail corridor (traced from 2025 ortho)",
        "kind": "traced",
        "ring": [
            [-79.37388, 43.64458],
            [-79.37232, 43.64490],
            [-79.37218, 43.64340],
            [-79.37372, 43.64312],
            [-79.37388, 43.64458],
        ],
    },
    {
        "label": "Construction site west (traced from 2025 ortho)",
        "kind": "traced",
        "ring": [
            [-79.37806, 43.64576],
            [-79.37736, 43.64580],
            [-79.37731, 43.64537],
            [-79.37800, 43.64533],
            [-79.37806, 43.64576],
        ],
    },
]
_CURATED_CENTRE = (43.6474, -79.3736)
_CURATED_RANGE_DEG = 0.015  # ~1.5 km


def _curated_sites(lat: float, lng: float) -> list[dict[str, Any]] | None:
    if (
        abs(lat - _CURATED_CENTRE[0]) > _CURATED_RANGE_DEG
        or abs(lng - _CURATED_CENTRE[1]) > _CURATED_RANGE_DEG
    ):
        return None
    out: list[dict[str, Any]] = []
    for i, raw in enumerate(_CURATED_TORONTO):
        site_id = f"empty-{_LABELS[i]}"
        ring = raw["ring"]
        clng, clat = _centroid(ring)
        areas = _area_fields(ring)
        out.append(
            {
                "id": site_id,
                "label": raw["label"],
                "kind": raw["kind"],
                "center": {"lng": clng, "lat": clat},
                **areas,
                "polygon": {
                    "type": "Feature",
                    "properties": {
                        "id": site_id,
                        "label": raw["label"],
                        "kind": raw["kind"],
                        **areas,
                    },
                    "geometry": {"type": "Polygon", "coordinates": [ring]},
                },
            }
        )
    return out


# Last good Overpass result per rounded location; venue wifi insurance only.
_cache: dict[tuple[float, float], list[dict[str, Any]]] = {}

_context_cache: dict[tuple[float, float], dict[str, Any]] = {}


def _building_height(tags: dict[str, Any]) -> float:
    raw_height = tags.get("height")
    if raw_height:
        try:
            token = str(raw_height).split()[0]
            return max(3.0, min(140.0, float(token)))
        except (ValueError, IndexError):
            pass
    levels = tags.get("building:levels")
    if levels:
        try:
            return max(3.0, min(140.0, float(levels) * 3.2))
        except ValueError:
            pass
    return 10.0


def _ring_from_geometry(geom: list[dict[str, float]]) -> list[list[float]] | None:
    if not geom or len(geom) < 3:
        return None
    ring = [[float(p["lon"]), float(p["lat"])] for p in geom]
    if ring[0] != ring[-1]:
        ring.append(ring[0])
    if len(ring) < 4:
        return None
    return ring


def _centroid(ring: list[list[float]]) -> tuple[float, float]:
    xs = [p[0] for p in ring[:-1]]
    ys = [p[1] for p in ring[:-1]]
    return sum(xs) / len(xs), sum(ys) / len(ys)


def _area_approx(ring: list[list[float]]) -> float:
    """Degree² shoelace — used only for relative size filtering."""
    a = 0.0
    for i in range(len(ring) - 1):
        a += ring[i][0] * ring[i + 1][1] - ring[i + 1][0] * ring[i][1]
    return abs(a) * 0.5


_M2_PER_ACRE = 4046.8564224


def _area_m2(ring: list[list[float]]) -> float:
    """Approx polygon area in m² via local equirectangular projection."""
    if len(ring) < 4:
        return 0.0
    _clng, clat = _centroid(ring)
    cos_lat = math.cos(math.radians(clat)) or 1e-6
    pts: list[tuple[float, float]] = []
    for lng, lat in ring:
        x = (lng - _clng) * 111_320.0 * cos_lat
        y = (lat - clat) * 111_320.0
        pts.append((x, y))
    a = 0.0
    for i in range(len(pts) - 1):
        a += pts[i][0] * pts[i + 1][1] - pts[i + 1][0] * pts[i][1]
    return abs(a) * 0.5


def _area_fields(ring: list[list[float]]) -> dict[str, float]:
    m2 = round(_area_m2(ring), 1)
    return {"area_m2": m2, "area_acres": round(m2 / _M2_PER_ACRE, 3)}


def _offset(lng: float, lat: float, east_m: float, north_m: float) -> tuple[float, float]:
    d_lat = north_m / 111_320.0
    cos_lat = math.cos(math.radians(lat)) or 1e-6
    d_lng = east_m / (111_320.0 * cos_lat)
    return lng + d_lng, lat + d_lat


def _rect(lng: float, lat: float, half_w: float, half_h: float) -> list[list[float]]:
    sw = _offset(lng, lat, -half_w, -half_h)
    se = _offset(lng, lat, half_w, -half_h)
    ne = _offset(lng, lat, half_w, half_h)
    nw = _offset(lng, lat, -half_w, half_h)
    return [list(sw), list(se), list(ne), list(nw), list(sw)]


def _fallback_sites(lat: float, lng: float, limit: int) -> list[dict[str, Any]]:
    """Offset pads away from the pin — never on the exact road center."""
    offsets = (
        (95, 70, 24, 28),
        (-90, 75, 26, 22),
        (80, -85, 22, 26),
        (-75, -80, 28, 24),
        (110, -40, 20, 24),
    )
    out: list[dict[str, Any]] = []
    for i, (e, n, w, h) in enumerate(offsets[:limit]):
        clng, clat = _offset(lng, lat, e, n)
        label = f"Empty site {_LABELS[i]} (approx.)"
        site_id = f"empty-{_LABELS[i]}"
        ring = _rect(clng, clat, w, h)
        areas = _area_fields(ring)
        out.append(
            {
                "id": site_id,
                "label": label,
                "kind": "approx",
                "center": {"lng": clng, "lat": clat},
                **areas,
                "polygon": {
                    "type": "Feature",
                    "properties": {
                        "id": site_id,
                        "label": label,
                        "kind": "approx",
                        **areas,
                    },
                    "geometry": {"type": "Polygon", "coordinates": [ring]},
                },
            }
        )
    return out


def _point_in_ring(lng: float, lat: float, ring: list[list[float]]) -> bool:
    inside = False
    j = len(ring) - 2
    for i in range(len(ring) - 1):
        xi, yi = ring[i]
        xj, yj = ring[j]
        if (yi > lat) != (yj > lat) and lng < (xj - xi) * (lat - yi) / (
            (yj - yi) or 1e-12
        ) + xi:
            inside = not inside
        j = i
    return inside


def _intersects_building(
    ring: list[list[float]], building_rings: list[list[list[float]]]
) -> bool:
    """Real polygon intersection where shapely is available; bounding boxes
    falsely reject nearly everything downtown (live-tested)."""
    try:
        from shapely.geometry import Polygon

        candidate = Polygon(ring)
        if not candidate.is_valid:
            candidate = candidate.buffer(0)
        for other in building_rings:
            try:
                poly = Polygon(other)
                if not poly.is_valid:
                    poly = poly.buffer(0)
                if candidate.intersects(poly):
                    return True
            except Exception:
                continue
        return False
    except ImportError:
        clng, clat = _centroid(ring)
        return any(_point_in_ring(clng, clat, b) for b in building_rings)


def _elements_to_sites(
    elements: list[dict[str, Any]],
    limit: int,
    building_rings: list[list[list[float]]] | None = None,
) -> list[dict[str, Any]]:
    scored: list[tuple[float, dict[str, Any]]] = []
    for el in elements:
        geom = el.get("geometry")
        if not isinstance(geom, list):
            continue
        ring = _ring_from_geometry(geom)
        if not ring:
            continue
        area = _area_approx(ring)
        if area < 1e-9 or area > 8e-5:
            continue
        tags = el.get("tags") or {}
        if "building" in tags:
            continue
        if building_rings and _intersects_building(ring, building_rings):
            continue
        kind = tags.get("landuse") or tags.get("natural") or tags.get("amenity") or "open"
        if kind == "construction":
            kind = "construction, already committed"
        clng, clat = _centroid(ring)
        scored.append((area, {"kind": kind, "lng": clng, "lat": clat, "ring": ring}))

    scored.sort(key=lambda t: t[0], reverse=True)
    out: list[dict[str, Any]] = []
    for i, (_, raw) in enumerate(scored[: min(limit, len(_LABELS))]):
        label = f"Empty site {_LABELS[i]} ({raw['kind']})"
        site_id = f"empty-{_LABELS[i]}"
        ring = raw["ring"]
        areas = _area_fields(ring)
        out.append(
            {
                "id": site_id,
                "label": label,
                "kind": raw["kind"],
                "center": {"lng": raw["lng"], "lat": raw["lat"]},
                **areas,
                "polygon": {
                    "type": "Feature",
                    "properties": {
                        "id": site_id,
                        "label": label,
                        "kind": raw["kind"],
                        **areas,
                    },
                    "geometry": {"type": "Polygon", "coordinates": [ring]},
                },
            }
        )
    return out


async def _query_overpass(
    lat: float, lng: float, radius: int
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """One combined round trip: (parcel elements, building elements)."""
    query = _COMBINED_QUERY.format(lat=lat, lng=lng, radius=radius)
    last_err: Exception | None = None
    for url, timeout in OVERPASS_URLS:
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                res = await client.post(
                    url,
                    data={"data": query},
                    headers={"User-Agent": USER_AGENT},
                )
            if res.status_code != 200:
                continue
            elements = list((res.json() or {}).get("elements") or [])
            parcels = [e for e in elements if "building" not in (e.get("tags") or {})]
            buildings = [e for e in elements if "building" in (e.get("tags") or {})]
            return parcels, buildings
        except Exception as exc:  # noqa: BLE001
            last_err = exc
            continue
    if last_err:
        raise last_err
    return [], []


def _buildings_to_features(
    buildings: list[dict[str, Any]], limit: int = 400
) -> list[dict[str, Any]]:
    features: list[dict[str, Any]] = []
    for el in buildings[:limit]:
        ring = _ring_from_geometry(el.get("geometry") or [])
        if not ring:
            continue
        features.append(
            {
                "type": "Feature",
                "properties": {"height": _building_height(el.get("tags") or {})},
                "geometry": {"type": "Polygon", "coordinates": [ring]},
            }
        )
    return features


@router.get("/sites/context")
async def context_buildings(
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
    radius: int = Query(450, ge=100, le=900),
    limit: int = Query(400, ge=10, le=800),
) -> dict[str, Any]:
    """Neighbouring OSM building footprints with heights, for the 3D context
    layer. Empty collection on failure; the map simply renders without it."""
    cache_key = (round(lat, 3), round(lng, 3))
    cached = _context_cache.get(cache_key)
    if cached:
        return cached

    features: list[dict[str, Any]] = []
    try:
        _, buildings = await _query_overpass(lat, lng, radius)
        features = _buildings_to_features(buildings, limit)
    except Exception:
        features = []

    payload = {
        "type": "FeatureCollection",
        "features": features,
        "source": "openstreetmap" if features else "unavailable",
    }
    if features:
        _context_cache[cache_key] = payload
    return payload


@router.get("/sites/empty")
async def empty_sites(
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
    radius: int = Query(700, ge=150, le=2000),
    limit: int = Query(5, ge=1, le=8),
) -> dict[str, Any]:
    note_osm = "OSM open land / parking — not a legal vacant-lot registry."
    cache_key = (round(lat, 3), round(lng, 3))
    try:
        parcels, buildings = await _query_overpass(lat, lng, radius)
        building_rings = [
            r
            for el in buildings
            if (r := _ring_from_geometry(el.get("geometry") or []))
        ]
        sites = _elements_to_sites(parcels, limit, building_rings)
        if buildings:
            # Same round trip feeds the 3D context layer.
            _context_cache[cache_key] = {
                "type": "FeatureCollection",
                "features": _buildings_to_features(buildings),
                "source": "openstreetmap",
            }
        if sites:
            _cache[cache_key] = sites
            return {
                "sites": sites,
                "source": "openstreetmap-overpass",
                "note": note_osm,
                "count": len(sites),
            }
    except Exception:
        pass

    cached = _cache.get(cache_key)
    if cached:
        return {
            "sites": cached,
            "source": "openstreetmap-overpass-cached",
            "note": note_osm + " (cached)",
            "count": len(cached),
        }

    curated = _curated_sites(lat, lng)
    if curated:
        return {
            "sites": curated,
            "source": "curated-orthophoto",
            "note": "OSM unavailable — parcels from Toronto 2025 ortho.",
            "count": len(curated),
        }

    sites = _fallback_sites(lat, lng, limit)
    return {
        "sites": sites,
        "source": "approx-fallback",
        "note": "OSM unavailable — approx pads; verify on imagery.",
        "count": len(sites),
    }
