import { useEffect, useState } from "react";
import { TypewriterText } from "../common/TypewriterText";
import { ScrambleText } from "../common/ScrambleText";
import { StatusPill } from "../common/StatusPill";
import type { Station } from "../../lib/stations";
import type { CurrentReading, StationStatus } from "../../lib/mockData";
import { levelForNO2, levelForO3 } from "../../lib/aqi";

interface Props {
  station: Station | null;
  status: StationStatus | null;
  // Passed in by the caller (real API data or mock, per DelhiMap.tsx's
  // useRealApi() check) rather than fetched here — this component doesn't
  // know or care which source it came from.
  reading: CurrentReading | null;
  isLive?: boolean;
  className?: string;
}

// Each field's scramble starts once the previous one is halfway
// resolved — same cascading waterfall used on the station detail page.
const SCRAMBLE_DURATION_MS = 700;
const SCRAMBLE_STAGGER_MS = SCRAMBLE_DURATION_MS / 2;
// The NO₂/O₃ cards stay hidden until the ID/ZONE/STATUS block above is
// about halfway through its own reveal, then fade in and start scrambling.
const CARDS_DELAY_MS = 500;

export function StationInfoPanel({ station, status, reading, isLive, className = "" }: Props) {
  const [nameTyped, setNameTyped] = useState(false);

  // StationInfoPanel itself never unmounts between hovers (only the
  // key={station.id} div below does) — without this, nameTyped would
  // stay stuck true after the first reveal, so every later hover would
  // render the content already fully visible instead of replaying it.
  useEffect(() => {
    setNameTyped(false);
  }, [station?.id]);

  if (!station || !status) {
    return (
      <div className={`flex min-h-[280px] flex-col items-center justify-center gap-3 border border-dashed border-border p-6 text-center ${className}`}>
        <div className="h-8 w-8 border border-border-strong" />
        <div className="text-xs tracking-[0.3em] text-ink-dim">
          <TypewriterText text="HOVER A STATION TO SCAN" speedMs={30} />
        </div>
      </div>
    );
  }

  // reading can legitimately be null (e.g. real API data still loading,
  // or unavailable) — never fabricated as 0 either here or by the caller.
  const no2Level = reading ? levelForNO2(reading.no2) : null;
  const o3Level = reading ? levelForO3(reading.o3) : null;

  return (
    <div key={station.id} className={`flex flex-col justify-between border border-border-strong p-6 ${className}`}>
      <div>
        <div className="mb-1 text-xs tracking-[0.25em] text-ink-dim">
          <TypewriterText text="STATION SCAN — LIVE READOUT" speedMs={12} />
        </div>
        <div className="mb-6 text-2xl font-bold tracking-wide text-ink-bright">
          <TypewriterText
            text={station.name.toUpperCase()}
            speedMs={16}
            startDelayMs={200}
            onComplete={() => setNameTyped(true)}
          />
        </div>

        <div className={`transition-opacity duration-500 ${nameTyped ? "opacity-100" : "opacity-0"}`}>
          <div className="mb-6 space-y-2 text-xs tracking-widest text-ink-dim">
            <div>
              ID{" "}
              <ScrambleText
                active={nameTyped}
                durationMs={SCRAMBLE_DURATION_MS}
                startDelayMs={0}
                text={station.id}
              />
            </div>
            <div>
              ZONE{" "}
              <ScrambleText
                active={nameTyped}
                durationMs={SCRAMBLE_DURATION_MS}
                startDelayMs={1 * SCRAMBLE_STAGGER_MS}
                text={station.zone}
              />
            </div>
            <div className="flex items-center gap-2">
              STATUS
              <StatusPill level={status === "ONLINE" ? "GOOD" : status === "DEGRADED" ? "MODERATE" : "UNHEALTHY"} />
              {isLive && (
                <span className="flex items-center gap-1 border border-[var(--color-good)] px-1.5 py-0.5 text-[10px] font-bold tracking-widest text-[var(--color-good)]">
                  <span className="h-1 w-1 animate-blink rounded-full bg-[var(--color-good)]" />
                  LIVE
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Cards stay hidden until the block above is about halfway
            through revealing, then fade in and scramble their values. */}
        <div className={`transition-opacity delay-500 duration-500 ${nameTyped ? "opacity-100" : "opacity-0"}`}>
          <div className="grid grid-cols-2 gap-3">
            <div className="border border-border-faint p-4">
              <div className="text-[12px] tracking-widest text-ink-dim">NO₂</div>
              <div className="text-2xl font-bold tabular-nums text-amber-300">
                <ScrambleText
                  active={nameTyped}
                  durationMs={SCRAMBLE_DURATION_MS}
                  startDelayMs={CARDS_DELAY_MS}
                  text={reading?.no2 === null || reading?.no2 === undefined ? "N/A" : `${reading.no2.toFixed(1)} µg/m³`}
                />
              </div>
              <StatusPill level={no2Level} />
            </div>
            <div className="border border-border-faint p-4">
              <div className="text-[12px] tracking-widest text-ink-dim">O₃</div>
              <div className="text-2xl font-bold tabular-nums text-amber-300">
                <ScrambleText
                  active={nameTyped}
                  durationMs={SCRAMBLE_DURATION_MS}
                  startDelayMs={CARDS_DELAY_MS + SCRAMBLE_STAGGER_MS}
                  text={reading?.o3 === null || reading?.o3 === undefined ? "N/A" : `${reading.o3.toFixed(1)} µg/m³`}
                />
              </div>
              <StatusPill level={o3Level} />
            </div>
          </div>
        </div>
      </div>

      <div className={`transition-opacity delay-1000 duration-500 ${nameTyped ? "opacity-100" : "opacity-0"}`}>
        <div className="mb-4 h-px bg-border" />
        <div className="text-[13px] tracking-widest text-ink-dim">CLICK MARKER TO CONNECT →</div>
      </div>
    </div>
  );
}
