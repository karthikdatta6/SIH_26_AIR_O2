# AIRO2 — Phase 4 Backend

## Overview

Production FastAPI backend for SIH 25178 — Ground-Level O₃ & NO₂ Forecasting System.

Consumes the frozen Phase 3 model bundles (`models/NO2/model.pkl`, `models/O3/model.pkl`) and serves forecasts via REST API.

---

## Requirements

- **Run from project root** (NOT from inside `backend/`)
- Python 3.11+
- GPU not required for inference (LightGBM CPU only at serving time)

---

## Setup

```powershell
# From the project root:
cd "c:\Users\saisu\OneDrive\Desktop\SIH 2026\PROJECT-AIRO2"

pip install -r backend/requirements.txt
```

---

## Run the API Server

```powershell
# From the project root:
uvicorn backend.app.main:app --reload --port 8000
```

The server will:
1. Load both model bundles once at startup (~5-10 seconds)
2. Log: `Models loaded in Xs: {'NO2': 'loaded', 'O3': 'loaded'}`
3. Begin serving requests

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Welcome message + links |
| GET | `/health` | API + model health check |
| GET | `/docs` | Interactive Swagger UI |
| GET | `/api/v1/model` | Phase 3 model metadata + performance |
| GET | `/api/v1/stations` | All 10 CPCB stations |
| GET | `/api/v1/stations/{id}` | Single station metadata |
| GET | `/api/v1/stations/{id}/current` | Latest observed reading (stub) |
| GET | `/api/v1/stations/{id}/forecast` | **12 model predictions (main endpoint)** |
| GET | `/api/v1/stations/{id}/forecast/explanation` | SHAP Model Drivers |

---

## Quick Test (after server is running)

```powershell
# Health check
curl http://localhost:8000/health

# Forecast for Anand Vihar (demo mode)
curl "http://localhost:8000/api/v1/stations/ANAND_VIHAR/forecast?use_demo=true"

# All stations
curl http://localhost:8000/api/v1/stations

# Model info
curl http://localhost:8000/api/v1/model
```

---

## Forecast Response Contract

Per the Phase 3 → Phase 4 Handoff Document:

- **6 discrete horizons only:** `+1h, +3h, +6h, +12h, +24h, +48h`
- **NOT 48 hourly points** — no interpolation
- **Unit:** always `ug/m3`
- **12 predictions per call:** 2 pollutants × 6 horizons
- **AQI** calculated using official CPCB breakpoints

---

## Run Tests (Golden Compatibility)

```powershell
# From project root:
pytest backend/tests/test_phase3_phase4_compatibility.py -v
```

Expected output: **13 tests passing** ✅

---

## Frontend Integration

See `PHASE_2_3_SUDHITH/6_PHASE_4_DEVELOPER_KIT/FRONTEND_INTEGRATION_SPEC.md`

The main forecast endpoint:
```
GET /api/v1/stations/ANAND_VIHAR/forecast?use_demo=true
```

Returns JSON with `forecasts.NO2[]` and `forecasts.O3[]`, each with 6 entries containing `horizon_hours`, `target_timestamp`, `prediction` (ug/m3), and `aqi`.

---

## File Structure

```
backend/
├── requirements.txt                           # Dependencies
├── README.md                                  # This file
└── app/
    ├── main.py                                # FastAPI app + model startup
    ├── config.py                              # All paths and constants
    ├── services/
    │   └── model_service.py                   # Core model loading + inference
    ├── routers/
    │   ├── stations.py                        # Station + forecast endpoints
    │   ├── model.py                           # Health + model info endpoints
    │   └── explain.py                         # SHAP Model Drivers endpoint
    ├── schemas/
    │   ├── station.py                         # Station Pydantic schemas
    │   └── forecast.py                        # Forecast response schemas
    └── utils/
        ├── aqi.py                             # Official CPCB AQI calculator
        └── feature_builder.py                 # 58-feature vector construction
```
