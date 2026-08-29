interface Series {
  name: string;
  color: string;
  values: number[];
  // Optional uncertainty band (e.g. prediction ± real held-out test RMSE
  // at each horizon) — same length as values, or omitted where unknown
  // (element is null). Rendered as a shaded region around the line, not
  // a fabricated confidence interval — see ForecastPanel.tsx for where
  // this comes from.
  band?: { lower: (number | null)[]; upper: (number | null)[] };
}

interface Props {
  series: Series[];
  xLabels: string[];
  height?: number;
  unit?: string;
}

function pathFor(values: number[], width: number, height: number, min: number, max: number): string {
  if (values.length < 2) return "";
  const step = width / (values.length - 1);
  const norm = (v: number) => height - ((v - min) / (max - min || 1)) * height;
  return values.map((v, i) => `${i === 0 ? "M" : "L"} ${i * step} ${norm(v).toFixed(1)}`).join(" ");
}

// Closed polygon: upper bound left-to-right, then lower bound right-to-
// left, so the fill covers the whole band. Points with a null bound are
// skipped — the band just doesn't extend to unknown horizons instead of
// guessing a width for them.
function bandPathFor(
  band: { lower: (number | null)[]; upper: (number | null)[] },
  width: number,
  height: number,
  min: number,
  max: number
): string {
  const n = band.upper.length;
  const step = width / (n - 1 || 1);
  const norm = (v: number) => height - ((v - min) / (max - min || 1)) * height;
  const upperPts: string[] = [];
  const lowerPts: string[] = [];
  for (let i = 0; i < n; i++) {
    if (band.upper[i] === null || band.lower[i] === null) continue;
    upperPts.push(`${i * step} ${norm(band.upper[i] as number).toFixed(1)}`);
    lowerPts.push(`${i * step} ${norm(band.lower[i] as number).toFixed(1)}`);
  }
  if (upperPts.length === 0) return "";
  return `M ${upperPts.join(" L ")} L ${lowerPts.reverse().join(" L ")} Z`;
}

export function TrendChart({ series, xLabels, height = 220, unit = "" }: Props) {
  const width = 1000;
  const bandValues = series.flatMap((s) =>
    s.band ? [...s.band.lower, ...s.band.upper].filter((v): v is number => v !== null) : []
  );
  const all = [...series.flatMap((s) => s.values), ...bandValues];
  const min = Math.min(...all) * 0.9;
  const max = Math.max(...all) * 1.1;
  const gridLines = 4;

  return (
    <div className="border border-border p-6">
      <div className="mb-4 flex flex-wrap items-center gap-6">
        {series.map((s) => (
          <span key={s.name} className="flex items-center gap-2 text-xs tracking-widest text-ink-dim">
            <span className="h-2 w-2" style={{ background: s.color }} />
            {s.name} {unit}
          </span>
        ))}
      </div>
      <svg viewBox={`0 0 ${width} ${height}`} className="w-full overflow-visible" preserveAspectRatio="none">
        {Array.from({ length: gridLines + 1 }, (_, i) => (
          <line
            key={i}
            x1={0}
            x2={width}
            y1={(height / gridLines) * i}
            y2={(height / gridLines) * i}
            stroke="var(--color-border-faint)"
            strokeWidth={1}
          />
        ))}
        {series.map(
          (s) =>
            s.band && (
              <path
                key={`${s.name}-band`}
                d={bandPathFor(s.band, width, height, min, max)}
                fill={s.color}
                fillOpacity={0.15}
                stroke="none"
              />
            )
        )}
        {series.map((s) => (
          <path
            key={s.name}
            d={pathFor(s.values, width, height, min, max)}
            fill="none"
            stroke={s.color}
            strokeWidth={2.5}
            vectorEffect="non-scaling-stroke"
          />
        ))}
      </svg>
      <div className="mt-3 flex justify-between text-[12px] tracking-widest text-ink-dim">
        {xLabels.map((l, i) => (
          <span key={i}>{l}</span>
        ))}
      </div>
    </div>
  );
}
