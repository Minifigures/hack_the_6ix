/** Building plan shapes: distribution, massing rings, estimate modifiers.

Storeys (UI "Floors") are separate from assembler material `BuildComponents.floors`.
GFA in the sim remains rooms × sqft; shape only redistributes rooms and applies
labelled estimate multipliers.
*/

export type ShapeId = "slab" | "l_wing" | "courtyard" | "podium_tower";

/** How a massing ring cuts the parcel footprint. */
export type PlanCut = "full" | "l_wing" | "tower" | "courtyard";

export interface ShapeModifiers {
  facade_area: number;
  circulation: number;
  embodied: number;
}

export interface MassingRing {
  /** 0..1 inset of parcel polygon (1 = full footprint). */
  inset: number;
  /** Inclusive 0-based storey index. */
  fromLevel: number;
  /** Exclusive upper storey index. */
  toLevel: number;
  /** Footprint cut — defaults to full inset parcel. */
  plan?: PlanCut;
}

export interface BuildingShape {
  id: ShapeId;
  label: string;
  blurb: string;
  /** SVG path(s) in a 40×40 viewBox for wireframe thumbs. */
  wireframePaths: string[];
  modifiers: ShapeModifiers;
  distribute(rooms: number, storeys: number): number[];
  massing(storeys: number): MassingRing[];
}

function clampStoreys(storeys: number): number {
  return Math.max(1, Math.floor(storeys));
}

/** Even split; leftover rooms on lower floors. */
function evenDistribute(rooms: number, storeys: number): number[] {
  const n = clampStoreys(storeys);
  const base = Math.floor(rooms / n);
  let rem = rooms - base * n;
  const out: number[] = [];
  for (let i = 0; i < n; i++) {
    const extra = rem > 0 ? 1 : 0;
    if (rem > 0) rem -= 1;
    out.push(base + extra);
  }
  return out;
}

/** Weight floors then round while preserving sum. */
function weightedDistribute(
  rooms: number,
  storeys: number,
  weightAt: (level: number, n: number) => number,
): number[] {
  const n = clampStoreys(storeys);
  if (rooms <= 0) return Array(n).fill(0);
  const raw = Array.from({ length: n }, (_, i) => weightAt(i, n));
  const sumW = raw.reduce((a, b) => a + b, 0) || 1;
  const ideal = raw.map((w) => (rooms * w) / sumW);
  const floors = ideal.map((x) => Math.floor(x));
  let rem = rooms - floors.reduce((a, b) => a + b, 0);
  const order = ideal
    .map((x, i) => ({ i, frac: x - Math.floor(x) }))
    .sort((a, b) => b.frac - a.frac);
  let k = 0;
  while (rem > 0) {
    floors[order[k % n].i] += 1;
    rem -= 1;
    k += 1;
  }
  return floors;
}

export const BUILDING_SHAPES: Record<ShapeId, BuildingShape> = {
  slab: {
    id: "slab",
    label: "Slab",
    blurb: "Rectangular bar — even rooms per floor",
    wireframePaths: ["M6 12h28v16H6z"],
    modifiers: { facade_area: 1.0, circulation: 1.0, embodied: 1.0 },
    distribute: evenDistribute,
    massing(storeys) {
      const n = clampStoreys(storeys);
      return [{ inset: 0.92, fromLevel: 0, toLevel: n }];
    },
  },
  l_wing: {
    id: "l_wing",
    label: "L-wing",
    blurb: "L plan — denser lower / outer wing floors",
    wireframePaths: ["M6 10h18v12H6z", "M6 22h12v10H6z"],
    modifiers: { facade_area: 1.08, circulation: 1.04, embodied: 1.03 },
    distribute(rooms, storeys) {
      return weightedDistribute(rooms, storeys, (level, n) => {
        // Lower floors heavier (wing occupancy).
        return 1.15 - (level / Math.max(1, n - 1)) * 0.35;
      });
    },
    massing(storeys) {
      const n = clampStoreys(storeys);
      if (n <= 2) {
        return [{ inset: 0.92, fromLevel: 0, toLevel: n, plan: "l_wing" }];
      }
      const split = Math.max(1, Math.ceil(n * 0.55));
      return [
        { inset: 0.94, fromLevel: 0, toLevel: split, plan: "l_wing" },
        // Upper floors keep the L but pull in slightly (shorter wing feel).
        { inset: 0.78, fromLevel: split, toLevel: n, plan: "l_wing" },
      ];
    },
  },
  courtyard: {
    id: "courtyard",
    label: "Courtyard",
    blurb: "O/U plan — more circulation, more facade",
    wireframePaths: ["M6 8h28v24H6z", "M14 14h12v12H14z"],
    modifiers: { facade_area: 1.18, circulation: 1.12, embodied: 1.06 },
    distribute(rooms, storeys) {
      return weightedDistribute(rooms, storeys, () => 1);
    },
    massing(storeys) {
      const n = clampStoreys(storeys);
      return [{ inset: 0.92, fromLevel: 0, toLevel: n, plan: "courtyard" }];
    },
  },
  podium_tower: {
    id: "podium_tower",
    label: "Podium + tower",
    blurb: "Wide base, slender top — rooms packed in podium",
    wireframePaths: ["M4 26h32v8H4z", "M12 8h16v18H12z"],
    modifiers: { facade_area: 1.12, circulation: 1.08, embodied: 1.05 },
    distribute(rooms, storeys) {
      return weightedDistribute(rooms, storeys, (level, n) => {
        const podiumEnd = Math.max(1, Math.ceil(n * 0.4));
        return level < podiumEnd ? 1.45 : 0.75;
      });
    },
    massing(storeys) {
      const n = clampStoreys(storeys);
      if (n <= 2) return [{ inset: 0.92, fromLevel: 0, toLevel: n, plan: "full" }];
      const podium = Math.max(1, Math.ceil(n * 0.4));
      return [
        { inset: 0.94, fromLevel: 0, toLevel: podium, plan: "full" },
        { inset: 0.55, fromLevel: podium, toLevel: n, plan: "tower" },
      ];
    },
  },
};

export const SHAPE_IDS = Object.keys(BUILDING_SHAPES) as ShapeId[];

export function getShape(id: ShapeId): BuildingShape {
  return BUILDING_SHAPES[id] ?? BUILDING_SHAPES.slab;
}

export function defaultStoreys(uiType: "hotel" | "homestay" | "bnb"): number {
  if (uiType === "hotel") return 8;
  return 3;
}

export function storeysRange(uiType: "hotel" | "homestay" | "bnb"): {
  min: number;
  max: number;
} {
  if (uiType === "hotel") return { min: 3, max: 24 };
  return { min: 2, max: 6 };
}

export function defaultShapeId(uiType: "hotel" | "homestay" | "bnb"): ShapeId {
  if (uiType === "hotel") return "slab";
  return "slab";
}

export function avgRoomsPerStorey(rooms: number, storeys: number): number {
  const n = clampStoreys(storeys);
  return Math.round((rooms / n) * 10) / 10;
}
