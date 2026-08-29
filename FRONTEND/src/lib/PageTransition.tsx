import { createContext, useContext, useRef, useState, type ReactNode } from "react";
import { PixelTransition } from "../components/hero/PixelTransition";

// Flip to re-enable the pixel wipe on route changes — everything below is
// left intact, this just short-circuits `start()` to navigate immediately.
const PIXEL_TRANSITION_ENABLED = false;

type StartTransition = (onCovered: () => void) => void;

const PageTransitionContext = createContext<StartTransition | null>(null);

// Lives at the app root (outside any single route, always mounted) so:
//  1. the reveal-out half of the wipe plays over whatever page navigate()
//     lands on, not the page that triggered it (which unmounts the instant
//     navigate() runs), and
//  2. the ~2,500-cell grid is built once at app load instead of at the
//     moment the user clicks — building it on demand was the stutter that
//     ate the first frames of the cover sweep.
export function PageTransitionProvider({ children }: { children: ReactNode }) {
  const [triggerId, setTriggerId] = useState(0);
  const onCoveredRef = useRef<() => void>(() => {});

  const start: StartTransition = (onCovered) => {
    if (!PIXEL_TRANSITION_ENABLED) {
      onCovered();
      return;
    }
    onCoveredRef.current = onCovered;
    setTriggerId((id) => id + 1);
  };

  return (
    <PageTransitionContext.Provider value={start}>
      {children}
      {PIXEL_TRANSITION_ENABLED && (
        <PixelTransition triggerId={triggerId} onCovered={() => onCoveredRef.current()} />
      )}
    </PageTransitionContext.Provider>
  );
}

export function usePageTransition(): StartTransition {
  const ctx = useContext(PageTransitionContext);
  if (!ctx) throw new Error("usePageTransition must be used within a PageTransitionProvider");
  return ctx;
}
