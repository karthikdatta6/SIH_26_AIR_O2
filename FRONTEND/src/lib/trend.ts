export interface Trend {
  vsPreviousHourPct: number | null;
  vs24hAvgPct: number | null;
}

const NO_TREND: Trend = { vsPreviousHourPct: null, vs24hAvgPct: null };

// "vs previous hour" and "vs 24h average", computed from real history
// points — never from a single hardcoded lag, and never fabricated when
// there isn't enough real trailing data (returns null instead of a
// guessed percentage).
export function computeTrend(
  currentValue: number | null,
  currentTs: string | null,
  history: { timestamp: string; value: number | null }[]
): Trend {
  if (currentValue === null || !currentTs) return NO_TREND;
  const currentTime = new Date(currentTs).getTime();
  const withValues = history.filter(
    (h): h is { timestamp: string; value: number } => h.value !== null
  );

  // Closest real point to exactly 1 hour before the current reading —
  // only trusted if it's within 45 minutes of that mark, so a 15-minute-
  // granularity gap doesn't get silently treated as "the previous hour".
  let prevHourValue: number | null = null;
  let bestDiffMs = Infinity;
  const targetMs = currentTime - 60 * 60 * 1000;
  for (const h of withValues) {
    const diff = Math.abs(new Date(h.timestamp).getTime() - targetMs);
    if (diff < bestDiffMs) {
      bestDiffMs = diff;
      prevHourValue = h.value;
    }
  }
  const vsPreviousHourPct =
    prevHourValue !== null && bestDiffMs <= 45 * 60 * 1000 && prevHourValue !== 0
      ? ((currentValue - prevHourValue) / prevHourValue) * 100
      : null;

  // Mean of real points within the 24h before the current reading.
  const dayAgoMs = currentTime - 24 * 60 * 60 * 1000;
  const last24h = withValues.filter((h) => {
    const t = new Date(h.timestamp).getTime();
    return t >= dayAgoMs && t <= currentTime;
  });
  const avg24h =
    last24h.length > 0 ? last24h.reduce((sum, h) => sum + h.value, 0) / last24h.length : null;
  const vs24hAvgPct =
    avg24h !== null && avg24h !== 0 ? ((currentValue - avg24h) / avg24h) * 100 : null;

  return { vsPreviousHourPct, vs24hAvgPct };
}
