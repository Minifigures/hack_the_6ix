"use client";

import { useEffect, useRef } from "react";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { SITE, SITE_POLYGON } from "@/lib/site";
import type { Structure } from "@/lib/types";

// Esri World Imagery raster tiles; attribution required, no key needed.
const SATELLITE_STYLE: maplibregl.StyleSpecification = {
  version: 8,
  sources: {
    satellite: {
      type: "raster",
      tiles: [
        "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
      ],
      tileSize: 256,
      attribution:
        "Imagery © Esri, Maxar, Earthstar Geographics, and the GIS User Community",
    },
  },
  layers: [{ id: "satellite", type: "raster", source: "satellite" }],
};

const STRUCTURE_COLOUR: Record<Structure, string> = {
  concrete: "#9aa5b1",
  mass_timber: "#d97e3f",
  steel: "#7d93a8",
};

// Building footprint: the site polygon inset toward its centroid.
function insetPolygon(
  feature: GeoJSON.Feature<GeoJSON.Polygon>,
  factor: number,
): GeoJSON.Feature<GeoJSON.Polygon> {
  const ring = feature.geometry.coordinates[0];
  const cx = ring.reduce((s, p) => s + p[0], 0) / ring.length;
  const cy = ring.reduce((s, p) => s + p[1], 0) / ring.length;
  const inset = ring.map(([x, y]) => [
    cx + (x - cx) * factor,
    cy + (y - cy) * factor,
  ]);
  return {
    type: "Feature",
    properties: {},
    geometry: { type: "Polygon", coordinates: [inset] },
  };
}

export interface BuildingSpec {
  structure: Structure;
  floors: number;
}

interface SiteMapProps {
  building: BuildingSpec | null;
}

export function SiteMap({ building }: SiteMapProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const readyRef = useRef(false);
  const buildingRef = useRef<BuildingSpec | null>(building);
  buildingRef.current = building;

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;

    const map = new maplibregl.Map({
      container: containerRef.current,
      style: SATELLITE_STYLE,
      center: [SITE.lng, SITE.lat],
      zoom: SITE.zoom,
      pitch: 55,
      bearing: -15,
      attributionControl: { compact: true },
    });
    mapRef.current = map;

    map.addControl(new maplibregl.NavigationControl(), "top-left");

    map.on("load", () => {
      map.addSource("site", { type: "geojson", data: SITE_POLYGON });
      map.addSource("building", {
        type: "geojson",
        data: insetPolygon(SITE_POLYGON, 0.72),
      });
      map.addLayer({
        id: "site-fill",
        type: "fill",
        source: "site",
        paint: { "fill-color": "#f5c518", "fill-opacity": 0.08 },
      });
      map.addLayer({
        id: "site-outline",
        type: "line",
        source: "site",
        paint: { "line-color": "#10151c", "line-width": 2 },
      });
      map.addLayer({
        id: "building-mass",
        type: "fill-extrusion",
        source: "building",
        paint: {
          "fill-extrusion-color": "#9aa5b1",
          "fill-extrusion-height": 0,
          "fill-extrusion-opacity": 0.92,
        },
      });
      readyRef.current = true;
      syncBuilding(map, buildingRef.current);
    });

    return () => {
      readyRef.current = false;
      map.remove();
      mapRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (map && readyRef.current) syncBuilding(map, building);
  }, [building]);

  return (
    <div className="relative h-full w-full">
      <div ref={containerRef} className="h-full w-full" />
      <div className="pointer-events-none absolute left-1/2 top-3 -translate-x-1/2 rounded bg-white/90 px-2.5 py-1 text-[11px] font-medium text-text-strong shadow">
        SITE: {SITE.name}
      </div>
    </div>
  );
}

function syncBuilding(map: maplibregl.Map, building: BuildingSpec | null) {
  if (!map.getLayer("building-mass")) return;
  const height = building ? building.floors * 3.4 : 0;
  const colour = building ? STRUCTURE_COLOUR[building.structure] : "#9aa5b1";
  map.setPaintProperty("building-mass", "fill-extrusion-height", height);
  map.setPaintProperty("building-mass", "fill-extrusion-color", colour);
}
