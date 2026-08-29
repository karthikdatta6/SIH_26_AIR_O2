import { useEffect, useMemo } from "react";

const CELL_SIZE = 22; // px — target cell size, denser than a fixed low-res grid
const SWEEP_SECONDS = 1.1; // time for the top-down wave to reach the bottom row — slow
// enough that the eye catches it originating right at row 0, not partway down.
const CELL_FADE_SECONDS = 0.12; // short pop per cell, so the wave-front reads as a moving edge
const JITTER_SECONDS = 0.04; // small, so the leading edge stays a crisp line, not a fuzzy band
const HOLD_SECONDS = 0.12; // beat at full coverage before the reveal wipe starts

// Site palette only — ink-bright white, amber yellow, USG orange, unhealthy red.
const COLORS = ["#efe9d8", "#ddb654", "#e0762a", "#d8452e"];

const COVER_DURATION = SWEEP_SECONDS + JITTER_SECONDS + CELL_FADE_SECONDS;
const REVEAL_START = COVER_DURATION + HOLD_SECONDS;

interface Props {
  /** Bump to fire a new wipe; 0 means idle. */
  triggerId: number;
  /** Fired once the screen is fully covered — safe to swap page content now. */
  onCovered: () => void;
}

export function PixelTransition({ triggerId, onCovered }: Props) {
  // Grid dimensions and the div count are fixed for the component's whole
  // lifetime — kept stable across triggers (same React keys below) so a
  // transition never pays to create ~2,500 DOM nodes at the moment it
  // starts. That one-time cost is what made the cover sweep's earliest
  // rows appear to "just pop in" instead of animating.
  const { cols, rows, total } = useMemo(() => {
    const cols = Math.ceil(window.innerWidth / CELL_SIZE);
    const rows = Math.ceil(window.innerHeight / CELL_SIZE);
    return { cols, rows, total: cols * rows };
  }, []);

  // Re-rolled every trigger for fresh colors/timing, applied as a style
  // patch onto the already-mounted cells rather than new elements.
  const session = useMemo(() => {
    if (triggerId === 0) return null;
    const list: { color: string; coverDelay: number; revealDelay: number }[] = [];
    for (let row = 0; row < rows; row++) {
      const wave = (row / rows) * SWEEP_SECONDS;
      for (let col = 0; col < cols; col++) {
        list.push({
          color: COLORS[Math.floor(Math.random() * COLORS.length)],
          coverDelay: wave + Math.random() * JITTER_SECONDS,
          revealDelay: REVEAL_START + wave + Math.random() * JITTER_SECONDS,
        });
      }
    }
    return list;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [triggerId, cols, rows]);

  useEffect(() => {
    if (triggerId === 0) return;
    const t = setTimeout(onCovered, COVER_DURATION * 1000);
    return () => clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [triggerId]);

  return (
    <div
      aria-hidden="true"
      // Above Leaflet's own panes (its tooltip/popup panes go up to
      // z-index 700), so the map can't bleed through mid-transition.
      className="pointer-events-none fixed inset-0 z-[1000] grid"
      style={{ gridTemplateColumns: `repeat(${cols}, 1fr)`, gridTemplateRows: `repeat(${rows}, 1fr)` }}
    >
      {Array.from({ length: total }, (_, i) => {
        const s = session?.[i];
        return (
          <div
            key={i}
            style={
              s
                ? {
                    background: s.color,
                    opacity: 0,
                    animation: `
                      pixel-in ${CELL_FADE_SECONDS}s ease-out ${s.coverDelay}s forwards,
                      pixel-out ${CELL_FADE_SECONDS}s ease-in ${s.revealDelay}s forwards
                    `,
                  }
                : { opacity: 0 }
            }
          />
        );
      })}
    </div>
  );
}
