"use client";

import { useEffect, useRef } from "react";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import {
  candidatesToFeatureCollection,
  type CandidateSite,
} from "@/lib/candidate-sites";
import type { ActiveSite } from "@/lib/site";
import type { Structure } from "@/lib/types";

// Primary imagery: City of Toronto 2025 orthophoto (8 cm/px, open licence,
// no key). Esri World Imagery sits underneath as the outside-city fallback.
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
    "toronto-ortho": {
      type: "raster",
      tiles: [
        "https://gis.toronto.ca/arcgis/rest/services/basemap/cot_ortho_2025_color_8cm/MapServer/tile/{z}/{y}/{x}",
      ],
      tileSize: 256,
      maxzoom: 20,
      attribution:
        "Contains information licensed under the Open Government Licence - Toronto",
    },
  },
  layers: [
    { id: "satellite", type: "raster", source: "satellite" },
    { id: "toronto-ortho", type: "raster", source: "toronto-ortho" },
  ],
};

const STRUCTURE_COLOUR: Record<Structure, string> = {
  concrete: "#9aa5b1",
  mass_timber: "#d97e3f",
  steel: "#7d93a8",
};

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
    properties: feature.properties ?? {},
    geometry: { type: "Polygon", coordinates: [inset] },
  };
}

export interface BuildingSpec {
  structure: Structure;
  floors: number;
}

interface SiteMapProps {
  building: BuildingSpec | null;
  activeSite: ActiveSite;
  candidates: CandidateSite[];
  selectedCandidateId: string | null;
  sitesNote?: string;
  onSelectCandidate: (site: CandidateSite) => void;
}

