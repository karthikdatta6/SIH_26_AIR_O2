import { useEffect, useRef } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { STATIONS, type Station } from "../../lib/stations";
import type { StationStatus } from "../../lib/mockData";
import { DELHI_BOUNDARY_FEATURE, DELHI_BBOX, DELHI_CENTER } from "../../lib/delhiBoundary";

const STATUS_DOT_COLOR: Record<StationStatus, string> = {
  ONLINE: "#ddb654",
  DEGRADED: "#d1a125",
  OFFLINE: "#d8452e",
};

const MIN_ZOOM = 10.3;
const MAX_ZOOM = 18;

function lerp(a: number, b: number, t: number): number {
  return a + (b - a) * t;
}

function clamp01(t: number): number {
  return Math.max(0, Math.min(1, t));
}

// Marker size tracks zoom inversely: bigger and easier to spot when
// zoomed out over the whole NCT (each dot stands in for a wider area),
// smaller and more precise once you've zoomed into street level (so it
// pinpoints the station instead of covering the detail around it).
function markerIcon(active: boolean, color: string, zoom: number): L.DivIcon {
  const t = clamp01((zoom - MIN_ZOOM) / (MAX_ZOOM - MIN_ZOOM));
  const baseDot = lerp(12, 5, t);
  const dot = active ? baseDot * 1.5 : baseDot;
  const box = active ? dot + 16 : dot + 5;

  return L.divIcon({
    className: "airwatch-marker",
    html: `
      <div style="position:relative;width:${box}px;height:${box}px;">
        ${active ? `<div class="airwatch-marker-pulse" style="border-color:${color}"></div>` : ""}
        <div style="
          position:absolute; inset:0; margin:auto;
          width:${dot}px; height:${dot}px;
          background:${color}; border:1.5px solid #08070a; border-radius:0;
        "></div>
      </div>
    `,
    iconSize: [box, box],
    iconAnchor: [box / 2, box / 2],
  });
}

interface Props {
  hoveredId: string | null;
  getStatus: (id: string) => StationStatus;
  onHover: (id: string | null) => void;
  onSelect: (id: string) => void;
  // Bump this (e.g. once real station data finishes an async load) to
  // re-apply every marker's icon from the current getStatus — markers are
  // otherwise only created once on mount, so a status that resolves after
  // that (real API data loading in) would never reach already-drawn
  // markers without this, the same way hoveredId already triggers a
  // refresh below.
  statusVersion?: number;
}

