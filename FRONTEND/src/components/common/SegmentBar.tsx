import { useInView } from "../../lib/useInView";

interface Props {
  fraction: number; // 0..1
  segments?: number;
  color?: string;
}

export function SegmentBar({ fraction, segments = 20, color = "var(--color-amber-500)" }: Props) {
  const { ref, inView } = useInView<HTMLDivElement>();
  const filled = Math.round(Math.min(1, Math.max(0, fraction)) * segments);
  return (
    <div ref={ref} className="flex gap-[3px]">
      {Array.from({ length: segments }, (_, i) => (
        <span
          key={i}
          className="h-3 flex-1 origin-left transition-transform duration-300 ease-out"
          style={{
            background: i < filled ? color : "var(--color-border-faint)",
            transform: inView ? "scaleX(1)" : "scaleX(0)",
            transitionDelay: `${i * 18}ms`,
          }}
        />
      ))}
    </div>
  );
}
