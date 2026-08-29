import type { ReactNode } from "react";

export function SectionHeader({ index }: { index: string }) {
  return (
    <div className="mb-2 flex items-center gap-4">
      <span className="text-xs tracking-[0.25em] text-ink-dim">
        SECTION {index}
        <span className="mx-4 text-border-strong">—</span>
      </span>
      <span className="h-px flex-1 bg-border" />
    </div>
  );
}

export function SectionTitle({ children }: { children: ReactNode }) {
  return <h2 className="mb-8 text-2xl font-bold tracking-[0.08em] text-ink-bright sm:text-3xl">{children}</h2>;
}
