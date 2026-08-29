import { LEVEL_COLOR, LEVEL_LABEL, type AqiLevel } from "../../lib/aqi";

export function StatusPill({ level }: { level: AqiLevel | null }) {
  // null = no reading right now (e.g. a real CPCB sensor gap) — a distinct
  // neutral state, never a colored AQI band standing in for "unknown".
  if (level === null) {
    return (
      <span
        className="inline-flex items-center border px-2 py-0.5 text-[13px] tracking-widest font-semibold uppercase text-ink-dim"
        style={{ borderColor: "var(--color-border)" }}
      >
        N/A
      </span>
    );
  }
  const color = LEVEL_COLOR[level];
  return (
    <span
      className="inline-flex items-center border px-2 py-0.5 text-[13px] tracking-widest font-semibold uppercase"
      style={{ color, borderColor: color }}
    >
      {LEVEL_LABEL[level]}
    </span>
  );
}
