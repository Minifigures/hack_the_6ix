"use client";

export interface AreaBrief {
  lat: number;
  lng: number;
  timezone?: string;
  elevation_m?: number | null;
  climate: {
    temp_c?: number | null;
    feels_like_c?: number | null;
    humidity_pct?: number | null;
    precip_mm?: number | null;
    wind_kmh?: number | null;
    weather?: string;
  };
  outlook_3d?: {
    dates: string[];
    tmax_c: number[];
    tmin_c: number[];
    precip_mm: number[];
  };
  source?: string;
  note?: string;
  land?: {
    empty_count: number;
    kinds: string[];
  };
}

interface AreaBriefPanelProps {
  placeName: string;
  brief: AreaBrief | null;
  loading: boolean;
}

function fmt(n: number | null | undefined, suffix = "", digits = 0): string {
  if (n === null || n === undefined || Number.isNaN(n)) return "—";
  return `${n.toFixed(digits)}${suffix}`;
}

export function AreaBriefPanel({
  placeName,
  brief,
  loading,
}: AreaBriefPanelProps) {
  if (loading) {
    return (
      <aside className="absolute bottom-14 left-3 z-20 w-[min(100%-1.5rem,17rem)] rounded-md border border-panel-border bg-white/95 p-3 shadow-md">
        <p className="text-[10px] font-semibold uppercase tracking-wider text-text-soft">
          Area data
        </p>
        <p className="mt-1 text-[12px] text-text-soft">Loading live climate…</p>
      </aside>
    );
  }

  if (!brief) return null;

  const c = brief.climate;
  const day0 =
    brief.outlook_3d?.dates?.[0] &&
    brief.outlook_3d.tmax_c?.[0] !== undefined
      ? {
          date: brief.outlook_3d.dates[0],
          tmax: brief.outlook_3d.tmax_c[0],
          tmin: brief.outlook_3d.tmin_c[0],
          precip: brief.outlook_3d.precip_mm[0],
        }
      : null;

  return (
    <aside className="absolute bottom-14 left-3 z-20 w-[min(100%-1.5rem,17rem)] rounded-md border border-panel-border bg-white/95 p-3 shadow-md">
      <p className="text-[10px] font-semibold uppercase tracking-wider text-text-soft">
        Area data · live
      </p>
      <p className="mt-0.5 truncate text-[13px] font-semibold text-text-strong">
        {placeName}
      </p>

      <dl className="mt-2 grid grid-cols-2 gap-x-2 gap-y-1.5 text-[11px]">
        <div>
          <dt className="text-text-soft">Weather</dt>
          <dd className="font-medium text-text-strong">
            {c.weather ?? "—"}
          </dd>
        </div>
        <div>
          <dt className="text-text-soft">Temp</dt>
          <dd className="font-medium text-text-strong">
            {fmt(c.temp_c, "°C", 1)}
          </dd>
        </div>
        <div>
          <dt className="text-text-soft">Feels like</dt>
          <dd className="font-medium text-text-strong">
            {fmt(c.feels_like_c, "°C", 1)}
          </dd>
        </div>
        <div>
          <dt className="text-text-soft">Humidity</dt>
          <dd className="font-medium text-text-strong">
            {fmt(c.humidity_pct, "%")}
          </dd>
        </div>
        <div>
          <dt className="text-text-soft">Wind</dt>
          <dd className="font-medium text-text-strong">
            {fmt(c.wind_kmh, " km/h", 0)}
          </dd>
        </div>
        <div>
          <dt className="text-text-soft">Elevation</dt>
          <dd className="font-medium text-text-strong">
            {fmt(brief.elevation_m, " m", 0)}
          </dd>
        </div>
      </dl>

      {day0 && (
        <p className="mt-2 border-t border-panel-border pt-2 text-[10.5px] leading-snug text-text-soft">
          Today: {fmt(day0.tmin, "°", 0)}–{fmt(day0.tmax, "°C", 0)}
          {day0.precip != null ? ` · precip ${fmt(day0.precip, " mm", 1)}` : ""}
        </p>
      )}

      {brief.land && (
        <p className="mt-1.5 text-[10.5px] leading-snug text-text-soft">
          Land: {brief.land.empty_count} empty parcel
          {brief.land.empty_count === 1 ? "" : "s"}
          {brief.land.kinds.length
            ? ` (${brief.land.kinds.slice(0, 3).join(", ")})`
            : ""}
        </p>
      )}

      <p className="mt-2 text-[9px] text-text-soft">
        {brief.source ?? "Open-Meteo"} · climate live for this pin
      </p>
    </aside>
  );
}
