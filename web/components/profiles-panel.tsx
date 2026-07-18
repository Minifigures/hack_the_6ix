"use client";

import Image from "next/image";
import { useEffect, useState } from "react";
import { fetchProfiles } from "@/lib/api";
import { LoadChart } from "@/components/load-chart";
import type { BuildingType, LoadProfileInfo } from "@/lib/types";

interface ProfilesPanelProps {
  buildingType: BuildingType;
  onClose: () => void;
}

export function ProfilesPanel({ buildingType, onClose }: ProfilesPanelProps) {
  const [profiles, setProfiles] = useState<Record<string, LoadProfileInfo> | null>(
    null,
  );
  const [selected, setSelected] = useState<BuildingType>(buildingType);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchProfiles()
      .then(setProfiles)
      .catch(() => setError("Profile service unavailable"));
  }, []);

  const profile = profiles?.[selected];

  return (
    <div className="pointer-events-auto absolute inset-0 z-20 overflow-y-auto bg-[#0b1420]/92 p-5 backdrop-blur-sm">
      <div className="mx-auto max-w-4xl">
        <div className="mb-3 flex items-center justify-between">
          <div>
            <h2 className="text-[17px] font-semibold text-white">
              Energy Load Profiles
            </h2>
            <p className="text-[12px] text-white/60">
              Hospitality-specific benchmarking: occupancy-driven shapes, not
              generic commercial curves. Sources footnoted in the memo.
            </p>
          </div>
          <button
            onClick={onClose}
            className="rounded border border-white/25 px-3 py-1.5 text-[12px] font-semibold text-white hover:bg-white/10"
          >
            Close
          </button>
        </div>

        <div className="mb-3 flex gap-2">
          {profiles &&
            (Object.keys(profiles) as BuildingType[]).map((key) => (
              <button
                key={key}
                onClick={() => setSelected(key)}
                className={`rounded border px-3 py-1.5 text-[12px] font-medium ${
                  selected === key
                    ? "border-accent bg-accent/15 text-accent"
                    : "border-white/20 text-white/70 hover:bg-white/10"
                }`}
              >
                {profiles[key].label}
                <span className="ml-1.5 text-[10px] opacity-70">
                  {profiles[key].character}
                </span>
              </button>
            ))}
        </div>

        {error && <p className="text-[13px] text-alert">{error}</p>}

        {profile && (
          <LoadChart
            title={`${profile.label}: normalized 24h shape (${profile.character}), mean = 1.0`}
            colour="#f5c518"
            series={profile.hourly_shape.map((kw, hour) => ({ hour, kw }))}
            height={220}
          />
        )}

        <div className="mt-4 rounded border border-[#1a3a57] bg-chart-navy p-3">
          <p className="mb-2 text-[12px] font-semibold text-white/90">
            Validation: our generated curve vs a published metered hotel
          </p>
          <Image
            src="/validation.png"
            alt="Generated tower load curve overlaid on the metered full-service hotel curve from Placet et al. 2010; both trough overnight at 45-70 percent of peak"
            width={1290}
            height={690}
            className="h-auto w-full rounded"
            unoptimized
          />
          <p className="mt-2 text-[10.5px] leading-snug text-white/50">
            Published curve: Placet et al. 2010, ACEEE Summer Study, metered
            300-room full-service hotel (approximate trace of Figure 2; base
            400 kW and peak cooling 200 kW are text-stated). Our 200-room tower
            curve holds its night trough inside the published 44-67 percent
            band.
          </p>
        </div>
      </div>
    </div>
  );
}
