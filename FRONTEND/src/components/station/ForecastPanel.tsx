import { TrendChart } from "../common/TrendChart";
import type { ForecastPoint } from "../../lib/mockData";

// ±RMSE band around each prediction — the model's real held-out test
// error at that horizon (models/{NO2,O3}/metadata.json), not a fabricated
// confidence interval. null RMSE (mock data, or a horizon with no stored
// metric) means no band is drawn for that point, not a guessed width.
function bandFor(values: number[], rmses: (number | null)[]) {
  return {
    lower: values.map((v, i) => (rmses[i] === null ? null : v - (rmses[i] as number))),
    upper: values.map((v, i) => (rmses[i] === null ? null : v + (rmses[i] as number))),
  };
}

export function ForecastPanel({ points }: { points: ForecastPoint[] }) {
  const hasRealRmse = points.some((p) => p.no2Rmse !== null || p.o3Rmse !== null);
  return (
    <div>
      <TrendChart
        unit="(µg/m³)"
        series={[
          {
            name: "NO₂ FORECAST",
            color: "var(--color-amber-500)",
            values: points.map((p) => p.no2),
            band: bandFor(points.map((p) => p.no2), points.map((p) => p.no2Rmse)),
          },
          {
            name: "O₃ FORECAST",
            color: "var(--color-usg)",
            values: points.map((p) => p.o3),
            band: bandFor(points.map((p) => p.o3), points.map((p) => p.o3Rmse)),
          },
        ]}
        xLabels={points.map((p) => `+${p.hour}H`)}
      />
      {hasRealRmse && (
        <p className="mt-3 text-[11px] leading-relaxed text-ink-dim">
          Shaded band = ±the model&apos;s real held-out test RMSE at that horizon, not a fabricated
          confidence score — this model has no calibrated probability output, so this reports actual
          historical prediction error instead of inventing one.
        </p>
      )}
    </div>
  );
}
