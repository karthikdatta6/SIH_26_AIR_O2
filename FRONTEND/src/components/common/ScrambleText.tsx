import { useEffect, useRef, useState } from "react";

const LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
const DIGITS = "0123456789";

// Only letters/digits scramble — punctuation, spaces, °, %, etc. show
// immediately, so the effect reads as "decoding text and numbers" rather
// than pure static noise.
function randomCharLike(actual: string): string {
  if (/[a-z]/.test(actual)) return LETTERS[Math.floor(Math.random() * LETTERS.length)].toLowerCase();
  if (/[A-Z]/.test(actual)) return LETTERS[Math.floor(Math.random() * LETTERS.length)];
  if (/[0-9]/.test(actual)) return DIGITS[Math.floor(Math.random() * DIGITS.length)];
  return actual;
}

function scrambleAll(text: string): string {
  return text
    .split("")
    .map((ch) => (/[a-zA-Z0-9]/.test(ch) ? randomCharLike(ch) : ch))
    .join("");
}

interface Props {
  text: string;
  className?: string;
  durationMs?: number;
  /** Delay before this instance's own scramble starts, once `active`. */
  startDelayMs?: number;
  /** Set true to (re-)start the scramble-to-reveal; false renders an undecoded, scrambled placeholder. */
  active?: boolean;
}

export function ScrambleText({ text, className, durationMs = 900, startDelayMs = 0, active = true }: Props) {
  // Starts scrambled, not as the answer — otherwise there's a render
  // (mount, or the moment `active` flips true but the animation hasn't
  // started yet) that paints the correct text before the reveal begins.
  const [display, setDisplay] = useState(() => scrambleAll(text));
  const rafRef = useRef(0);
  const timeoutRef = useRef(0);

  useEffect(() => {
    if (!active) {
      setDisplay(scrambleAll(text));
      return;
    }

    function runScramble() {
      const start = performance.now();
      // Each character locks in at its own random point in time, biased
      // left-to-right, so the reveal reads as a sweep rather than pure noise.
      const resolveAt = text.split("").map((_, i) => {
        const base = (i / text.length) * durationMs * 0.6;
        return base + Math.random() * durationMs * 0.4;
      });

      function frame(now: number) {
        const elapsed = now - start;
        let out = "";
        let allResolved = true;
        for (let i = 0; i < text.length; i++) {
          const ch = text[i];
          if (elapsed >= resolveAt[i] || !/[a-zA-Z0-9]/.test(ch)) {
            out += ch;
          } else {
            out += randomCharLike(ch);
            allResolved = false;
          }
        }
        setDisplay(out);
        if (!allResolved) rafRef.current = requestAnimationFrame(frame);
      }

      rafRef.current = requestAnimationFrame(frame);
    }

    if (startDelayMs > 0) {
      timeoutRef.current = window.setTimeout(runScramble, startDelayMs);
    } else {
      runScramble();
    }

    return () => {
      cancelAnimationFrame(rafRef.current);
      clearTimeout(timeoutRef.current);
    };
  }, [text, durationMs, startDelayMs, active]);

  return <span className={className}>{display}</span>;
}
