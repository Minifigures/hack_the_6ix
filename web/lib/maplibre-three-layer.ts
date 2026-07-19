import maplibregl, { type CustomRenderMethodInput } from "maplibre-gl";
import * as THREE from "three";
import {
  buildModularBuilding,
  lngLatToLocalMetres,
  polygonCentroid,
  type LocalRing,
  type MeshBuildingSpec,
} from "@/lib/building-mesh";
import { getShape, type PlanCut } from "@/lib/building-shape";

const LAYER_ID = "modular-building-three";

type LayerState = {
  camera: THREE.Camera;
  scene: THREE.Scene;
  renderer: THREE.WebGLRenderer;
  map: maplibregl.Map;
  root: THREE.Group | null;
  origin: [number, number];
  altitude: number;
};

type LocalPt = { x: number; z: number };

function openRing(ring: GeoJSON.Position[]): GeoJSON.Position[] {
  if (
    ring.length > 1 &&
    ring[0][0] === ring[ring.length - 1][0] &&
    ring[0][1] === ring[ring.length - 1][1]
  ) {
    return ring.slice(0, -1);
  }
  return ring.slice();
}

function insetRing(
  open: GeoJSON.Position[],
  factor: number,
): GeoJSON.Position[] {
  if (open.length < 3) return open;
  const cx = open.reduce((s, p) => s + p[0], 0) / open.length;
  const cy = open.reduce((s, p) => s + p[1], 0) / open.length;
  return open.map(([x, y]) => [
    cx + (x - cx) * factor,
    cy + (y - cy) * factor,
  ]);
}

function toLocal(
  ring: GeoJSON.Position[],
  originLng: number,
  originLat: number,
): LocalPt[] {
  return ring.map(([lng, lat]) =>
    lngLatToLocalMetres(lng, lat, originLng, originLat),
  );
}

/**
 * Build an L in the parcel's own edge frame (first edge = long axis),
 * so it follows the street grid instead of a north-south AABB.
 */
function cutLWing(points: LocalPt[]): LocalPt[] {
  if (points.length < 3) return points;
  const o = points[0];
  let ux = points[1].x - o.x;
  let uz = points[1].z - o.z;
  const edgeLen = Math.hypot(ux, uz) || 1;
  ux /= edgeLen;
  uz /= edgeLen;
  const vx = -uz;
  const vz = ux;

  let minU = Infinity;
  let maxU = -Infinity;
  let minV = Infinity;
  let maxV = -Infinity;
  for (const p of points) {
    const du = (p.x - o.x) * ux + (p.z - o.z) * uz;
    const dv = (p.x - o.x) * vx + (p.z - o.z) * vz;
    minU = Math.min(minU, du);
    maxU = Math.max(maxU, du);
    minV = Math.min(minV, dv);
    maxV = Math.max(maxV, dv);
  }

  const midU = minU + (maxU - minU) * 0.48;
  const midV = minV + (maxV - minV) * 0.48;

  // L: full bar along u at low v, plus wing along v at low u.
  const corners: Array<[number, number]> = [
    [minU, minV],
    [maxU, minV],
    [maxU, midV],
    [midU, midV],
    [midU, maxV],
    [minU, maxV],
  ];

  return corners.map(([u, v]) => ({
    x: o.x + ux * u + vx * v,
    z: o.z + uz * u + vz * v,
  }));
}

/** Slender tower pad toward parcel centroid (podium upper). */
function cutTower(points: LocalPt[]): LocalPt[] {
  if (points.length < 3) return points;
  const cx = points.reduce((s, p) => s + p.x, 0) / points.length;
  const cz = points.reduce((s, p) => s + p.z, 0) / points.length;
  return points.map((p) => ({
    x: cx + (p.x - cx) * 0.42,
    z: cz + (p.z - cz) * 0.42,
  }));
}

/** Inner courtyard hole, ~35% of footprint toward center. */
function cutCourtyardHole(points: LocalPt[]): LocalPt[] {
  if (points.length < 3) return [];
  const cx = points.reduce((s, p) => s + p.x, 0) / points.length;
  const cz = points.reduce((s, p) => s + p.z, 0) / points.length;
  // Reverse winding for a hole.
  return points
    .map((p) => ({
      x: cx + (p.x - cx) * 0.38,
      z: cz + (p.z - cz) * 0.38,
    }))
    .reverse();
}

