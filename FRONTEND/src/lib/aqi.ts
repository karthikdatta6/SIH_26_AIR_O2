export type AqiLevel = "GOOD" | "MODERATE" | "USG" | "UNHEALTHY" | "VERY_UNHEALTHY" | "HAZARDOUS";

export const LEVEL_LABEL: Record<AqiLevel, string> = {
  GOOD: "GOOD",
  MODERATE: "MODERATE",
  USG: "UNHEALTHY (SG)",
  UNHEALTHY: "UNHEALTHY",
  VERY_UNHEALTHY: "VERY UNHEALTHY",
  HAZARDOUS: "HAZARDOUS",
};

export const LEVEL_COLOR: Record<AqiLevel, string> = {
  GOOD: "var(--color-good)",
  MODERATE: "var(--color-moderate)",
  USG: "var(--color-usg)",
  UNHEALTHY: "var(--color-unhealthy)",
  VERY_UNHEALTHY: "var(--color-very-unhealthy)",
  HAZARDOUS: "var(--color-hazardous)",
};

interface Band {
  max: number;
  level: AqiLevel;
}

// Real EPA AQI breakpoints (the standard 6-category NO2 1-hour / O3 8-hour
// tables), converted from the EPA's own ppb units to µg/m³ — the Phase 3
// model's native output unit (models/NO2/feature_schema.json
// "target_unit") — since pasting ppb numbers directly against µg/m³
// values would misclassify every reading.
//
// Conversion: µg/m³ = ppb × (molecular_weight / 24.45), the standard
// gas-to-mass formula at EPA reference conditions (25°C, 1 atm).
// NO2 (MW 46.01 g/mol): factor ≈ 1.882. O3 (MW 48.00 g/mol): factor ≈ 1.963.
//
// Source breakpoints (ppb) — NO2: 53/100/360/649/1249/2049,
// O3: 54/70/85/105/200/500. Converted (µg/m³, rounded):
const NO2_BANDS: Band[] = [
  { max: 100, level: "GOOD" },            // 53 ppb
  { max: 188, level: "MODERATE" },        // 100 ppb
  { max: 677, level: "USG" },             // 360 ppb
  { max: 1221, level: "UNHEALTHY" },      // 649 ppb
  { max: 2350, level: "VERY_UNHEALTHY" }, // 1249 ppb
  { max: Infinity, level: "HAZARDOUS" },  // 2049 ppb (~3856) and beyond
];

const O3_BANDS: Band[] = [
  { max: 106, level: "GOOD" },            // 54 ppb
  { max: 137, level: "MODERATE" },        // 70 ppb
  { max: 167, level: "USG" },             // 85 ppb
  { max: 206, level: "UNHEALTHY" },       // 105 ppb
  { max: 393, level: "VERY_UNHEALTHY" },  // 200 ppb
  { max: Infinity, level: "HAZARDOUS" },  // 500 ppb (~982) and beyond
];

// PM2.5 and PM10 breakpoints are already µg/m³ in both the EPA table and
// this app's data (PHASE_2_3_SUDHITH/4_DOCUMENTATION/PHASE_3_ML_RESEARCHER_HANDOUT.md
// confirms PM2.5_ground/PM10_ground are µg/m³) — no unit conversion needed,
// pasted directly from the real breakpoint table.
const PM25_BANDS: Band[] = [
  { max: 9.0, level: "GOOD" },
  { max: 35.4, level: "MODERATE" },
  { max: 55.4, level: "USG" },
  { max: 125.4, level: "UNHEALTHY" },
  { max: 225.4, level: "VERY_UNHEALTHY" },
  { max: Infinity, level: "HAZARDOUS" }, // 500.4 and beyond
];

const PM10_BANDS: Band[] = [
  { max: 54, level: "GOOD" },
  { max: 154, level: "MODERATE" },
  { max: 254, level: "USG" },
  { max: 354, level: "UNHEALTHY" },
  { max: 424, level: "VERY_UNHEALTHY" },
  { max: Infinity, level: "HAZARDOUS" }, // 604 and beyond
];

