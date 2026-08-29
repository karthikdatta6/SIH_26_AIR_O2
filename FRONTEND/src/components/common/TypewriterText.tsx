import { useEffect, useState } from "react";

interface Props {
  text: string;
  speedMs?: number;
  startDelayMs?: number;
  className?: string;
  cursor?: boolean;
  onComplete?: () => void;
}

export function TypewriterText({ text, speedMs = 18, startDelayMs = 0, className, cursor = true, onComplete }: Props) {
  const [shown, setShown] = useState(0);
  const [started, setStarted] = useState(startDelayMs === 0);

  useEffect(() => {
    setShown(0);
    setStarted(startDelayMs === 0);
    if (startDelayMs > 0) {
      const t = setTimeout(() => setStarted(true), startDelayMs);
      return () => clearTimeout(t);
    }
  }, [text, startDelayMs]);

  useEffect(() => {
    if (!started) return;
    if (shown >= text.length) return;
    const t = setTimeout(() => setShown((s) => s + 1), speedMs);
    return () => clearTimeout(t);
  }, [shown, started, text, speedMs]);

  const done = shown >= text.length;

  useEffect(() => {
    if (started && done) onComplete?.();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [started, done]);

  return (
    <span className={className}>
      {text
        .slice(0, shown)
        .split("")
        .map((ch, i) => (
          // Keyed by index so only the newest character (the rest already
          // finished and sit at opacity 1) actually plays the fade-in —
          // a soft pop instead of characters just snapping into place.
          <span key={i} style={{ animation: "pixel-in 0.16s ease-out forwards" }}>
            {ch}
          </span>
        ))}
      {cursor && !done && <span className="animate-blink">▌</span>}
    </span>
  );
}