export function RealDelhiMap({ hoveredId, getStatus, onHover, onSelect, statusVersion }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<L.Map | null>(null);
  const markersRef = useRef<Map<string, L.Marker>>(new Map());
  const propsRef = useRef({ hoveredId, getStatus, onHover, onSelect });
  propsRef.current = { hoveredId, getStatus, onHover, onSelect };
  const refreshAllIconsRef = useRef<() => void>(() => {});

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;

    const [minLon, minLat, maxLon, maxLat] = DELHI_BBOX;
    const bounds = L.latLngBounds([minLat - 0.03, minLon - 0.03], [maxLat + 0.03, maxLon + 0.03]);
    const delhiFitBounds = L.latLngBounds([minLat, minLon], [maxLat, maxLon]);

    const map = L.map(containerRef.current, {
      center: DELHI_CENTER,
      zoom: 11,
      minZoom: MIN_ZOOM,
      maxZoom: MAX_ZOOM,
      maxBounds: bounds,
      maxBoundsViscosity: 1.0,
      zoomControl: false,
      attributionControl: true,
    });
    mapRef.current = map;

    // Default view: the whole NCT framed with a little breathing room, same
    // on any screen size, instead of a fixed zoom level that looks too tight
    // on a narrow panel or too loose on a wide desktop one.
    map.fitBounds(delhiFitBounds, { padding: [28, 28] });

    map.on("zoom zoomend", () => refreshAllIconsRef.current());

    L.control.zoom({ position: "bottomright" }).addTo(map);

    L.control.attribution({ prefix: false, position: "bottomright" }).addAttribution(
      '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noreferrer">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions" target="_blank" rel="noreferrer">CARTO</a>'
    );

    // Labelled dark basemap: place names + roads get more detailed the
    // further in you zoom, same as any standard slippy map. CARTO's
    // basemap tiles now require a free API key (their anonymous-access
    // policy changed) — without VITE_CARTO_API_KEY set, the request still
    // succeeds but every tile is watermarked "API KEY REQUIRED" by
    // CARTO's own servers, not something retriable on our end.
    const cartoKey = import.meta.env.VITE_CARTO_API_KEY as string | undefined;
    const cartoUrl = cartoKey
      ? `https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png?key=${cartoKey}`
      : "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png";
    L.tileLayer(cartoUrl, {
      subdomains: "abcd",
      maxZoom: 20,
    }).addTo(map);

    // Dim everything outside the NCT boundary: a polygon comfortably larger
    // than the pannable area (not a near-world rectangle — projecting
    // near-polar/antimeridian coordinates at city zoom levels produces huge
    // pixel values that trigger SVG precision artifacts, visible as stray
    // hairlines) with the real Delhi outline cut out as a hole.
    const world: [number, number][] = [
      [minLat - 6, minLon - 6],
      [minLat - 6, maxLon + 6],
      [maxLat + 6, maxLon + 6],
      [maxLat + 6, minLon - 6],
    ];
    const holeRings =
      DELHI_BOUNDARY_FEATURE.geometry.type === "Polygon"
        ? [DELHI_BOUNDARY_FEATURE.geometry.coordinates[0]]
        : DELHI_BOUNDARY_FEATURE.geometry.coordinates.map((poly) => poly[0]);

    for (const ring of holeRings) {
      const hole = ring.map(([lon, lat]) => [lat, lon] as [number, number]);
      L.polygon([world, hole], {
        stroke: false,
        fillColor: "#050608",
        fillOpacity: 0.72,
        interactive: false,
      }).addTo(map);
    }

    // Bold, glowing NCT outline: a soft wide underlay plus a crisp bright line.
    L.geoJSON(DELHI_BOUNDARY_FEATURE, {
      style: { color: "#eaf9ff", weight: 7, opacity: 0.18, fill: false },
      interactive: false,
    }).addTo(map);
    L.geoJSON(DELHI_BOUNDARY_FEATURE, {
      style: { color: "#f4fbff", weight: 2.4, opacity: 0.95, fill: false },
      interactive: false,
    }).addTo(map);

    return () => {
      map.remove();
      mapRef.current = null;
      markersRef.current.clear();
    };
  }, []);

  // Create markers once the map exists, and wire up the zoom-aware refresh.
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    function applyIcon(id: string) {
      const marker = markersRef.current.get(id);
      if (!marker || !map) return;
      const status = propsRef.current.getStatus(id);
      const active = id === propsRef.current.hoveredId;
      marker.setIcon(markerIcon(active, STATUS_DOT_COLOR[status], map.getZoom()));
      marker.setZIndexOffset(active ? 1000 : 0);
    }

    refreshAllIconsRef.current = () => {
      markersRef.current.forEach((_marker, id) => applyIcon(id));
    };

    STATIONS.forEach((station: Station) => {
      const marker = L.marker([station.lat, station.lon], {
        icon: markerIcon(false, STATUS_DOT_COLOR[propsRef.current.getStatus(station.id)], map.getZoom()),
        riseOnHover: true,
      }).addTo(map);

      marker.on("mouseover", () => propsRef.current.onHover(station.id));
      marker.on("mouseout", () => propsRef.current.onHover(null));
      marker.on("click", () => propsRef.current.onSelect(station.id));

      markersRef.current.set(station.id, marker);
    });

    return () => {
      markersRef.current.forEach((m) => m.remove());
      markersRef.current.clear();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Reflect hover state, or freshly-loaded status data, onto marker icons
  // (size still respects current zoom).
  useEffect(() => {
    refreshAllIconsRef.current();
  }, [hoveredId, statusVersion]);

  return <div ref={containerRef} className="h-full w-full" />;
}
