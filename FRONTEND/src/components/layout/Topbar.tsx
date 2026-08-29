import { Link } from "react-router-dom";
import { LiveClock } from "../common/LiveClock";

const NAV = ["NETWORK", "STATIONS", "FORECAST", "ARCHIVE"];

export function Topbar() {
  return (
    <header className="sticky top-0 z-40 border-b border-border bg-bg/95 backdrop-blur-sm">
      <div className="mx-auto flex h-16 max-w-[1600px] items-center justify-between px-6">
        <div className="flex items-center gap-4">
          <Link to="/" className="font-display text-xl font-normal tracking-[0.04em] text-amber-400 text-shadow-amber">
            AIRWATCH
          </Link>
          <span className="hidden h-4 w-px bg-border-strong sm:block" />
          <span className="hidden text-xs tracking-widest text-ink-dim sm:block">CPCB EST. 1974</span>
        </div>

        <nav className="hidden items-center gap-8 md:flex">
          {NAV.map((item) => (
            <Link
              key={item}
              to={item === "NETWORK" || item === "STATIONS" ? "/network" : "#"}
              className="text-xs tracking-[0.2em] text-ink-dim transition-colors hover:text-amber-300"
            >
              {item}
            </Link>
          ))}
        </nav>

        <div className="flex items-center gap-3 text-xs tracking-widest text-ink-dim">
          <LiveClock />
          <span className="h-3 w-3 animate-flicker bg-amber-500" />
        </div>
      </div>
    </header>
  );
}