// CO in this app is mg/m³, confirmed from the same handout doc
// (CO_ground: mg/m³, range 0.00-22.90) — the real CPCB CCR export column
// itself is also explicitly labeled "CO (mg/m³)" (verified against a real
// export this session). The breakpoint table is in ppm, so it's converted
// here rather than converting every CO value displayed throughout the
// app — much smaller, less risky change, and it also means the frontend's
// previous "ppm" unit label (StationDashboard.tsx) was actually wrong and
// needs fixing to "mg/m³" alongside this.
// Conversion: mg/m³ = ppm × (MW/24.45); CO MW 28.01 g/mol → factor ≈ 1.146.
// Source breakpoints (ppm): 4.4/9.4/12.4/15.4/30.4/50.4.
const CO_BANDS: Band[] = [
  { max: 5.04, level: "GOOD" },
  { max: 10.77, level: "MODERATE" },
  { max: 14.21, level: "USG" },
  { max: 17.64, level: "UNHEALTHY" },
  { max: 34.83, level: "VERY_UNHEALTHY" },
  { max: Infinity, level: "HAZARDOUS" }, // 57.74 (50.4 ppm) and beyond
];

// SO2 in this app is µg/m³ (SO2_ground, same handout doc). Breakpoint
// table is ppb, converted the same way as NO2/O3.
// Conversion: µg/m³ = ppb × (MW/24.45); SO2 MW 64.07 g/mol → factor ≈ 2.620.
// Source breakpoints (ppb): 35/75/185/304/604/1004.
const SO2_BANDS: Band[] = [
  { max: 92, level: "GOOD" },
  { max: 197, level: "MODERATE" },
  { max: 485, level: "USG" },
  { max: 797, level: "UNHEALTHY" },
  { max: 1583, level: "VERY_UNHEALTHY" },
  { max: Infinity, level: "HAZARDOUS" }, // 2631 (1004 ppb) and beyond
];

function bandFor(value: number, bands: Band[]): AqiLevel {
  return bands.find((b) => value <= b.max)?.level ?? "HAZARDOUS";
}

// null means "genuinely no reading" (e.g. a CPCB sensor gap for this
// pollutant right now) — must stay distinct from any real AqiLevel all the
// way through to display, never silently coerced to a value that would
// render as a real (and misleadingly good-looking) band.
export function levelForNO2(ugm3: number | null): AqiLevel | null {
  return ugm3 === null ? null : bandFor(ugm3, NO2_BANDS);
}

export function levelForO3(ugm3: number | null): AqiLevel | null {
  return ugm3 === null ? null : bandFor(ugm3, O3_BANDS);
}

export function levelForPM25(ugm3: number | null): AqiLevel | null {
  return ugm3 === null ? null : bandFor(ugm3, PM25_BANDS);
}

export function levelForPM10(ugm3: number | null): AqiLevel | null {
  return ugm3 === null ? null : bandFor(ugm3, PM10_BANDS);
}

export function levelForCO(mgm3: number | null): AqiLevel | null {
  return mgm3 === null ? null : bandFor(mgm3, CO_BANDS);
}

export function levelForSO2(ugm3: number | null): AqiLevel | null {
  return ugm3 === null ? null : bandFor(ugm3, SO2_BANDS);
}

export function worstLevel(levels: (AqiLevel | null)[]): AqiLevel | null {
  const order: AqiLevel[] = ["GOOD", "MODERATE", "USG", "UNHEALTHY", "VERY_UNHEALTHY", "HAZARDOUS"];
  const real = levels.filter((l): l is AqiLevel => l !== null);
  if (real.length === 0) return null;
  return real.reduce((worst, l) => (order.indexOf(l) > order.indexOf(worst) ? l : worst), "GOOD");
}
