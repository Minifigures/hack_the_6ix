import { API_BASE } from "@/lib/flags";
import type {
  BuildingType,
  Comparison,
  Hvac,
  LoadProfileInfo,
  Memo,
  Structure,
} from "@/lib/types";

export interface OptionOverrides {
  structure_a: Structure;
  hvac_a: Hvac;
  structure_b: Structure;
  hvac_b: Hvac;
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`${path} failed: ${res.status}`);
  return (await res.json()) as T;
}

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) throw new Error(`${path} failed: ${res.status}`);
  return (await res.json()) as T;
}

export function fetchComparison(
  buildingType: BuildingType,
  rooms: number,
  scenario: string,
  overrides?: OptionOverrides,
): Promise<Comparison> {
  return post<Comparison>("/compare", {
    building_type: buildingType,
    rooms,
    scenario,
    ...overrides,
  });
}

export function fetchMemo(
  buildingType: BuildingType,
  rooms: number,
  scenario: string,
  overrides?: OptionOverrides,
): Promise<Memo> {
  return post<Memo>("/memo", {
    building_type: buildingType,
    rooms,
    scenario,
    ...overrides,
  });
}

export function fetchProfiles(): Promise<Record<string, LoadProfileInfo>> {
  return get<Record<string, LoadProfileInfo>>("/profiles");
}

/** Upsert Auth0 profile into MongoDB InnSight.auth (signup / login sync). */
export function syncAuthUser(user: {
  sub: string;
  email?: string | null;
  name?: string | null;
  picture?: string | null;
  role?: string | null;
}): Promise<{ saved: boolean; upserted?: boolean; reason?: string }> {
  return post("/users/upsert", {
    sub: user.sub,
    email: user.email ?? null,
    name: user.name ?? null,
    picture: user.picture ?? null,
    role: user.role ?? null,
  });
}
