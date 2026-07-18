"use client";

import { LogGlyph } from "@/components/component-icons";
import type { LogEntry } from "@/lib/build-config";

interface PhysicsLogProps {
  entries: LogEntry[];
  runtimeLines: string[];
}

export function PhysicsLog({ entries, runtimeLines }: PhysicsLogProps) {
  return (
    <aside className="flex w-72 shrink-0 flex-col border-l border-panel-border bg-panel">
      <div className="border-b border-panel-border px-4 py-3">
        <p className="text-[10px] font-semibold uppercase tracking-wider text-text-soft">
          Activity
        </p>
        <h2 className="text-[14px] font-semibold text-text-strong">
          Structure log
        </h2>
      </div>
      <div className="flex-1 overflow-y-auto">
        {entries.length === 0 && runtimeLines.length === 0 && (
          <p className="px-4 py-6 text-center text-[12px] text-text-soft">
            Place a building to see structure notes here.
          </p>
        )}
        {entries.map((entry, i) => (
          <div key={i} className="border-b border-panel-border px-4 py-3">
            <p
              className={`text-[12.5px] leading-snug ${
                entry.kind === "warning"
                  ? "font-medium text-[#A35A52]"
                  : "text-text-strong"
              }`}
            >
              {entry.kind === "warning" ? "Warning: " : ""}
              {entry.text}
            </p>
            <div className="mt-1.5 flex items-center gap-2 text-text-soft">
              <LogGlyph icon={entry.icon} />
              <LogGlyph icon={entry.kind === "warning" ? "shear" : "bolt"} />
            </div>
          </div>
        ))}
        {runtimeLines.length > 0 && (
          <div className="px-4 py-3">
            <p className="mb-2 text-[10px] font-semibold uppercase tracking-wider text-text-soft">
              Engine
            </p>
            <ul className="space-y-2">
              {runtimeLines.map((line, i) => (
                <li
                  key={i}
                  className="rounded-md bg-panel-muted px-2.5 py-2 text-[12px] leading-snug text-text-strong"
                >
                  {line}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </aside>
  );
}
