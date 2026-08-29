import { TrendChart } from "../common/TrendChart";
import type { HistoryPoint } from "../../lib/mockData";

export function HistoryPanel({ points }: { points: HistoryPoint[] }) {
  const sampled = points.filter((_, i) => i % 6 === 0 || i === points.length - 1);
  return (
    <TrendChart
      unit="(µg/m³)"
      series={[
        { name: "NO₂ OBSERVED", color: "var(--color-amber-500)", values: points.map((p) => p.no2) },
        { name: "O₃ OBSERVED", color: "var(--color-usg)", values: points.map((p) => p.o3) },
      ]}
      xLabels={sampled.map((p) => (p.hoursAgo === 0 ? "NOW" : `-${p.hoursAgo}H`))}
    />
  );
}
