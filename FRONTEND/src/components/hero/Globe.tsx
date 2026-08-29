import { useEffect, useRef } from "react";
import * as THREE from "three";
import ThreeGlobe from "three-globe";
import { feature } from "topojson-client";
import type { GeometryCollection, Topology } from "topojson-specification";
import { geoBounds, geoContains } from "d3-geo";
import type { Feature, FeatureCollection, Geometry } from "geojson";
import { STATIONS } from "../../lib/stations";
import countriesTopology from "../../data/countries-110m.json";

const WORLD = feature(
  countriesTopology as unknown as Topology,
  (countriesTopology as unknown as Topology).objects.countries as GeometryCollection,
) as FeatureCollection;

// Bounding boxes let us cheaply reject most countries per sample point
// before running the expensive exact spherical point-in-polygon test.
const COUNTRY_BOXES = WORLD.features.map((f: Feature<Geometry>) => ({
  feature: f,
  bounds: geoBounds(f),
}));

function isLand(lat: number, lng: number): boolean {
  for (const { feature: f, bounds } of COUNTRY_BOXES) {
    const [[lonMin, latMin], [lonMax, latMax]] = bounds;
    if (lat < latMin || lat > latMax) continue;
    const lonOk = lonMin <= lonMax ? lng >= lonMin && lng <= lonMax : lng >= lonMin || lng <= lonMax;
    if (!lonOk) continue;
    if (geoContains(f, [lng, lat])) return true;
  }
  return false;
}

// Sample a lat/lng grid and keep only points that land on a country
// polygon — this is what draws the dotted continents on the globe.
function buildLandDots(): { lat: number; lng: number }[] {
  const dots: { lat: number; lng: number }[] = [];
  const step = 2.2;
  for (let lat = -80; lat <= 83; lat += step) {
    for (let lng = -180; lng < 180; lng += step) {
      if (isLand(lat, lng)) dots.push({ lat, lng });
    }
  }
  return dots;
}

function makeDotTexture(): THREE.Texture {
  const canvas = document.createElement("canvas");
  canvas.width = canvas.height = 32;
  const ctx = canvas.getContext("2d")!;
  const grad = ctx.createRadialGradient(16, 16, 0, 16, 16, 16);
  grad.addColorStop(0, "rgba(255,255,255,1)");
  grad.addColorStop(0.6, "rgba(255,255,255,0.7)");
  grad.addColorStop(1, "rgba(255,255,255,0)");
  ctx.fillStyle = grad;
  ctx.fillRect(0, 0, 32, 32);
  const tex = new THREE.CanvasTexture(canvas);
  tex.needsUpdate = true;
  return tex;
}

const DELHI = { lat: 28.6139, lng: 77.209 };

// Real upstream locations for the two off-network data sources AIRWATCH
// fuses with the CPCB ground readings — not decorative, these are the
// actual operating institutions behind Sentinel-5P and ERA5.
const DATA_LINKS = [
  { startLat: DELHI.lat, startLng: DELHI.lng, endLat: 49.8728, endLng: 8.6512 }, // ESA/ESOC, Darmstadt — Sentinel-5P/TROPOMI
  { startLat: DELHI.lat, startLng: DELHI.lng, endLat: 51.4416, endLng: -0.9391 }, // ECMWF, Reading — ERA5 reanalysis
];

const STATION_POINTS = STATIONS.map((s) => ({ lat: s.lat, lng: s.lon }));

const AMBER = "#ddb654";
const AMBER_DIM = "rgba(216, 178, 84, 0.05)";
const AMBER_ARC = "rgba(216, 178, 84, 0.85)";

