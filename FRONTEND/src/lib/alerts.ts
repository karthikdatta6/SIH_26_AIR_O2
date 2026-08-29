import type { AqiLevel } from "./aqi";

export const ALERT_COPY: Record<AqiLevel, { headline: string; body: string }> = {
  GOOD: {
    headline: "AIR QUALITY SATISFACTORY",
    body: "Ozone and nitrogen dioxide levels pose little or no risk. Normal outdoor activity is safe for all groups.",
  },
  MODERATE: {
    headline: "MODERATE AIR QUALITY",
    body: "Acceptable levels overall. Unusually sensitive individuals should consider reducing prolonged exertion outdoors.",
  },
  USG: {
    headline: "UNHEALTHY FOR SENSITIVE GROUPS",
    body: "Sensitive groups (children, elderly, respiratory/cardiac conditions) may experience health effects. General public unlikely to be affected at these levels.",
  },
  UNHEALTHY: {
    headline: "UNHEALTHY AIR QUALITY",
    body: "Everyone may begin to experience health effects. Sensitive groups should avoid prolonged outdoor exertion.",
  },
  VERY_UNHEALTHY: {
    headline: "VERY UNHEALTHY AIR QUALITY",
    body: "Health alert: significant risk of health effects for everyone. Sensitive groups should avoid all outdoor exertion; the general public should limit prolonged outdoor exertion.",
  },
  HAZARDOUS: {
    headline: "HAZARDOUS AIR QUALITY",
    body: "Health emergency conditions. The entire population is likely to be affected. Avoid all outdoor exertion.",
  },
};
