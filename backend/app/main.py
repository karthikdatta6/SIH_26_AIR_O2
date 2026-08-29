"""
main.py - AIRO2 FastAPI Application Entry Point.

Loads both Phase 3 production model bundles ONCE at startup (not per request).
Per handoff doc Section 39: DO NOT load 82 MB NO2 + 34 MB O3 bundles on every request.

Endpoints exposed:
  GET /                                                   - Interactive Web Dashboard & Welcome
  GET /dashboard                                          - Complete Animated Decision Support UI
  GET /health                                             - Model + API health check
  GET /api/v1/model                                       - Phase 3 model metadata
  GET /api/v1/stations                                    - All 10 canonical stations
  GET /api/v1/stations/{station_id}                       - Single station info
  GET /api/v1/stations/{station_id}/forecast              - Phase 3 forecasts (12 predictions)
  GET /api/v1/stations/{station_id}/forecast/explanation  - SHAP Model Drivers
  GET /api/v1/stations/{station_id}/report/pdf            - 1-Click Official CPCB PDF Dossier
  POST /api/v1/simulate                                   - "What-If" CAQM / GRAP Policy Simulator
  GET /api/v1/spatial/heatmap                             - 2D Continuous Spatial Pollution Heatmap
  GET /api/v1/alerts/active                               - Early Warning Proactive Web Alerts
  POST /api/v1/alerts/simulate                            - Live Demo Emergency Alert Trigger
  GET /api/v1/live/stations/{id}/forecast                 - Real-time Open-Meteo Live Ingestion Forecast
"""

import os
import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.app.services.model_service import ModelService
from backend.app.services.forecast_database import DB_PATH
from backend.app.routers import stations, model, explain, alerts, simulate, spatial, report
from LIVE_DATA.live_api_router import live_router
from backend.app.middleware.security import (
    SecurityHeadersMiddleware,
    RateLimiterMiddleware,
    RequestCorrelationMiddleware,
    PayloadSizeLimitMiddleware
)
from backend.app.middleware.error_handler import register_error_handlers

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("airo2.main")

_STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load Phase 3 models once at startup. Keep in memory throughout lifecycle."""
    logger.info("=" * 60)
    logger.info("AIRO2 API starting up — loading Phase 3 model bundles...")
    t0 = time.time()
    ModelService.load_models()
    elapsed = time.time() - t0
    health = ModelService.health_check()
    logger.info(f"Models loaded in {elapsed:.2f}s: {health}")
    logger.info("=" * 60)

    task = None
    if os.getenv("PROVIDER_MODE", "historical").lower().strip() == "live":
        import asyncio
        from backend.app import scheduler
        task = asyncio.create_task(scheduler.run_forever())
        logger.info(f"Started background forecast refresh loop (every {scheduler.REFRESH_MINUTES}m)")

    yield

    if task:
        task.cancel()
    logger.info("AIRO2 API shutting down.")


app = FastAPI(
    title="AIRO2 — Institutional Ground-Level O3 & NO2 Forecasting API",
    description=(
        "SIH 25178 enterprise forecast service.\n\n"
        "**Models:** LightGBM + BiLSTM+Attention + NNLS Simplex Stacking\n"
        "**Pollutants:** NO2, O3\n"
        "**Horizons:** +1h, +3h, +6h, +12h, +24h, +48h (6 discrete checkpoints)\n"
        "**Units:** ug/m3 (native model output)\n"
        "**Security Tier:** Institutional Rate Limiting, CSP, HSTS, Sanitized Envelopes\n"
        "**Stations:** 10 CPCB monitoring stations in Delhi NCR\n\n"
        "Per SIH 25178 Phase 3 -> Phase 4 Production Contract."
    ),
    version="1.1.0",
    lifespan=lifespan,
)

# 1. Mount Global Enterprise Error Envelopes
register_error_handlers(app)

# 2. Add Security & Observability Middlewares (Outer-to-Inner Order)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimiterMiddleware, requests_per_minute=180)
app.add_middleware(PayloadSizeLimitMiddleware, max_payload_bytes=2 * 1024 * 1024)
app.add_middleware(RequestCorrelationMiddleware)

# 3. CORS Policy
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-Response-Time-Ms"],
)

# Mount Static Files
if os.path.exists(_STATIC_DIR):
    app.mount("/static", StaticFiles(directory=_STATIC_DIR), name="static")

# Include all routers
app.include_router(stations.router)
app.include_router(model.router)
app.include_router(explain.router)
app.include_router(alerts.router)
app.include_router(simulate.router)
app.include_router(spatial.router)
app.include_router(report.router)
app.include_router(live_router)


# ======================================================================================
# ENTERPRISE OBSERVABILITY & HEALTH PROBES
# ======================================================================================

@app.get("/healthz", tags=["Observability"])
def liveness_probe():
    """Kubernetes / Cloud Liveness Probe confirming web server is responding."""
    return {"status": "healthy", "service": "airo2_forecaster", "timestamp": time.time()}


@app.get("/readyz", tags=["Observability"])
def readiness_probe():
    """Kubernetes / Cloud Readiness Probe confirming models and database are ready for traffic."""
    model_health = ModelService.health_check()
    models_ready = all(v == "loaded" for v in model_health.values())
    db_ready = os.path.exists(DB_PATH)
    
    status_code = 200 if (models_ready and db_ready) else 503
    return {
        "status": "ready" if status_code == 200 else "degraded",
        "models": model_health,
        "database_store": "connected" if db_ready else "initializing",
        "ready": status_code == 200
    }


@app.get("/", tags=["Dashboard UI"])
def root():
    """Serves the complete interactive animated web dashboard."""
    index_path = os.path.join(_STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {
        "service": "AIRO2 Air Quality Forecasting API",
        "docs": "/docs",
        "health": "/health",
        "healthz": "/healthz",
        "readyz": "/readyz",
        "dashboard": "/dashboard"
    }


@app.get("/dashboard", tags=["Dashboard UI"])
def get_dashboard():
    """Serves the complete interactive animated web dashboard."""
    index_path = os.path.join(_STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"error": "Dashboard HTML not found"}