function applyPlan(
  points: LocalPt[],
  plan: PlanCut | undefined,
): { points: LocalPt[]; hole?: LocalPt[] } {
  switch (plan) {
    case "l_wing":
      return { points: cutLWing(points) };
    case "tower":
      return { points: cutTower(points) };
    case "courtyard":
      return { points, hole: cutCourtyardHole(points) };
    case "full":
    default:
      return { points };
  }
}

function buildLocalRings(
  parcel: GeoJSON.Feature<GeoJSON.Polygon>,
  spec: MeshBuildingSpec,
  originLng: number,
  originLat: number,
): LocalRing[] {
  const shape = getShape(spec.shapeId ?? "slab");
  const massing = shape.massing(spec.floors);
  const exterior = openRing(parcel.geometry.coordinates[0]);

  return massing.map((ring) => {
    const inset = insetRing(exterior, ring.inset);
    const base = toLocal(inset, originLng, originLat);
    const cut = applyPlan(base, ring.plan ?? "full");
    return {
      points: cut.points,
      hole: cut.hole,
      fromLevel: ring.fromLevel,
      toLevel: ring.toLevel,
    };
  });
}

/**
 * MapLibre custom layer: Three.js modular building in metre space at the
 * parcel centroid (official MapLibre + three.js pattern).
 */
export type ModularBuildingLayer = maplibregl.CustomLayerInterface & {
  sync(
    building: MeshBuildingSpec | null,
    parcel: GeoJSON.Feature<GeoJSON.Polygon>,
  ): void;
};

export function createModularBuildingLayer(): ModularBuildingLayer {
  const state: Partial<LayerState> = {};

  const layer: ModularBuildingLayer = {
    id: LAYER_ID,
    type: "custom" as const,
    renderingMode: "3d" as const,

    onAdd(map: maplibregl.Map, gl: WebGLRenderingContext | WebGL2RenderingContext) {
      const camera = new THREE.Camera();
      const scene = new THREE.Scene();

      const ambient = new THREE.AmbientLight(0xffffff, 0.55);
      scene.add(ambient);
      const sun = new THREE.DirectionalLight(0xfff2e0, 1.1);
      sun.position.set(80, 120, 40);
      scene.add(sun);
      const fill = new THREE.DirectionalLight(0xc8d8ff, 0.45);
      fill.position.set(-60, 40, -80);
      scene.add(fill);

      const renderer = new THREE.WebGLRenderer({
        canvas: map.getCanvas(),
        context: gl,
        antialias: true,
      });
      renderer.autoClear = false;

      state.camera = camera;
      state.scene = scene;
      state.renderer = renderer;
      state.map = map;
      state.root = null;
      state.origin = [0, 0];
      state.altitude = 0;
    },

    onRemove(_map: maplibregl.Map, _gl: WebGLRenderingContext | WebGL2RenderingContext) {
      if (state.root && state.scene) {
        state.scene.remove(state.root);
        (state.root.userData.dispose as (() => void) | undefined)?.();
        state.root = null;
      }
      state.renderer?.dispose();
    },

    render(_gl: WebGLRenderingContext | WebGL2RenderingContext, args: CustomRenderMethodInput) {
      if (!state.camera || !state.scene || !state.renderer || !state.map) return;
      if (!state.root || !state.origin) return;

      // Official MapLibre helper: metres at lng/lat, Y-up (includes Rz/Rx/scale).
      const modelMatrix = state.map.transform.getMatrixForModel(
        state.origin,
        state.altitude ?? 0,
      );
      const m = new THREE.Matrix4().fromArray(args.defaultProjectionData.mainMatrix);
      const l = new THREE.Matrix4().fromArray(modelMatrix);

      state.camera.projectionMatrix = m.multiply(l);
      state.renderer.resetState();
      state.renderer.render(state.scene, state.camera);
      state.map.triggerRepaint();
    },

    sync(
      building: MeshBuildingSpec | null,
      parcel: GeoJSON.Feature<GeoJSON.Polygon>,
    ) {
      if (!state.scene || !state.map) return;

      if (state.root) {
        state.scene.remove(state.root);
        (state.root.userData.dispose as (() => void) | undefined)?.();
        state.root = null;
      }

      const ring0 = parcel.geometry?.coordinates?.[0];
      if (!building || !ring0 || ring0.length < 3) {
        state.map.triggerRepaint();
        return;
      }

      const exterior = openRing(ring0);
      const { lng, lat } = polygonCentroid(exterior);
      state.origin = [lng, lat];
      state.altitude = 0;

      const rings = buildLocalRings(parcel, building, lng, lat);
      const group = buildModularBuilding(building, rings);
      state.root = group;
      state.scene.add(group);
      state.map.triggerRepaint();
    },
  };

  return layer;
}
