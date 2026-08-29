import { useEffect, useState } from "react";
import { Link, Navigate, useParams } from "react-router-dom";
import { Topbar } from "../layout/Topbar";
import { Footer } from "../layout/Footer";
import { Ticker } from "../layout/Ticker";
import { SectionHeader, SectionTitle } from "../common/SectionHeader";
import { StatusPill } from "../common/StatusPill";
import { TypewriterText } from "../common/TypewriterText";
import { ScrambleText } from "../common/ScrambleText";
import { ReadingCard } from "./ReadingCard";
import { QuickScanTable, type QuickScanRow } from "./QuickScanTable";
import { ForecastPanel } from "./ForecastPanel";
import { HistoryPanel } from "./HistoryPanel";
import { getStation } from "../../lib/stations";
import {
  currentReading,
  stationDetails,
  stationStatus,
  forecastSeries,
  historySeries,
  overallLevel,
  type CurrentReading,
  type ForecastPoint,
  type HistoryPoint,
  type StationDetails,
  type StationStatus,
} from "../../lib/mockData";
import { levelForNO2, levelForO3, levelForPM25, levelForPM10, levelForCO, levelForSO2, worstLevel, LEVEL_COLOR, type AqiLevel } from "../../lib/aqi";
import { ALERT_COPY } from "../../lib/alerts";
import { isoNowUtc } from "../common/LiveClock";
import { formatIst } from "../../lib/time";
import { computeTrend } from "../../lib/trend";
import {
  useRealApi,
  fetchStationBundle,
  degreesToCompass,
  type StationBundle,
} from "../../lib/api";

function bundleToViewModel(bundle: StationBundle) {
  const c = bundle.current;
  // Pass nulls through as-is — a genuinely missing reading (e.g. a real
  // CPCB sensor gap) must never be silently coerced to 0, which would
  // render as the best possible air-quality band instead of "unavailable".
  const reading: CurrentReading = {
    pm25: c.pm25.value,
    pm10: c.pm10.value,
    no2: c.no2.value,
    o3: c.o3.value,
    co: c.co.value,
    so2: c.so2.value,
  };
  const round1 = (n: number | null) => (n === null ? NaN : Math.round(n * 10) / 10);
  const details: StationDetails = {
    elevationM: bundle.station.elevation_m ?? NaN,
    windDir: degreesToCompass(c.wind_direction),
    windKt: round1(c.wind_speed),
    humidityPct: round1(c.humidity_pct),
  };

  const byHorizon = new Map<
    number,
    { no2?: number; o3?: number; ts?: string; no2Rmse?: number | null; o3Rmse?: number | null }
  >();
  for (const p of bundle.forecast.forecasts.NO2) {
    byHorizon.set(p.horizon_hours, {
      ...byHorizon.get(p.horizon_hours),
      no2: p.prediction,
      ts: p.target_timestamp,
      no2Rmse: p.rmse,
    });
  }
  for (const p of bundle.forecast.forecasts.O3) {
    byHorizon.set(p.horizon_hours, {
      ...byHorizon.get(p.horizon_hours),
      o3: p.prediction,
      ts: p.target_timestamp,
      o3Rmse: p.rmse,
    });
  }
  const forecast: ForecastPoint[] = [...byHorizon.entries()]
    .sort(([a], [b]) => a - b)
    .map(([hour, v]) => ({
      hour: hour as ForecastPoint["hour"],
      timestamp: v.ts ?? bundle.forecast.generated_at,
      no2: v.no2 ?? 0,
      o3: v.o3 ?? 0,
      no2Rmse: v.no2Rmse ?? null,
      o3Rmse: v.o3Rmse ?? null,
    }));

  const historyPoints = bundle.history.points;
  const lastTs = historyPoints.length
    ? new Date(historyPoints[historyPoints.length - 1].timestamp).getTime()
    : Date.now();
  const history: HistoryPoint[] = historyPoints.map((p) => ({
    hoursAgo: Math.round((lastTs - new Date(p.timestamp).getTime()) / 3_600_000),
    timestamp: p.timestamp,
    no2: p.no2 ?? 0,
    o3: p.o3 ?? 0,
  }));

  const level = worstLevel([levelForNO2(reading.no2), levelForO3(reading.o3)]);

  return { reading, details, level, forecast, history };
}

// Each detail row's scramble starts once the previous row is halfway
// resolved — a cascading waterfall where row 1 finishes first, then row 2,
// and so on — rather than all four decoding in lockstep.
const SCRAMBLE_DURATION_MS = 900;
const SCRAMBLE_STAGGER_MS = SCRAMBLE_DURATION_MS / 2;

