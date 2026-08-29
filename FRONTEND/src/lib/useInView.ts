import { useEffect, useRef, useState } from "react";

// Fires once, the first time the element scrolls into the viewport —
// used to trigger scroll-in reveal animations instead of playing them
// immediately on mount (which the user never gets to see if the element
// starts off-screen).
export function useInView<T extends HTMLElement>(threshold = 0.3) {
  const ref = useRef<T>(null);
  const [inView, setInView] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el || inView) return;
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setInView(true);
          observer.disconnect();
        }
      },
      { threshold },
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, [inView, threshold]);

  return { ref, inView };
}
