import { useEffect, useState } from "react";

function formatUtc(d: Date): string {
  const hh = String(d.getUTCHours()).padStart(2, "0");
  const mm = String(d.getUTCMinutes()).padStart(2, "0");
  const ss = String(d.getUTCSeconds()).padStart(2, "0");
  return `${hh}:${mm}:${ss}`;
}

export function LiveClock({ className }: { className?: string }) {
  const [now, setNow] = useState(() => new Date());

  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(id);
  }, []);

  return (
    <span className={className}>
      {formatUtc(now)} <span className="text-amber-400">UTC</span>
    </span>
  );
}

export function isoNowUtc(): string {
  return new Date().toISOString().replace("T", " ").slice(0, 19) + " UTC";
}
