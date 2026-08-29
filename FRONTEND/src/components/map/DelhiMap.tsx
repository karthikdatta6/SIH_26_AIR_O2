import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Topbar } from "../layout/Topbar";
import { Footer } from "../layout/Footer";
import { Ticker } from "../layout/Ticker";
import { SectionHeader, SectionTitle } from "../common/SectionHeader";
import { TypewriterText } from "../common/TypewriterText";
import { StationInfoPanel } from "./StationInfoPanel";
import { ScanOverlay } from "./ScanOverlay";
import { RealDelhiMap } from "./RealDelhiMap";
import { getStation } from "../../lib/stations";
import { stationStatus, currentReading, type CurrentReading, type StationStatus } from "../../lib/mockData";
import { usePageTransition } from "../../lib/PageTransition";
import { useRealApi, fetchStationsCurrent, type ApiStationCurrent } from "../../lib/api";

export function DelhiMap() {
  const navigate = useNavigate();
  const startTransition = usePageTransition();
  const [hoveredId, setHoveredId] = useState<string | null>(null);
  const realApi = useRealApi();

  // Fetched once on mount (not per-hover — a hover needs to feel instant,
  // and this is 10 stations' worth of data anyway) and looked up per
  // station from there. null = still loading or real API mode is off.
  const [liveByStation, setLiveByStation] = useState<Map<string, ApiStationCurrent> | null>(null);

  useEffect(() => {
    if (!realApi) return;
    let cancelled = false;
    fetchStationsCurrent()
      .then((data) => {
        if (!cancelled) setLiveByStation(new Map(data.stations.map((s) => [s.station_id, s])));
      })
      .catch(() => {
        // A failed fetch is "no data available", not a crash — every
        // station just falls back to the OFFLINE/no-reading state below.
        if (!cancelled) setLiveByStation(new Map());
      });
    return () => {
      cancelled = true;
    };
  }, [realApi]);

  function deriveStatus(id: string): StationStatus {
    if (!realApi) return stationStatus(id);
    const c = liveByStation?.get(id);
    if (!c) return "OFFLINE"; // not loaded yet, or genuinely no data for this station
    if (c.no2.value === null && c.o3.value === null) return "OFFLINE";
    if (c.no2.value === null || c.o3.value === null) return "DEGRADED";
    return "ONLINE";
  }

  function deriveReading(id: string): CurrentReading | null {
    if (!realApi) return currentReading(id);
    const c = liveByStation?.get(id);
    if (!c) return null;
    return { pm25: c.pm25.value, pm10: c.pm10.value, no2: c.no2.value, o3: c.o3.value, co: c.co.value, so2: c.so2.value };
  }

  const hoveredStation = hoveredId ? getStation(hoveredId) ?? null : null;
  const hoveredStatus = hoveredId ? deriveStatus(hoveredId) : null;
  const hoveredReading = hoveredId ? deriveReading(hoveredId) : null;
  const hoveredIsLive = hoveredId && realApi ? (liveByStation?.get(hoveredId)?.is_live ?? false) : false;

  return (
    <div className="flex min-h-screen flex-col bg-bg">
      <Topbar />

      <main className="mx-auto w-full max-w-[1600px] flex-1 px-6 py-10">
        <SectionHeader index="01" />
        <div className="mb-8 flex flex-wrap items-end justify-between gap-4">
          <SectionTitle>
            <TypewriterText text="DELHI MONITORING NETWORK" speedMs={22} />
          </SectionTitle>
          <div className="mb-8 text-xs tracking-widest text-ink-dim">
            <TypewriterText text="10 ACTIVE STATIONS · NCT OF DELHI" speedMs={14} startDelayMs={650} cursor={false} />
          </div>
        </div>

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-[1fr_320px]">
          {/* Map */}
          <div className="relative h-[560px] overflow-hidden border border-border bg-panel">
            <RealDelhiMap
              hoveredId={hoveredId}
              getStatus={deriveStatus}
              statusVersion={liveByStation ? 1 : 0}
              onHover={setHoveredId}
              onSelect={(id) => startTransition(() => navigate(`/station/${id}`))}
            />
            <ScanOverlay />
            <div className="pointer-events-none absolute bottom-3 left-3 z-[500] text-[12px] tracking-widest text-ink-dim">
              LIVE MAP · OPENSTREETMAP + CARTO · SCAN INTERVAL 5S
            </div>
          </div>

          {/* Side panel: hover readout only, matches the map's fixed height exactly */}
          <div className="flex h-[560px] flex-col">
            <StationInfoPanel
              station={hoveredStation}
              status={hoveredStatus}
              reading={hoveredReading}
              isLive={hoveredIsLive}
              className="h-full"
            />
          </div>
        </div>
      </main>

      <Footer />
      <Ticker />
    </div>
  );
}
