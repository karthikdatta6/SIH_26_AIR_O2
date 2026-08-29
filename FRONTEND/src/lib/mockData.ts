import { STATIONS } from "./stations";
import { levelForNO2, levelForO3, worstLevel, type AqiLevel } from "./aqi";

// Deterministic seeded PRNG (mulberry32) keyed off station id + a salt,
// so mock values are stable across re-renders instead of jumping around.
function hashSeed(str: string): number {
  let h = 1779033703 ^ str.length;
  for (let i = 0; i < str.length; i++) {
    h = Math.imul(h ^ str.charCodeAt(i), 3432918353);
    h = (h << 13) | (h >>> 19);
  }
  return h >>> 0;
}

function mulberry32(seed: number) {
  let a = seed;
  return function () {
    a |= 0;
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function rngFor(stationId: string, salt: string) {
  return mulberry32(hashSeed(stationId + "::" + salt));
}

export type StationStatus = "ONLINE" | "DEGRADED" | "OFFLINE";

export interface CurrentReading {
  // number | null: mock data always supplies a real number, but a live
  // reading can genuinely be missing for one pollutant (e.g. a CPCB
  // sensor gap) — null must stay distinct from a real 0 all the way to
  // display, never silently coerced.
  pm25: number | null;
  pm10: number | null;
  no2: number | null;
  o3: number | null;
  co: number | null;
  so2: number | null;
}

export interface StationDetails {
  elevationM: number;
  windDir: string;
  windKt: number;
  humidityPct: number;
}

// The Phase 3 model forecasts six direct horizons, not 48 continuous
// hourly points — see docs/PHASE_3_MODEL_ARCHITECTURE_REPORT.md.
export const FORECAST_HORIZONS_H = [1, 3, 6, 12, 24, 48] as const;

export interface ForecastPoint {
  hour: (typeof FORECAST_HORIZONS_H)[number]; // one of the six model horizons
  timestamp: string;
  no2: number;
  o3: number;
  // Real held-out test RMSE at this horizon (models/{NO2,O3}/metadata.json)
  // — null for mock data (no real model backing it) or if genuinely
  // unavailable, never a guessed number.
  no2Rmse: number | null;
  o3Rmse: number | null;
}

export interface HistoryPoint {
  hoursAgo: number; // 47..0
  timestamp: string;
  no2: number;
  o3: number;
}

const WIND_DIRS = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"];

export function stationStatus(stationId: string): StationStatus {
  const r = rngFor(stationId, "status")();
  if (r > 0.94) return "OFFLINE";
  if (r > 0.82) return "DEGRADED";
  return "ONLINE";
}

export function currentReading(stationId: string): CurrentReading {
  const r = rngFor(stationId, "current");
  return {
    pm25: 30 + r() * 140,
    pm10: 60 + r() * 220,
    no2: 15 + r() * 150,
    o3: 20 + r() * 110,
    co: 0.4 + r() * 3.2,
    so2: 4 + r() * 40,
  };
}

export function stationDetails(stationId: string): StationDetails {
  const r = rngFor(stationId, "details");
  return {
    elevationM: Math.round(210 + r() * 60),
    windDir: WIND_DIRS[Math.floor(r() * WIND_DIRS.length)],
    windKt: Math.round(2 + r() * 16),
    humidityPct: Math.round(25 + r() * 55),
  };
}

export function forecastSeries(stationId: string): ForecastPoint[] {
  const r = rngFor(stationId, "forecast");
  const base = currentReading(stationId);
  // currentReading()'s mock implementation always fills every field with
  // a real number — the null case CurrentReading allows for is only for
  // real API data, which this mock-only function never touches. Asserted
  // once here rather than defaulted, so it stays honest about why this
  // is safe instead of implying null is a real possibility.
  const baseNo2 = base.no2!;
  const baseO3 = base.o3!;
  const now = Date.now();
  const horizonSet = new Set<number>(FORECAST_HORIZONS_H);
  const points: ForecastPoint[] = [];
  let no2 = baseNo2;
  let o3 = baseO3;
  // Simulate hour-by-hour so the trajectory feeding each horizon looks
  // continuous, but only the six model horizons are ever exposed below —
  // the real model does not produce the 42 hours in between.
  for (let h = 1; h <= 48; h++) {
    const hourOfDay = new Date(now + h * 3600_000).getUTCHours();
    // Rough diurnal shape: NO2 peaks with traffic (morning/evening), O3 peaks midday.
    const no2Diurnal = 1 + 0.35 * Math.sin(((hourOfDay - 8) / 24) * Math.PI * 2);
    const o3Diurnal = 1 + 0.5 * Math.sin(((hourOfDay - 14) / 24) * Math.PI * 2);
    no2 = Math.max(8, no2 * 0.85 + baseNo2 * no2Diurnal * 0.15 + (r() - 0.5) * 6);
    o3 = Math.max(5, o3 * 0.85 + baseO3 * o3Diurnal * 0.15 + (r() - 0.5) * 5);
    if (!horizonSet.has(h)) continue;
    points.push({
      hour: h as ForecastPoint["hour"],
      timestamp: new Date(now + h * 3600_000).toISOString(),
      no2: Math.round(no2 * 10) / 10,
      o3: Math.round(o3 * 10) / 10,
      no2Rmse: null, // mock data has no real model backing it
      o3Rmse: null,
    });
  }
  return points;
}

export function historySeries(stationId: string, hours = 48): HistoryPoint[] {
  const r = rngFor(stationId, "history");
  const base = currentReading(stationId);
  const now = Date.now();
  const points: HistoryPoint[] = [];
  // See forecastSeries() above for why this assertion is safe (mock-only,
  // currentReading() never actually returns null for these fields).
  let no2 = base.no2! * (0.8 + r() * 0.4);
  let o3 = base.o3! * (0.8 + r() * 0.4);
  for (let h = hours - 1; h >= 0; h--) {
    no2 = Math.max(8, no2 * 0.9 + (r() - 0.5) * 14);
    o3 = Math.max(5, o3 * 0.9 + (r() - 0.5) * 12);
    points.push({
      hoursAgo: h,
      timestamp: new Date(now - h * 3600_000).toISOString(),
      no2: Math.round(no2 * 10) / 10,
      o3: Math.round(o3 * 10) / 10,
    });
  }
  return points;
}

export function overallLevel(stationId: string): AqiLevel {
  const c = currentReading(stationId);
  // worstLevel() only returns null when every input is null — c.no2/c.o3
  // are mock-generated real numbers here, never null, so this can't
  // actually happen; asserted rather than defaulted to keep that honest.
  return worstLevel([levelForNO2(c.no2), levelForO3(c.o3)])!;
}

export const ALL_STATION_SUMMARIES = STATIONS.map((s) => ({
  station: s,
  status: stationStatus(s.id),
  level: overallLevel(s.id),
  reading: currentReading(s.id),
}));