export function SiteMap({
  building,
  activeSite,
  candidates,
  selectedCandidateId,
  sitesNote,
  onSelectCandidate,
}: SiteMapProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const readyRef = useRef(false);
  const buildingRef = useRef<BuildingSpec | null>(building);
  const candidatesRef = useRef(candidates);
  const onSelectRef = useRef(onSelectCandidate);
  buildingRef.current = building;
  candidatesRef.current = candidates;
  onSelectRef.current = onSelectCandidate;

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;

    const map = new maplibregl.Map({
      container: containerRef.current,
      style: SATELLITE_STYLE,
      center: [activeSite.lng, activeSite.lat],
      zoom: activeSite.zoom,
      pitch: 55,
      bearing: -15,
      attributionControl: { compact: true },
    });
    mapRef.current = map;

    map.addControl(new maplibregl.NavigationControl(), "bottom-right");

    map.on("load", () => {
      map.addSource("candidates", {
        type: "geojson",
        data: candidatesToFeatureCollection(candidatesRef.current),
      });
      map.addSource("site", { type: "geojson", data: activeSite.polygon });
      map.addSource("building", {
        type: "geojson",
        data: insetPolygon(activeSite.polygon, 0.72),
      });

      map.addLayer({
        id: "candidates-fill",
        type: "fill",
        source: "candidates",
        paint: {
          "fill-color": "#35c28f",
          "fill-opacity": 0.28,
        },
      });
      map.addLayer({
        id: "candidates-outline",
        type: "line",
        source: "candidates",
        paint: {
          "line-color": "#0d7a55",
          "line-width": 1.5,
          "line-dasharray": [2, 1],
        },
      });
      map.addLayer({
        id: "site-fill",
        type: "fill",
        source: "site",
        paint: { "fill-color": "#f5c518", "fill-opacity": 0.18 },
      });
      map.addLayer({
        id: "site-outline",
        type: "line",
        source: "site",
        paint: { "line-color": "#f5c518", "line-width": 2.5 },
      });
      map.addLayer({
        id: "building-mass",
        type: "fill-extrusion",
        source: "building",
        paint: {
          "fill-extrusion-color": "#9aa5b1",
          "fill-extrusion-height": 0,
          "fill-extrusion-opacity": 0.96,
          "fill-extrusion-vertical-gradient": true,
        },
      });
      map.addLayer({
        id: "building-shell",
        type: "fill-extrusion",
        source: "building",
        paint: {
          "fill-extrusion-color": "#f4f8fc",
          "fill-extrusion-height": 0,
          "fill-extrusion-base": 0,
          "fill-extrusion-opacity": 0.55,
          "fill-extrusion-vertical-gradient": true,
        },
      });

      map.on("click", "candidates-fill", (e) => {
        const id = e.features?.[0]?.properties?.id as string | undefined;
        if (!id) return;
        const match = candidatesRef.current.find((c) => c.id === id);
        if (match) onSelectRef.current(match);
      });
      map.on("mouseenter", "candidates-fill", () => {
        map.getCanvas().style.cursor = "pointer";
      });
      map.on("mouseleave", "candidates-fill", () => {
        map.getCanvas().style.cursor = "";
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
    if (!map || !readyRef.current) return;
    map.flyTo({
      center: [activeSite.lng, activeSite.lat],
      zoom: activeSite.zoom,
      essential: true,
      duration: 1400,
    });
    const siteSrc = map.getSource("site") as maplibregl.GeoJSONSource | undefined;
    const buildingSrc = map.getSource(
      "building",
    ) as maplibregl.GeoJSONSource | undefined;
    siteSrc?.setData(activeSite.polygon);
    buildingSrc?.setData(insetPolygon(activeSite.polygon, 0.72));
    syncBuilding(map, buildingRef.current);
  }, [activeSite]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !readyRef.current) return;
    const src = map.getSource("candidates") as maplibregl.GeoJSONSource | undefined;
    src?.setData(candidatesToFeatureCollection(candidates));
  }, [candidates]);

  useEffect(() => {
    const map = mapRef.current;
    if (map && readyRef.current) syncBuilding(map, building);
  }, [building]);

  const selectedLabel =
    candidates.find((c) => c.id === selectedCandidateId)?.label ??
    activeSite.name;

  return (
    <div className="relative h-full w-full">
      <div ref={containerRef} className="h-full w-full" />

      <div className="pointer-events-none absolute right-3 top-3 z-20 max-w-[15rem]">
        <div className="rounded-md border border-white/20 bg-ink/80 px-3 py-2 shadow-lg backdrop-blur-sm">
          <p className="text-[9px] font-semibold uppercase tracking-wider text-white/55">
            Active site
          </p>
          <p className="truncate text-[12px] font-semibold text-white">
            {selectedLabel}
          </p>
        </div>
      </div>

      <p className="pointer-events-none absolute bottom-3 left-1/2 z-10 max-w-md -translate-x-1/2 rounded-md bg-ink/80 px-3 py-1.5 text-center text-[10px] leading-snug text-white/90 backdrop-blur-sm">
        {sitesNote?.trim()
          ? sitesNote
          : "Green = open OSM land. Click a parcel to select — not buildings or roads."}
      </p>
    </div>
  );
}

function syncBuilding(map: maplibregl.Map, building: BuildingSpec | null) {
  if (!map.getLayer("building-mass") || !map.getLayer("building-shell")) return;
  // Zero-height extrusions still paint a flat slab; hide the layers instead.
  const visibility = building ? "visible" : "none";
  map.setLayoutProperty("building-mass", "visibility", visibility);
  map.setLayoutProperty("building-shell", "visibility", visibility);
  if (!building) return;
  const total = building.floors * 3.4;
  const lower = total * 0.55;
  const colour = STRUCTURE_COLOUR[building.structure];
  map.setPaintProperty("building-mass", "fill-extrusion-height", lower);
  map.setPaintProperty("building-mass", "fill-extrusion-color", colour);
  map.setPaintProperty("building-shell", "fill-extrusion-base", lower);
  map.setPaintProperty("building-shell", "fill-extrusion-height", total);
}
