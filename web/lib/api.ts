import { API_BASE } from "@/lib/flags";
import type { BuildingType, Comparison, LoadProfileInfo, Memo } from "@/lib/types";

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
): Promise<Comparison> {
  return post<Comparison>("/compare", {
    building_type: buildingType,
    rooms,
    scenario,
  });
}

export function fetchMemo(
  buildingType: BuildingType,
  rooms: number,
  scenario: string,
): Promise<Memo> {
  return post<Memo>("/memo", { building_type: buildingType, rooms, scenario });
}

export function fetchProfiles(): Promise<Record<string, LoadProfileInfo>> {
  return get<Record<string, LoadProfileInfo>>("/profiles");
}
