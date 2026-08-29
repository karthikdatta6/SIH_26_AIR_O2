import raw from "../data/delhi_boundary.json";
import type { Feature, Polygon, MultiPolygon } from "geojson";

// Real NCT-of-Delhi administrative boundary, OpenStreetMap contributors (ODbL),
// fetched once via Nominatim and vendored here (src/data/delhi_boundary.json)
// so the app has no runtime dependency on that API.
export const DELHI_BOUNDARY_FEATURE = (
  raw as unknown as { features: Feature<Polygon | MultiPolygon>[] }
).features[0];

// [minLon, minLat, maxLon, maxLat]
export const DELHI_BBOX: [number, number, number, number] = [
  76.8388351, 28.4046285, 77.3453379, 28.8834464,
];

export const DELHI_CENTER: [number, number] = [28.6139, 77.209];
