"use client";

import type { StrainClass } from "@/lib/types";

const CLASS_STYLE: Record<
  StrainClass,
  { colour: string; glow: string; verdict: string }
> = {
  STABLE: { colour: "#35c28f", glow: "#35c28f66", verdict: "STABLE (OPTIMIZED)" },
  ELEVATED: { colour: "#f5a623", glow: "#f5a62366", verdict: "ELEVATED (WATCH)" },
  CRITICAL: { colour: "#e5484d", glow: "#e5484d88", verdict: "CRITICAL (ALERT)" },
};

interface StrainGaugeProps {
  ratio: number; // 0..1+ of feeder capacity proxy
  strainClass: StrainClass;
  peakKw: number;
}

export function StrainGauge({ ratio, strainClass, peakKw }: StrainGaugeProps) {
  const style = CLASS_STYLE[strainClass];
  const fraction = Math.min(1, ratio);
  // Arc from 180 to 0 degrees (half circle), radius 70, centre (90, 86).
  const sweep = 180 * fraction;
  const end = polar(90, 86, 70, 180 - sweep);

  return (
    <div className="flex flex-col items-center">
      <svg width="180" height="102" viewBox="0 0 180 102" aria-hidden="true">
        <path
          d={arcPath(90, 86, 70, 180, 0)}
          fill="none"
          stroke="#ffffff33"
          strokeWidth="14"
          strokeLinecap="round"
        />
        <path
          d={arcPath(90, 86, 70, 180, 180 - sweep)}
          fill="none"
          stroke={style.colour}
          strokeWidth="14"
          strokeLinecap="round"
          style={{ filter: `drop-shadow(0 0 8px ${style.glow})` }}
        />
        <circle cx={end.x} cy={end.y} r="4" fill="#ffffff" />
        <text
          x="90"
          y="80"
          textAnchor="middle"
          fill="#ffffff"
          fontSize="19"
          fontWeight="700"
        >
          {peakKw.toLocaleString("en-CA", { maximumFractionDigits: 0 })} kW
        </text>
        <text x="90" y="97" textAnchor="middle" fill="#ffffffaa" fontSize="9">
          {(ratio * 100).toFixed(0)}% of feeder proxy
        </text>
      </svg>
      <p className="mt-1 text-[13px] font-semibold text-white">
        PEAK GRID STRAIN:{" "}
        <span style={{ color: style.colour }}>{style.verdict}</span>
      </p>
    </div>
  );
}

function polar(cx: number, cy: number, r: number, angleDeg: number) {
  const rad = (angleDeg * Math.PI) / 180;
  return { x: cx + r * Math.cos(rad), y: cy - r * Math.sin(rad) };
}

function arcPath(
  cx: number,
  cy: number,
  r: number,
  startDeg: number,
  endDeg: number,
) {
  const start = polar(cx, cy, r, startDeg);
  const end = polar(cx, cy, r, endDeg);
  const large = Math.abs(startDeg - endDeg) > 180 ? 1 : 0;
  return `M ${start.x} ${start.y} A ${r} ${r} 0 ${large} 1 ${end.x} ${end.y}`;
}
