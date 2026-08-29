export function ScanOverlay() {
  return (
    <div
      className="pointer-events-none absolute inset-0 animate-[sweep_5s_linear_infinite] opacity-40"
      style={{
        background:
          "conic-gradient(from 0deg, rgba(216,178,84,0.22) 0deg, rgba(216,178,84,0) 55deg, rgba(216,178,84,0) 360deg)",
      }}
    >
      <style>{`
        @keyframes sweep {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}