export function StationDashboard() {
  const { stationId } = useParams<{ stationId: string }>();
  const station = stationId ? getStation(stationId) : undefined;
  const realApi = useRealApi();
  // 0 = name typing, 1 = name done (status + alert revealing), 2 = alert
  // done (lat/lon/elevation/wind/humidity revealing + scrambling).
  const [stage, setStage] = useState(0);
  const [bundle, setBundle] = useState<StationBundle | null>(null);
  const [fetchError, setFetchError] = useState<string | null>(null);

  useEffect(() => {
    setStage(0);
  }, [stationId]);

  useEffect(() => {
    if (!realApi || !station) return;
    let cancelled = false;
    setBundle(null);
    setFetchError(null);
    fetchStationBundle(station.id)
      .then((b) => {
        if (!cancelled) setBundle(b);
      })
      .catch((err: Error) => {
        if (!cancelled) setFetchError(err.message);
      });
    return () => {
      cancelled = true;
    };
  }, [realApi, station]);

  if (!station) return <Navigate to="/network" replace />;

  if (realApi && fetchError) {
    return (
      <div className="flex min-h-screen flex-col bg-bg">
        <Topbar />
        <main className="mx-auto w-full max-w-[1200px] flex-1 px-6 py-10 text-ink-dim">
          <Link to="/network" className="mb-8 inline-block text-xs tracking-widest hover:text-amber-300">
            ← BACK TO NETWORK
          </Link>
          <p className="text-sm">Failed to load live backend data for {station.name}: {fetchError}</p>
        </main>
        <Footer />
      </div>
    );
  }

  if (realApi && !bundle) {
    return (
      <div className="flex min-h-screen flex-col bg-bg">
        <Topbar />
        <main className="mx-auto w-full max-w-[1200px] flex-1 px-6 py-10 text-ink-dim">
          <p className="text-sm">Loading {station.name} from the backend…</p>
        </main>
        <Footer />
      </div>
    );
  }

  const viewModel = realApi && bundle ? bundleToViewModel(bundle) : null;
  const reading = viewModel?.reading ?? currentReading(station.id);
  const details = viewModel?.details ?? stationDetails(station.id);
  const status: StationStatus | null = viewModel ? null : stationStatus(station.id);
  // When we have a real viewModel (live/historical API mode), its level is
  // authoritative even when null (both NO2 and O3 genuinely missing) —
  // must NOT fall back to mock data in that case, only mock mode (no
  // viewModel at all) uses the mock overallLevel().
  const level: AqiLevel | null = viewModel ? viewModel.level : overallLevel(station.id);
  const alert = level === null ? null : ALERT_COPY[level];
  const forecast = viewModel?.forecast ?? forecastSeries(station.id);
  const history = viewModel?.history ?? historySeries(station.id);
  const isLive = bundle?.current.is_live ?? false;
  // Computed from the raw API history (real nulls preserved), not the
  // view-model's `history` array above (which coerces missing points to
  // 0 for chart rendering — wrong for trend math, since a fabricated 0
  // would produce a nonsense percentage). Undefined in mock mode, since
  // there's no real trailing data to compute a trend from.
  const no2Trend = bundle
    ? computeTrend(
        bundle.current.no2.value,
        bundle.current.observation_timestamp,
        bundle.history.points.map((p) => ({ timestamp: p.timestamp, value: p.no2 }))
      )
    : undefined;
  const o3Trend = bundle
    ? computeTrend(
        bundle.current.o3.value,
        bundle.current.observation_timestamp,
        bundle.history.points.map((p) => ({ timestamp: p.timestamp, value: p.o3 }))
      )
    : undefined;
  // Ground chemistry can come from two different live sources — a real
  // manually-exported CPCB reading (preferred, no accuracy caveat needed)
  // or CAMS's atmospheric-model estimate (fallback, real measured
  // accuracy gap — see docs/CAMS_ACCURACY_EVALUATION.md). Never show one
  // badge/caveat when the other source actually supplied the data.
  const isCpcbManual = bundle?.current.source === "CPCB_LIVE_MANUAL";
  // IST, not UTC: the underlying data (CPCB exports, and this app's whole
  // subject) is Delhi-local — showing IST avoids a mismatch against the
  // timestamps a viewer sees directly on a CPCB CCR export they uploaded.
  const observationTs = bundle?.current.observation_timestamp
    ? formatIst(bundle.current.observation_timestamp)
    : "UNAVAILABLE";
  const dataModeLabel = bundle
    ? isLive
      ? isCpcbManual
        ? `LIVE DATA — CPCB GROUND TRUTH (MANUAL EXPORT) · LAST OBSERVATION: ${observationTs}`
        : `LIVE DATA — CAMS-SOURCED GROUND CHEMISTRY · LAST OBSERVATION: ${observationTs}`
      : `${bundle.current.data_mode.toUpperCase()} DATA — LAST OBSERVATION: ${observationTs}`
    : null;

  // Real EPA breakpoint bands per pollutant (see lib/aqi.ts for the
  // source tables and unit conversions) — not the old arbitrary
  // approximations (PM2.5/PM10 reusing NO2 bands scaled by a made-up
  // factor, CO/SO2 using a single hand-picked threshold).
  const coLevel = levelForCO(reading.co);
  const so2Level = levelForSO2(reading.so2);
  const quickScan: QuickScanRow[] = [
    { compound: "PM2.5", value: reading.pm25, unit: "µg/m³", level: levelForPM25(reading.pm25) },
    { compound: "PM10", value: reading.pm10, unit: "µg/m³", level: levelForPM10(reading.pm10) },
    { compound: "NO₂", value: reading.no2, unit: "µg/m³", level: levelForNO2(reading.no2) },
    { compound: "O₃", value: reading.o3, unit: "µg/m³", level: levelForO3(reading.o3) },
    // Units corrected: CO is mg/m³ and SO2 is µg/m³ in this app's real
    // data (PHASE_3_ML_RESEARCHER_HANDOUT.md), not ppm/ppb as previously
    // (mis)labeled here.
    { compound: "CO", value: reading.co, unit: "mg/m³", level: coLevel },
    { compound: "SO₂", value: reading.so2, unit: "µg/m³", level: so2Level },
  ];

  return (
    <div className="flex min-h-screen flex-col bg-bg">
      <Topbar />

      <main className="mx-auto w-full max-w-[1200px] flex-1 px-6 py-10">
        <Link
          to="/network"
          className="mb-8 inline-block text-xs tracking-widest text-ink-dim hover:text-amber-300"
        >
          ← BACK TO NETWORK
        </Link>

        {/* Report header */}
        <div className="mb-4 flex flex-wrap items-baseline justify-between gap-2 border-b border-border pb-4 text-xs tracking-widest text-ink-dim">
          <span>
            NATIONAL AIR QUALITY MONITORING NETWORK — REPORT #F-{station.id.slice(0, 3)}-2026
          </span>
          {/* The record's own real observation time, not a live ticking
              clock — this report describes that specific record, not
              "right now". Only mock mode (no real bundle at all) falls
              back to the live clock, since there's no real record to show. */}
          <span>{bundle ? observationTs : isoNowUtc()}</span>
        </div>
        {dataModeLabel && (
          <div className={`flex flex-wrap items-center gap-2 ${isLive ? "mb-1" : "mb-4"}`}>
            {isLive && (
              <span className="flex items-center gap-1.5 border border-[var(--color-good)] px-2 py-0.5 text-[11px] font-bold tracking-widest text-[var(--color-good)]">
                <span className="h-1.5 w-1.5 animate-blink rounded-full bg-[var(--color-good)]" />
                LIVE
              </span>
            )}
            <span className={`text-xs tracking-widest ${isLive ? "text-[var(--color-good)]" : "text-amber-300"}`}>
              {dataModeLabel}
            </span>
          </div>
        )}
        {isLive && !isCpcbManual && (
          <div className="mb-4 max-w-2xl text-[11px] leading-relaxed text-ink-dim">
            NO₂/O₃ are estimated from CAMS atmospheric-model data (~10km resolution), not
            measured by a CPCB ground sensor — real-world comparison shows this can deviate
            substantially from true CPCB readings (see docs/CAMS_ACCURACY_EVALUATION.md).
          </div>
        )}

        <div className="mb-2 text-xs tracking-[0.25em] text-ink-dim">MONITORING STATION</div>
        <h1 className="mb-2 text-4xl font-bold tracking-wide text-ink-bright sm:text-5xl">
          <TypewriterText
            key={station.id}
            text={station.name.toUpperCase()}
            speedMs={32}
            onComplete={() => setStage((s) => (s < 1 ? 1 : s))}
          />
        </h1>

        {/* Status + alert box — revealed once the name finishes typing */}
        <div
          className={`transition-opacity duration-700 ${stage >= 1 ? "opacity-100" : "opacity-0"}`}
          onTransitionEnd={(e) => {
            if (e.target === e.currentTarget && stage === 1) setStage(2);
          }}
        >
          <div className="mb-8 flex flex-wrap items-center gap-3 text-sm text-ink-dim">
            <span>
              STATION {station.id} · {station.zone} ZONE
            </span>
            <StatusPill level={level} />
            {status && <span className="text-ink-dim">{status}</span>}
          </div>

          {/* Alert box — level/alert are null only when NO2 and O3 are both
              genuinely missing right now; shown as a neutral "no data"
              state rather than fabricating an alert from mock data. */}
          <div className="mb-8 border p-6" style={{ borderColor: level === null ? "var(--color-border)" : LEVEL_COLOR[level] }}>
            <div className="mb-2 text-xs tracking-[0.25em] text-ink-dim">CURRENT ALERT STATUS</div>
            {alert === null ? (
              <>
                <div className="mb-2 text-2xl font-bold tracking-wide text-ink-dim">NO CURRENT READING</div>
                <p className="max-w-2xl text-sm leading-relaxed text-ink">
                  NO₂ and O₃ are both unavailable for this station right now — no alert can be computed.
                </p>
              </>
            ) : (
              <>
                <div className="mb-2 text-2xl font-bold tracking-wide" style={{ color: LEVEL_COLOR[level as AqiLevel] }}>
                  {alert.headline}
                </div>
                <p className="max-w-2xl text-sm leading-relaxed text-ink">{alert.body}</p>
              </>
            )}
          </div>
        </div>

        {/* Details rows — revealed + scrambled once the alert box has faded in */}
        <div className={`transition-opacity duration-700 ${stage >= 2 ? "opacity-100" : "opacity-0"}`}>
          <div className="mb-16 divide-y divide-border-faint border-y border-border text-sm">
            <div className="flex justify-between py-3">
              <span className="text-ink-dim">LAT/LON</span>
              <ScrambleText
                active={stage >= 2}
                durationMs={SCRAMBLE_DURATION_MS}
                startDelayMs={0}
                className="tabular-nums text-ink-bright"
                text={`${station.lat.toFixed(4)}° N, ${station.lon.toFixed(4)}° E`}
              />
            </div>
            <div className="flex justify-between py-3">
              <span className="text-ink-dim">ELEVATION</span>
              <ScrambleText
                active={stage >= 2}
                durationMs={SCRAMBLE_DURATION_MS}
                startDelayMs={1 * SCRAMBLE_STAGGER_MS}
                className="tabular-nums text-ink-bright"
                text={Number.isFinite(details.elevationM) ? `${details.elevationM} M ASL` : "NOT AVAILABLE"}
              />
            </div>
            <div className="flex justify-between py-3">
              <span className="text-ink-dim">WIND</span>
              <ScrambleText
                active={stage >= 2}
                durationMs={SCRAMBLE_DURATION_MS}
                startDelayMs={2 * SCRAMBLE_STAGGER_MS}
                className="tabular-nums text-ink-bright"
                text={
                  Number.isFinite(details.windKt)
                    ? `${details.windDir} ${details.windKt} ${realApi ? "M/S" : "KT"}`
                    : "NOT AVAILABLE"
                }
              />
            </div>
            <div className="flex justify-between py-3">
              <span className="text-ink-dim">HUMIDITY</span>
              <ScrambleText
                active={stage >= 2}
                durationMs={SCRAMBLE_DURATION_MS}
                startDelayMs={3 * SCRAMBLE_STAGGER_MS}
                className="tabular-nums text-ink-bright"
                text={Number.isFinite(details.humidityPct) ? `${details.humidityPct}%` : "NOT AVAILABLE"}
              />
            </div>
          </div>
        </div>

        {/* Section 01 — current conditions */}
        <section className="mb-16">
          <SectionHeader index="01" />
          <SectionTitle>CURRENT CONDITIONS</SectionTitle>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <ReadingCard label="NO₂" value={reading.no2} unit="µg/m³" limit={200} level={levelForNO2(reading.no2)} trend={no2Trend} emphasize />
            <ReadingCard label="O₃" value={reading.o3} unit="µg/m³" limit={150} level={levelForO3(reading.o3)} trend={o3Trend} emphasize />
            <ReadingCard label="PM2.5" value={reading.pm25} unit="µg/m³" limit={225} level={levelForPM25(reading.pm25)} />
            <ReadingCard label="PM10" value={reading.pm10} unit="µg/m³" limit={424} level={levelForPM10(reading.pm10)} />
            <ReadingCard label="CO" value={reading.co} unit="mg/m³" limit={18} level={coLevel} />
            <ReadingCard label="SO₂" value={reading.so2} unit="µg/m³" limit={800} level={so2Level} />
          </div>
        </section>

        {/* Section 02 — quick scan */}
        <section className="mb-16">
          <SectionHeader index="02" />
          <SectionTitle>POLLUTANT QUICK-SCAN</SectionTitle>
          <QuickScanTable rows={quickScan} />
        </section>

        {/* Section 03 — forecast */}
        <section className="mb-16">
          <SectionHeader index="03" />
          <SectionTitle>MULTI-HORIZON FORECAST — O₃ / NO₂ (1H · 3H · 6H · 12H · 24H · 48H)</SectionTitle>
          <ForecastPanel points={forecast} />
        </section>

        {/* Section 04 — history */}
        <section className="mb-8">
          <SectionHeader index="04" />
          <SectionTitle>48H HISTORY — O₃ / NO₂</SectionTitle>
          <HistoryPanel points={history} />
        </section>
      </main>

      <Footer />
      <Ticker />
    </div>
  );
}
