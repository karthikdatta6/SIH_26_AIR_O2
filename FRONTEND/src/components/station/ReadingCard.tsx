import { SegmentBar } from "../common/SegmentBar";
import { StatusPill } from "../common/StatusPill";
import { LEVEL_COLOR, type AqiLevel } from "../../lib/aqi";
import type { Trend } from "../../lib/trend";

interface Props {
  label: string;
  value: number | null;
  unit: string;
  limit: number;
  level: AqiLevel | null;
  emphasize?: boolean;
  // Real trailing-data trend context (see lib/trend.ts) — undefined for
  // pollutants with no history API to compute it from (PM2.5/PM10/CO/SO2
  // currently), not shown rather than guessed.
  trend?: Trend;
}

function TrendLine({ trend }: { trend: Trend }) {
  // Lower pollution is always better, regardless of which pollutant —
  // an increase is shown in the "unhealthy" red tone, a decrease in the
  // "good" green tone, independent of the card's own AQI-level color.
  const pct = trend.vsPreviousHourPct;
  if (pct === null) return null;
  const rounded = Math.round(Math.abs(pct));
  if (rounded === 0) {
    return <div className="mt-2 text-[12px] tracking-wide text-ink-dim">→ steady vs previous hour</div>;
  }
  const up = pct > 0;
  return (
    <div
      className="mt-2 text-[12px] tracking-wide"
      style={{ color: up ? "var(--color-unhealthy)" : "var(--color-good)" }}
    >
      {up ? "↑" : "↓"} {rounded}% vs previous hour
    </div>
  );
}

export function ReadingCard({ label, value, unit, limit, level, emphasize, trend }: Props) {
  // null = no reading right now — shown as "N/A", never as a fabricated
  // "0" (which would misleadingly read as the best possible air quality).
  const color = level === null ? "var(--color-ink-dim)" : LEVEL_COLOR[level];
  return (
    <div
      className="border p-6"
      style={{ borderColor: emphasize ? "var(--color-border-strong)" : "var(--color-border)" }}
    >
      <div className="mb-4 flex items-center justify-between">
        <span className="text-xs tracking-[0.2em] text-ink-dim">{label}</span>
        <StatusPill level={level} />
      </div>
      <div className="mb-4 flex items-baseline gap-2">
        <span className="text-4xl font-bold tabular-nums" style={{ color: value === null ? "var(--color-ink-dim)" : emphasize ? color : "var(--color-ink-bright)" }}>
          {value === null ? "N/A" : value.toFixed(1)}
        </span>
        {value !== null && <span className="text-sm text-ink-dim">{unit}</span>}
      </div>
      <SegmentBar fraction={value === null ? 0 : value / limit} color={color} />
      <div className="mt-2 flex justify-between text-[13px] text-ink-dim">
        <span>0</span>
        <span>LIMIT {limit}</span>
      </div>
      {trend && <TrendLine trend={trend} />}
    </div>
  );
}
