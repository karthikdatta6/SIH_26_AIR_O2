import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Topbar } from "../layout/Topbar";
import { Globe } from "./Globe";
import { LiveClock } from "../common/LiveClock";
import { TypewriterText } from "../common/TypewriterText";
import { usePageTransition } from "../../lib/PageTransition";

const STATS = [
  { value: "10", label: "GROUND STATIONS" },
  { value: "4", label: "DATA SOURCES FUSED" },
  { value: "2", label: "POLLUTANTS FORECAST" },
  { value: "24–48H", label: "FORECAST HORIZON" },
  { value: "9", label: "VARIABLES / STATION" },
];

const HEADLINE = [
  { text: "WE SEE", amber: false },
  { text: "THE INVISIBLE.", amber: false },
  { text: "WE PREDICT", amber: true },
  { text: "THE UNAVOIDABLE.", amber: true },
];

export function Hero() {
  const navigate = useNavigate();
  const startTransition = usePageTransition();
  const [headlineStage, setHeadlineStage] = useState(0);

  return (
    <div className="relative flex min-h-screen flex-col overflow-x-hidden bg-bg bg-grid">
      <Topbar />

      <main className="mx-auto flex w-full max-w-[1600px] flex-1 flex-col items-center justify-center gap-8 px-6 py-10 lg:flex-row lg:items-start lg:gap-6">
        {/* Left: messaging */}
        <div className="max-w-2xl text-center lg:text-left">
          <div className="mb-4 text-xs tracking-[0.35em] text-amber-500">
            ENVIRONMENTAL INTELLIGENCE SYSTEM
          </div>
          <h1 className="mb-8 font-display text-6xl font-normal uppercase leading-[1.15] tracking-tight text-ink-bright text-shadow-amber sm:text-7xl lg:text-8xl">
            {HEADLINE.map((line, i) => (
              <span key={i}>
                <span className={line.amber ? "text-amber-400" : undefined}>
                  {i < headlineStage && line.text}
                  {i === headlineStage && (
                    <TypewriterText
                      text={line.text}
                      speedMs={38}
                      startDelayMs={i === 0 ? 0 : 120}
                      onComplete={() => setHeadlineStage((s) => s + 1)}
                    />
                  )}
                </span>
                {i < HEADLINE.length - 1 && <br />}
              </span>
            ))}
          </h1>
          <div
            className={`transition-opacity duration-700 ${
              headlineStage >= HEADLINE.length ? "opacity-100" : "pointer-events-none opacity-0"
            }`}
          >
            <p className="mb-10 text-sm leading-relaxed text-ink sm:text-base">
              A unified intelligence layer for predicting Delhi's air — powered by
              ground stations, satellites, weather, and AI.
            </p>

            <button
              onClick={() => startTransition(() => navigate("/network"))}
              className="group relative inline-flex items-center gap-3 border border-amber-500 px-8 py-4 text-sm font-bold tracking-[0.2em] text-amber-400 transition-colors hover:bg-amber-500 hover:text-black"
            >
              [ INITIALIZE THE NETWORK ]
              <span className="transition-transform group-hover:translate-x-1">→</span>
            </button>
            <div className="mt-3 text-[11px] tracking-[0.2em] text-ink-dim">
              REF: SIH-25178 · CLEARANCE LEVEL 3 REQUIRED
            </div>
          </div>
        </div>

        {/* Right: globe */}
        <div className="relative flex items-center justify-center lg:flex-1">
          <Globe size={600} />
          <div className="pointer-events-none absolute left-1/2 top-1/2 h-[640px] w-[640px] -translate-x-1/2 -translate-y-1/2 rounded-full border border-border animate-scan-ring" />
          <div className="absolute -bottom-2 left-1/2 -translate-x-1/2 whitespace-nowrap text-[12px] tracking-[0.3em] text-ink-dim">
            28.61°N 77.20°E · DELHI NCT · <LiveClock />
          </div>
        </div>
      </main>

      <div className="border-t border-border">
        <div className="mx-auto flex w-full max-w-[1600px] flex-wrap items-baseline justify-center gap-x-12 gap-y-4 px-6 py-6 sm:justify-between">
          {STATS.map((s) => (
            <div key={s.label} className="text-center sm:text-left">
              <div className="text-2xl font-bold text-amber-400 text-shadow-amber">{s.value}</div>
              <div className="text-[11px] tracking-[0.2em] text-ink-dim">{s.label}</div>
            </div>
          ))}
        </div>
      </div>

      <div className="border-t border-border py-3 text-center text-[12px] tracking-[0.3em] text-ink-dim">
        SIH 25178 · SHORT-TERM FORECASTING OF GROUND-LEVEL O₃ AND NO₂
      </div>
    </div>
  );
}
