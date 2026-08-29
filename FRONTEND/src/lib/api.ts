// Typed client for the Phase 4 backend. Only used when
// import.meta.env.VITE_USE_REAL_API === "true" — see StationDashboard.tsx.
// Base URL defaults to the local dev backend (uvicorn on :8000).

const API_BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export function useRealApi(): boolean {
  return import.meta.env.VITE_USE_REAL_API === "true";
}

async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    const message = body?.error?.message ?? res.statusText;
    throw new Error(`API ${res.status}: ${message}`);
  }
  return res.json() as Promise<T>;
}

export interface ApiStation {
  station_id: string;
  name: string;
  latitude: number;
  longitude: number;
  zone: string;
  elevation_m: number | null;
  active: boolean;
}

interface PollutantReading {
  value: number | null;
  unit: string;
}

export interface ApiStationCurrent {
  station_id: string;
  observation_timestamp: string | null;
  data_mode: string;
  is_live: boolean;
  source: string | null;
  pm25: PollutantReading;
  pm10: PollutantReading;
  no2: PollutantReading;
  o3: PollutantReading;
  co: PollutantReading;
  so2: PollutantReading;
  humidity_pct: number | null;
  wind_speed: number | null;
  wind_direction: number | null;
}

interface ApiHistoryPoint {
  timestamp: string;
  no2: number | null;
  o3: number | null;
  data_mode: string;
  source: string;
}

export interface ApiHistory {
  station_id: string;
  data_mode: string;
  is_live: boolean;
  points: ApiHistoryPoint[];
}

interface ApiForecastPoint {
  horizon_hours: 1 | 3 | 6 | 12 | 24 | 48;
  target_timestamp: string;
  prediction: number;
  unit: string;
  rmse: number | null;
}

export interface ApiForecast {
  station_id: string;
  generated_at: string;
  reference_observation_timestamp: string;
  data_mode: string;
  is_live: boolean;
  forecasts: { NO2: ApiForecastPoint[]; O3: ApiForecastPoint[] };
}

export interface ApiStationsCurrent {
  generated_at: string;
  stations: ApiStationCurrent[];
}

export function fetchStation(stationId: string) {
  return getJson<ApiStation>(`/api/v1/stations/${stationId}`);
}

export function fetchStationsCurrent() {
  return getJson<ApiStationsCurrent>(`/api/v1/stations/current`);
}

export function fetchStationCurrent(stationId: string) {
  return getJson<ApiStationCurrent>(`/api/v1/stations/${stationId}/current`);
}

export function fetchStationHistory(stationId: string, hours = 48) {
  return getJson<ApiHistory>(`/api/v1/stations/${stationId}/history?hours=${hours}`);
}

export function fetchStationForecast(stationId: string) {
  return getJson<ApiForecast>(`/api/v1/stations/${stationId}/forecast`);
}

const COMPASS = [
  "N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
  "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW",
];

export function degreesToCompass(deg: number | null): string {
  if (deg === null) return "—";
  return COMPASS[Math.round(deg / 22.5) % 16];
}

export interface StationBundle {
  station: ApiStation;
  current: ApiStationCurrent;
  history: ApiHistory;
  forecast: ApiForecast;
}

export async function fetchStationBundle(stationId: string): Promise<StationBundle> {
  const [station, current, history, forecast] = await Promise.all([
    fetchStation(stationId),
    fetchStationCurrent(stationId),
    fetchStationHistory(stationId),
    fetchStationForecast(stationId),
  ]);
  return { station, current, history, forecast };
}