export function Globe({ size = 460 }: { size?: number }) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(50, 1, 0.1, 2000);
    camera.position.set(0, 0, 305);

    const renderer = new THREE.WebGLRenderer({
      antialias: true,
      alpha: true,
      powerPreference: "high-performance",
    });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    renderer.setSize(size, size);
    container.appendChild(renderer.domElement);

    scene.add(new THREE.AmbientLight(0xffe9c2, 1.2));
    const keyLight = new THREE.PointLight(0xddb654, 1.6, 900);
    keyLight.position.set(-200, 140, 240);
    scene.add(keyLight);

    const globe = new ThreeGlobe()
      .showGlobe(true)
      .showAtmosphere(true)
      .atmosphereColor(AMBER)
      .atmosphereAltitude(0.22)
      .pointsData(STATION_POINTS)
      .pointColor(() => "#ecd48a")
      .pointAltitude(0.015)
      .pointRadius(0.35)
      .pointsMerge(true)
      .arcsData(DATA_LINKS)
      .arcColor(() => [AMBER_ARC, AMBER_DIM])
      .arcStroke(0.4)
      .arcAltitude(0.32)
      .arcDashLength(0.35)
      .arcDashGap(1.4)
      .arcDashInitialGap(() => Math.random() * 3)
      .arcDashAnimateTime(3800)
      .ringsData([{ lat: DELHI.lat, lng: DELHI.lng }])
      .ringColor(() => (t: number) => `rgba(216, 178, 84, ${1 - t})`)
      .ringMaxRadius(6)
      .ringPropagationSpeed(2.2)
      .ringRepeatPeriod(1400);

    const globeMaterial = globe.globeMaterial() as THREE.MeshPhongMaterial;
    globeMaterial.color = new THREE.Color(0x0a0a08);
    globeMaterial.transparent = true;
    globeMaterial.opacity = 0.6;
    globeMaterial.emissive = new THREE.Color(0x1a1408);
    globeMaterial.emissiveIntensity = 0.35;
    globeMaterial.shininess = 3;

    // Dotted continents — sampled land points rendered as one merged point
    // cloud (single draw call) rather than three-globe's hex-polygon layer,
    // which throws on this dataset's country geometries in this renderer.
    const dotPositions = new Float32Array(
      buildLandDots().flatMap(({ lat, lng }) => {
        const { x, y, z } = globe.getCoords(lat, lng, 0.006);
        return [x, y, z];
      }),
    );
    const dotGeometry = new THREE.BufferGeometry();
    dotGeometry.setAttribute("position", new THREE.BufferAttribute(dotPositions, 3));
    const dotMaterial = new THREE.PointsMaterial({
      color: new THREE.Color(0xecd48a),
      size: 2.6,
      sizeAttenuation: true,
      map: makeDotTexture(),
      transparent: true,
      opacity: 0.55,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
    });
    globe.add(new THREE.Points(dotGeometry, dotMaterial));

    // Bring Delhi to face the camera on load.
    globe.rotation.y = -(DELHI.lng * Math.PI) / 180 + Math.PI / 2;
    globe.rotation.x = 0.25;

    scene.add(globe);

    let raf = 0;
    let autoRotate = 0.0018;
    let dragging = false;
    let lastX = 0;
    let lastY = 0;
    let idleTimeout: ReturnType<typeof setTimeout> | null = null;
    let idle = true;

    function resumeIdle() {
      idle = false;
      if (idleTimeout) clearTimeout(idleTimeout);
      idleTimeout = setTimeout(() => {
        idle = true;
      }, 2200);
    }

    function onPointerDown(e: PointerEvent) {
      dragging = true;
      lastX = e.clientX;
      lastY = e.clientY;
      resumeIdle();
      renderer.domElement.setPointerCapture(e.pointerId);
    }
    function onPointerMove(e: PointerEvent) {
      if (!dragging) return;
      const dx = e.clientX - lastX;
      const dy = e.clientY - lastY;
      lastX = e.clientX;
      lastY = e.clientY;
      globe.rotation.y += dx * 0.005;
      globe.rotation.x = Math.max(-1.1, Math.min(1.1, globe.rotation.x + dy * 0.005));
      resumeIdle();
    }
    function onPointerUp() {
      dragging = false;
    }

    const el = renderer.domElement;
    el.style.touchAction = "none";
    el.addEventListener("pointerdown", onPointerDown);
    el.addEventListener("pointermove", onPointerMove);
    el.addEventListener("pointerup", onPointerUp);
    el.addEventListener("pointerleave", onPointerUp);

    function animate() {
      if (!dragging && idle) globe.rotation.y += autoRotate;
      renderer.render(scene, camera);
      raf = requestAnimationFrame(animate);
    }

    // Fully stop rendering (rather than let the browser throttle a
    // background-tab rAF loop indefinitely) and cleanly resume on return —
    // avoids leaving the GPU context in a degraded/throttled state.
    function onVisibilityChange() {
      if (document.hidden) {
        cancelAnimationFrame(raf);
      } else {
        cancelAnimationFrame(raf);
        raf = requestAnimationFrame(animate);
      }
    }
    document.addEventListener("visibilitychange", onVisibilityChange);

    raf = requestAnimationFrame(animate);

    return () => {
      cancelAnimationFrame(raf);
      if (idleTimeout) clearTimeout(idleTimeout);
      document.removeEventListener("visibilitychange", onVisibilityChange);
      el.removeEventListener("pointerdown", onPointerDown);
      el.removeEventListener("pointermove", onPointerMove);
      el.removeEventListener("pointerup", onPointerUp);
      el.removeEventListener("pointerleave", onPointerUp);
      container.removeChild(el);
      renderer.dispose();
      renderer.forceContextLoss();
    };
  }, [size]);

  return (
    <div
      ref={containerRef}
      style={{ width: size, height: size, cursor: "grab" }}
      className="max-w-full"
    />
  );
}
