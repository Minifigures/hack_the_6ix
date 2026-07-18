export type BuildingType = "homestay" | "boutique" | "tower";
export type Structure = "concrete" | "mass_timber" | "steel";
export type Hvac = "central_gas" | "heat_pump";
export type OptionKey = "A" | "B";
export type StrainClass = "STABLE" | "ELEVATED" | "CRITICAL";

export interface OptionResult {
  scenario_name: string;
  floor_area_sqft: number;
  hourly_kw: number[];
  peak_kw: number;
  strain_ratio: number;
  strain_class: StrainClass;
  annual_elec_kwh: number;
  annual_gas_m3: number;
  annual_energy_cost: number;
  annual_demand_cost: number;
  annual_water_m3: number;
  annual_water_cost: number;
  annual_operating_cost: number;
  tco2e_operational: number;
  tco2e_embodied_amortized: number;
  tco2e_total: number;
  construction_cost: number;
  construction_cost_low: number;
  construction_cost_high: number;
  config: {
    building_type: BuildingType;
    rooms: number;
    structure: Structure;
    hvac: Hvac;
    label: string;
  };
}

export interface Comparison {
  option_a: OptionResult;
  option_b: OptionResult;
  scenario_name: string;
  capex_delta: number;
  annual_cost_delta: number;
  tco2e_delta: number;
  payback_years: number | null;
  abatement_cost: number | null;
  abatement_threshold: number;
  recommended: OptionKey;
  reasoning: string[];
}

export interface Footnote {
  index: number;
  key: string;
  value: number;
  unit: string;
  source: string;
  note: string;
  estimate: boolean;
}

export interface MemoOption {
  key: OptionKey;
  label: string;
  building_type: BuildingType;
  rooms: number;
  structure: Structure;
  hvac: Hvac;
  floor_area_sqft: number;
  construction_cost: {
    low: number;
    mid: number;
    high: number;
    method: string;
    footnotes: number[];
  };
  annual_energy_cost: {
    value: number;
    energy_portion: number;
    demand_portion: number;
    elec_kwh: number;
    gas_m3: number;
    footnotes: number[];
  };
  annual_water: { m3: number; cost: number; footnotes: number[] };
  tco2e_per_year: {
    operational: number;
    embodied_amortized: number;
    total: number;
    footnotes: number[];
    biogenic_note?: string;
  };
  peak_grid_strain: {
    class: StrainClass;
    ratio: number;
    peak_kw: number;
    label: string;
    footnotes: number[];
  };
  community_friction: {
    score: number;
    terms: Record<string, number>;
    label: string;
    formula: string;
  };
}

export interface Memo {
  title: string;
  scenario: string;
  options: MemoOption[];
  comparison: {
    capex_delta: number;
    annual_cost_delta: number;
    tco2e_delta: number;
    payback_years: number | null;
    abatement_cost: number | null;
    abatement_threshold: number;
    recommended: OptionKey;
    footnotes: number[];
  };
  reasoning_chain: string[];
  narrative: {
    summary: string;
    reasoning: string[];
    caveats: string[];
    generator: string;
  };
  footnotes: Footnote[];
}

export interface LoadProfileInfo {
  label: string;
  character: string;
  hourly_shape: number[];
}
