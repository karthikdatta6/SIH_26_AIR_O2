import { STATIONS } from "../../lib/stations";
import { currentReading } from "../../lib/mockData";

function buildTickerItems(): string[] {
  return STATIONS.map((s) => {
    const r = currentReading(s.id);
    // Ticker only ever shows mock data (never wired to the real API) —
    // currentReading()'s mock implementation always fills every field
    // with a real number, so the null case CurrentReading allows for
    // real API data genuinely can't happen here. Asserted, not defaulted,
    // so this stays honest about why it's safe rather than implying null
    // is a real possibility that got silently papered over.
    return `${s.name.toUpperCase()}  NO₂ ${r.no2!.toFixed(1)} µg/m³ · O₃ ${r.o3!.toFixed(1)} µg/m³`;
  });
}

export function Ticker() {
  const items = buildTickerItems();
  const track = [...items, ...items];

  return (
    <div className="sticky bottom-0 z-40 flex h-10 items-stretch overflow-hidden border-t border-border bg-panel">
      <div className="flex shrink-0 items-center gap-2 border-r border-border bg-amber-500 px-3 text-[13px] font-bold tracking-widest text-black">
        <span className="h-2 w-2 animate-blink rounded-full bg-black" />
        LIVE
      </div>
      <div className="relative flex flex-1 items-center overflow-hidden">
        <div className="flex w-max animate-[ticker_38s_linear_infinite] items-center gap-10 whitespace-nowrap pl-6 text-[13px] tracking-widest text-ink-dim">
          {track.map((t, i) => (
            <span key={i} className="flex items-center gap-2">
              {t}
              <span className="text-border-strong">|</span>
            </span>
          ))}
        </div>
      </div>
      <style>{`
        @keyframes ticker {
          from { transform: translateX(0); }
          to { transform: translateX(-50%); }
        }
      `}</style>
    </div>
  );
}
