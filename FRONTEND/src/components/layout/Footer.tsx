export function Footer() {
  return (
    <footer className="border-t border-border">
      <div className="mx-auto flex max-w-[1600px] flex-col gap-6 px-6 py-12 sm:flex-row sm:justify-between">
        <div>
          <div className="mb-2 text-lg font-bold tracking-[0.15em] text-amber-400">AIRWATCH BUREAU</div>
          <div className="text-sm text-ink-dim">DIVISION OF ENVIRONMENTAL MONITORING</div>
          <div className="text-sm text-ink-dim">CENTRAL POLLUTION CONTROL BOARD — NCT OF DELHI</div>
        </div>
        <div className="text-right text-sm text-ink-dim">
          <div>
            ALL READINGS ARE MODEL FORECASTS <span className="text-ink-bright">±5%</span>
          </div>
          <div>REPORT DISCREPANCIES TO NATIONAL BUREAU</div>
          <div>© AIRWATCH 2026</div>
        </div>
      </div>
      <div className="mx-auto max-w-[1600px] px-6 pb-10">
        <div className="border-t border-dashed border-border-strong" />
        <div className="mt-8 pb-2 text-center text-xs tracking-[0.3em] text-ink-dim">
          BREATHE CLEAN · MONITOR OFTEN · ACT NOW
        </div>
      </div>
    </footer>
  );
}
