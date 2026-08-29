import { StatusPill } from "../common/StatusPill";
import { LEVEL_COLOR, type AqiLevel } from "../../lib/aqi";

export interface QuickScanRow {
  compound: string;
  value: number | null;
  unit: string;
  level: AqiLevel | null;
}

export function QuickScanTable({ rows }: { rows: QuickScanRow[] }) {
  return (
    <div className="border border-border">
      <div className="grid grid-cols-[1fr_1fr_1fr_1fr] border-b border-border bg-panel px-6 py-3 text-xs tracking-[0.2em] text-ink-dim">
        <span>CPND</span>
        <span>VALUE</span>
        <span className="hidden sm:block">UNIT</span>
        <span className="text-right">STS</span>
      </div>
      {rows.map((row, i) => (
        <div
          key={row.compound}
          className="grid grid-cols-[1fr_1fr_1fr_1fr] items-center px-6 py-4"
          style={{ borderBottom: i < rows.length - 1 ? "1px solid var(--color-border-faint)" : "none" }}
        >
          <span className="text-sm text-ink">{row.compound}</span>
          <span
            className="text-lg font-bold tabular-nums"
            style={{ color: row.level === null ? "var(--color-ink-dim)" : LEVEL_COLOR[row.level] }}
          >
            {row.value === null ? "N/A" : row.value.toFixed(1)}
          </span>
          <span className="hidden text-sm text-ink-dim sm:block">{row.unit}</span>
          <span className="flex justify-end">
            <StatusPill level={row.level} />
          </span>
        </div>
      ))}
    </div>
  );
}
