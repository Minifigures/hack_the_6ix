import type { Hvac, OptionKey, Structure } from "@/lib/types";

// The assembler's component tree (ref_2). Foundation and facade are recorded
// and surfaced in the structure log; the engine's numbers are driven by the
// derived structure + energy system (documented in MOCKS ledger).
export interface BuildComponents {
  foundation: "reinforced_concrete" | "precast_piles";
  mainStructure: "timber" | "steel_brace";
  floors: "mass_timber" | "hollow_core";
  facade: "curtain_wall" | "rainscreen";
  energy: "heat_pump" | "central_plant";
}

export const COMPONENT_LABELS: Record<string, string> = {
  reinforced_concrete: "Reinforced Concrete",
  precast_piles: "Precast Piles",
  timber: "Timber",
  steel_brace: "Steel brace",
  mass_timber: "Mass Timber",
  hollow_core: "Hollow-core Concrete",
  curtain_wall: "Curtain Wall",
  rainscreen: "Rainscreen",
  heat_pump: "Heat Pump",
  central_plant: "Central Plant",
};

export const OPTION_PRESETS: Record<OptionKey, BuildComponents> = {
  A: {
    foundation: "reinforced_concrete",
    mainStructure: "steel_brace",
    floors: "hollow_core",
    facade: "curtain_wall",
    energy: "central_plant",
  },
  B: {
    foundation: "precast_piles",
    mainStructure: "timber",
    floors: "mass_timber",
    facade: "rainscreen",
    energy: "heat_pump",
  },
};

// Primary gravity system decides the engine structure: timber elements win,
// hollow-core floors read as a concrete building, a steel brace with concrete
// floors is still a concrete-mass hybrid.
export function deriveStructure(c: BuildComponents): Structure {
  if (c.mainStructure === "timber" || c.floors === "mass_timber") {
    return "mass_timber";
  }
  return "concrete";
}

export function deriveHvac(c: BuildComponents): Hvac {
  return c.energy === "heat_pump" ? "heat_pump" : "central_gas";
}

/** Short Option A/B subtitle from live components (not a fixed preset blurb). */
export function optionSummary(c: BuildComponents): string {
  const structure =
    c.mainStructure === "timber" || c.floors === "mass_timber"
      ? "Timber"
      : c.mainStructure === "steel_brace"
        ? "Steel"
        : "Concrete";
  const energy = c.energy === "heat_pump" ? "Heat pumps" : "Central plant";
  return `${structure} · ${energy}`;
}

export interface LogEntry {
  kind: "warning" | "confirm";
  text: string;
  icon: "shear" | "bolt" | "frame" | "pulse";
}

// Deterministic structure-log entries in the ref_2 style, generated from the
// actual selection (rule-based, illustrative engineering flavour).
export function structureLog(
  c: BuildComponents,
  floors: number,
  optionLabel: string,
): LogEntry[] {
  const entries: LogEntry[] = [];
  if (c.floors === "mass_timber" && floors >= 6) {
    entries.push({
      kind: "warning",
      text: `Mass Timber Floor-Wall Connection Shear Stress Level 3 (${floors} storeys)`,
      icon: "shear",
    });
  }
  if (c.mainStructure === "timber" && c.foundation === "reinforced_concrete") {
    entries.push({
      kind: "warning",
      text: "Timber frame on rigid foundation: verify differential movement detailing",
      icon: "bolt",
    });
  }
  if (c.mainStructure === "steel_brace" && c.floors === "hollow_core") {
    entries.push({
      kind: "confirm",
      text: "Structure: Frame-Core combination confirmed (Hybrid Type)",
      icon: "frame",
    });
  }
  if (c.mainStructure === "timber" && c.floors === "mass_timber") {
    entries.push({
      kind: "confirm",
      text: "Structure: Full mass-timber gravity system confirmed",
      icon: "frame",
    });
  }
  if (c.facade === "rainscreen" && c.energy === "heat_pump") {
    entries.push({
      kind: "confirm",
      text: "Envelope + heat-pump pairing: low-carbon services confirmed",
      icon: "pulse",
    });
  }
  entries.push({
    kind: "confirm",
    text: `${optionLabel}: components locked, metrics updating live`,
    icon: "pulse",
  });
  return entries;
}
