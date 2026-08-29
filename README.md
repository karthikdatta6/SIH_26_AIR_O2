# AIRO2 — Next-Gen AI/ML Forecasting System for Ground-Level Ozone ($O_3$) & Nitrogen Dioxide ($NO_2$)

[![Smart India Hackathon 2026](https://img.shields.io/badge/SIH%202026-Problem%20Statement%2025178-0052CC.svg)](https://www.sih.gov.in/)
[![FastAPI Backend](https://img.shields.io/badge/Backend-FastAPI%20%7C%20Uvicorn-009688.svg)](https://fastapi.tiangolo.com/)
[![React Frontend](https://img.shields.io/badge/Frontend-React%2018%20%7C%20TypeScript%20%7C%20Vite-61DAFB.svg)](https://react.dev/)
[![ML Architecture](https://img.shields.io/badge/ML%20Ensemble-LightGBM%20%2B%20BiLSTM%20%2B%20NNLS-FF6F00.svg)](https://lightgbm.readthedocs.io/)
[![Validation Pass](https://img.shields.io/badge/Golden%20Compatibility-100%25%20Passed%20(21%2F21)-brightgreen.svg)]()

> **SIH 25178 Enterprise Solution**: High-resolution, multi-modal atmospheric chemistry forecaster combining in-situ CPCB ground sensors, ECMWF ERA5 reanalysis meteorology, Sentinel-5P TROPOMI satellite columns, and static urban GIS features to deliver sub-10ms discrete horizon predictions up to 48 hours in advance.

---

## Table of Contents

1. [System Overview & Key Features](#1-system-overview--key-features)
2. [End-to-End System Architecture](#2-end-to-end-system-architecture)
3. [Repository Structure](#3-repository-structure)
4. [Dataset & Harmonization (Phase 1 & 2)](#4-dataset--harmonization-phase-1--2)
5. [Machine Learning & Stacking Architecture (Phase 3)](#5-machine-learning--stacking-architecture-phase-3)
6. [Empirical Benchmark Results](#6-empirical-benchmark-results)
7. [Production Backend & REST API (Phase 4)](#7-production-backend--rest-api-phase-4)
8. [Interactive Frontend Command Center (Phase 7)](#8-interactive-frontend-command-center-phase-7)
9. [Quickstart & Execution Guide](#9-quickstart--execution-guide)
10. [Automated Verification & Golden Tests](#10-automated-verification--golden-tests)
11. [Compliance & Handoff Checklist](#11-compliance--handoff-checklist)

---

## 1. System Overview & Key Features

* **Multi-Horizon Forecasting**: Predicts ground-level concentrations ($\mu g/m^3$) and CPCB AQI sub-indices across **6 discrete non-recursive checkpoints**:
  $$	ext{Horizons: } +1	ext{h},\; +3	ext{h},\; +6	ext{h},\; +12	ext{h},\; +24	ext{h},\; +48	ext{h}$$
* **Multi-Modal Data Fusion**: Harmonizes ground measurements across 10 Delhi NCR stations with 31 meteorological features from ECMWF ERA5 and spaceborne Sentinel-5P TROPOMI tropospheric $NO_2$ & total column $O_3$.
* **Stacked Hybrid Ensemble**: Blends Gradient Boosted Trees (LightGBM) with Bidirectional LSTM + Temporal Self-Attention via a Non-Negative Least Squares (NNLS) Convex Simplex meta-learner ($\sum w_i = 1, w_i \ge 0$).
* **Atmospheric Physics Integration**: Embedded diurnal cycle calibration capturing photolytic ozone peaks, nighttime NO-titration sinks, and boundary layer ventilation dynamics.
* **Institutional Governance**: Real-time SHAP feature attributions, automated early warning webhooks, spatial Gaussian grid interpolation, and interactive policy "What-If" simulation.

---

## 2. End-to-End System Architecture

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                 DATA INGESTION LAYERS                                   │
│  [CPCB Ground Stations]   [ECMWF ERA5 Met]   [Sentinel-5P TROPOMI]   [Static Urban GIS]│
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                             PHASE 2: DATASET HARMONIZATION                              │
│       Spatial Nearest-Neighbor / IDW Matching  •  Zero Future Leakage Verification     │
│             138 Domain Features (Multi-Scale Lags, Rolling Stats, Cyclical Solar)      │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              PHASE 3: ML & DEEP LEARNING                                │
│   ┌───────────────────────────┐           ┌──────────────────────────────────────┐     │
│   │   LightGBM Direct GBDTs   │           │    PyTorch BiLSTM + Self-Attention   │     │
│   │  (Quantile/Huber Losses)  │           │      (Sequential Dynamics Model)     │     │
│   └─────────────┬─────────────┘           └──────────────────┬───────────────────┘     │
│                 │                                            │                         │
│                 └─────────────────────┬──────────────────────┘                         │
│                                       ▼                                                │
│                 ┌───────────────────────────────────────────┐                          │
│                 │   NNLS Convex Simplex Meta-Stacking       │                          │
│                 │  + Diurnal Photochemical Solar Calibration│                          │
│                 └─────────────────────┬─────────────────────┘                          │
└───────────────────────────────────────┼────────────────────────────────────────────────┘
                                        ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                     PHASE 4: PRODUCTION BACKEND SERVICE (FastAPI)                      │
│      • Sub-10ms Inference Runtime         • Background Auto-Scheduler & SQLite DB      │
│      • SHAP Attribution API               • Real-Time Early Warning & Webhooks         │
│      • 2D Spatial Heatmaps                • Policy "What-If" Emission Simulator        │
└───────────────────────────────────────┬────────────────────────────────────────────────┘
                                        ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        PHASE 7: INTERACTIVE FRONTEND (React 18)                        │
│      • Real-Time Delhi Leaflet GIS Map    • Station Horizon Analytics & Telemetry      │
│      • 3D Atmospheric Globe View          • CPCB NAQI Health Advisory Cards            │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Repository Structure

```
SIH_26_AIR_O2/
├── MASTER_PHASE1_CPCB_AND_ERA5.md             # Phase 1 Data Ingestion Architecture
├── MASTER_PHASE1_SENTINEL5P_AND_GEOSPATIAL.md # Satellite and Geospatial Specification
├── README.md                                  # Master Project Documentation
├── FOLDER STRUCTURE.md                        # Complete Itemized File-by-File Directory
│
├── DATASET FUSION/                            # Phase 2 Harmonization & ETL Pipelines
│   ├── config/ (phase2.yaml, stations.csv)
│   ├── docs/ (Methodology & QA specifications)
│   ├── metadata/ (data_dictionary.csv, station coordinates)
│   └── scripts/ (build_fused_dataset.py, leakage_check.py)
│
├── DATASET VALIDATION/                        # Phase 2 Rigorous QA & Audit Benchmark Reports
│   ├── 01_SOURCE_STREAM_VALIDATORS/
│   ├── 02_FUSION_INTEGRITY_AND_LEAKAGE/
│   ├── 03_QUALITY_AND_AUDIT_REPORTING/
│   ├── DOCUMENTATION/
│   └── RESULTS/ (12 QA benchmark CSV reports)
│
├── FINAL DATASET/                             # Production Parquet Datasets & Data Dictionaries
│   ├── station_hourly_fused.parquet           # Fused hourly dataset (2019-2024)
│   ├── features_engineered.parquet            # 138-feature engineered dataset
│   ├── station_static_features.parquet        # Station GIS features
│   └── metadata/ & quality_reports/
│
├── MODEL_ARCHITECTURE_RESEARCH/               # Theoretical Formulations & Comparative Whitepapers
│   ├── Photochemical Leighton relationship & Diurnal cycle studies
│   ├── GBDTs vs RNNs vs Transformers comparative benchmarks
│   └── Real-time live data ingestion trade-off analyses
│
├── MODEL CODE/                                # Phase 3 ML/DL Training Pipelines & Model Bundles
│   ├── 01_MACHINE_LEARNING_MODELS/ (LightGBM multi-horizon models)
│   ├── 02_DEEP_LEARNING_MODELS/ (PyTorch BiLSTM + Self-Attention)
│   ├── 03_ENSEMBLE_AND_META_STACKING/ (NNLS Convex Simplex Stacking)
│   ├── 04_DIURNAL_CALIBRATION_MODEL/ (Solar angle curve calibrations)
│   ├── 05_TRAINING_PIPELINE_AND_CV/ (Expanding-window CV, EDA, SHAP)
│   ├── 06_PRODUCTION_INFERENCE_SERVICES/ (AQI calculator, feature builder)
│   ├── 07_PRODUCTION_MODEL_BUNDLES/ (Serialized NO₂ & O₃ models + schemas)
│   └── 08_MODEL_DOCUMENTATION/ (Architecture, specs, contracts, handoffs)
│
├── MODEL RESULTS/                             # Phase 3 Benchmark Metrics & Visualizations
│   ├── 01_BENCHMARK_AND_METRICS_CSVS/ (Performance summaries per horizon & station)
│   ├── 02_VISUALIZATIONS_AND_SHAP/ (Time-series plots, SHAP beeswarm figures)
│   └── 03_EVALUATION_AND_ACCURACY_REPORTS/ (Executive audit & evaluation reports)
│
├── MODEL OUTPUT VALIDATION/                   # Phase 3 -> Phase 4 Golden Verification Suite
│   ├── 01_GOLDEN_COMPATIBILITY_TESTS/ (Golden inputs/expected outputs)
│   ├── 02_PHYSICAL_PLAUSIBILITY_AND_INVARIANTS/ (Scientific checklists)
│   └── 03_READINESS_AND_FIT_FOR_USE_CERTIFICATES/ (Formal fit-for-use certificates)
│
├── PRODUCTION BACKEND SERVICE/ (and backend/) # Phase 4 Production FastAPI REST Server
│   ├── app/routers/ (stations, explain, simulate, spatial, alerts, model, report)
│   ├── app/providers/live/ (CPCB, CAMS, Sentinel-5P, Open-Meteo Weather)
│   ├── app/services/ (Inference runtime, forecast SQLite DB, live feature service)
│   ├── app/scheduler.py (Automated hourly forecast & ingestion scheduler)
│   ├── app/static/index.html (Interactive static control center dashboard)
│   └── tests/ (Unit, integration, and golden compatibility tests)
│
└── FRONTEND/                                  # Phase 7 React + TypeScript + Vite Web App
    ├── src/components/map/ (RealDelhiMap with Leaflet GIS tiles & radar overlay)
    ├── src/components/station/ (StationDashboard, ForecastPanel for +1h to +48h)
    ├── src/components/hero/ (Interactive 3D rotating Globe & live telemetry)
    └── src/lib/ (REST API client, CPCB NAQI calculation, GeoJSON boundaries)
```

For full line-by-line documentation of every individual file, see [FOLDER STRUCTURE.md](FOLDER%20STRUCTURE.md).

---

## 4. Dataset & Harmonization (Phase 1 & 2)

* **10 Target CPCB Monitoring Stations**: Anand Vihar, ITO, Okhla Phase-2, Aya Nagar, R.K. Puram, Major Dhyan Chand National Stadium, Mandir Marg, Punjabi Bagh, Jahangirpuri, Dwarka Sector-8.
* **Temporal Range**: 2019 to 2024 continuous hourly observations ($>52,000$ timesteps per station).
* **Multi-Modal Data Streams**:
  1. *CPCB In-Situ Sensors*: $NO_2$, $O_3$, $PM_{2.5}$, $PM_{10}$, $CO$, $SO_2$, $NO$, $NH_3$ ($\mu g/m^3$).
  2. *ECMWF ERA5 Reanalysis*: Temperature ($2m$), Surface Pressure, Relative Humidity, $U/V$ Wind Vectors ($10m$), Planetary Boundary Layer Height ($blh$), Solar Radiation ($ssrd$).
  3. *Sentinel-5P TROPOMI*: Tropospheric $NO_2$ column, Total column $O_3$, Carbon Monoxide, Formaldehyde ($HCHO$).
  4. *Static Geospatial*: DEM elevation, road length within 1km/3km buffers, proximity to railways, commercial/residential land-use ratios.
* **Zero-Leakage Assurance**: Verified with automated expanding-window temporal boundary checks ensuring no future information bleeds into training folds.

---

## 5. Machine Learning & Stacking Architecture (Phase 3)

### Multi-Horizon Direct Strategy
Rather than autoregressive recursive chaining (which accumulates compound prediction errors across horizons), AIRO2 trains dedicated multi-horizon regressors for each discrete horizon:
$$\hat{Y}_{t+h} = f_h(X_t), \quad h \in \{1, 3, 6, 12, 24, 48\}$$

### Stacking Formulation
Individual model predictions are combined via constrained Non-Negative Least Squares (NNLS) on out-of-fold validation sets:
$$\min_{w} \|Y - \sum_{m} w_m \hat{Y}_m\|_2^2 \quad 	ext{subject to } \sum w_m = 1,\; w_m \ge 0$$

### Diurnal Solar Cycle Calibration
Post-processing adjustments apply solar zenith angle $	heta_z$ and boundary layer scaling to capture photochemical peaks without unbounded extrapolation:
$$C_{	ext{calibrated}}(t) = C_{	ext{ensemble}}(t) \cdot \left[1 + \gamma \cdot \cos\left(rac{2\pi(t - \phi)}{24}ight)ight]$$

---

## 6. Empirical Benchmark Results

### $NO_2$ & $O_3$ Model Performance Across Horizons
| Horizon | $NO_2$ $R^2$ Score | $NO_2$ RMSE ($\mu g/m^3$) | $O_3$ $R^2$ Score | $O_3$ RMSE ($\mu g/m^3$) | Latency (ms) |
|---|---|---|---|---|---|
| **+1h** | **0.912** | 6.42 | **0.894** | 5.81 | 1.8 ms |
| **+3h** | **0.884** | 7.91 | **0.867** | 7.14 | 1.9 ms |
| **+6h** | **0.841** | 9.85 | **0.825** | 8.92 | 2.1 ms |
| **+12h** | **0.803** | 11.42 | **0.789** | 10.35 | 2.2 ms |
| **+24h** | **0.768** | 13.10 | **0.751** | 11.90 | 2.4 ms |
| **+48h** | **0.714** | 15.65 | **0.702** | 13.88 | 2.8 ms |

* **Peak-Episode Detection F1-Score**: $0.874$ (accurately alerts during extreme winter smog and harvest stubble-burning episodes).
* **Inference Speed**: $<5	ext{ms}$ per full 12-prediction forecast call (well within the $<200	ext{ms}$ handoff SLA).

---

## 7. Production Backend & REST API (Phase 4)

The FastAPI server provides production endpoints with enterprise security, rate limiting, and standard JSON schemas:

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/healthz` | Liveness and readiness probe for Kubernetes / cloud deployments |
| `GET` | `/api/v1/model` | Model version, metadata, feature schemas, and validation metrics |
| `GET` | `/api/v1/stations` | List of all 10 CPCB monitoring stations with live health status |
| `GET` | `/api/v1/stations/{id}/forecast` | **Main Endpoint**: 12 discrete predictions (2 pollutants $	imes$ 6 horizons) + AQI |
| `GET` | `/api/v1/stations/{id}/forecast/explanation` | Feature contribution ranking and SHAP values for predictions |
| `POST` | `/api/v1/simulate` | Policy sandbox evaluating traffic reduction and industrial emission cuts |
| `GET` | `/api/v1/spatial` | 2D continuous air quality heatmap and hotspot cluster coordinates |
| `POST` | `/api/v1/alerts/subscribe` | Webhook subscription for automated threshold breach notifications |
| `GET` | `/api/v1/report/daily` | Automated daily air quality briefing report generation (PDF / CSV) |

---

## 8. Interactive Frontend Command Center (Phase 7)

Built with **React 18**, **TypeScript**, **Vite**, **TailwindCSS**, and **Leaflet**:
* **Interactive GIS Map**: Real-time Leaflet map of Delhi NCR with color-coded station pins, pulse animations, and radar scanlines.
* **Horizon Viewer**: Tabbed inspection for $+1	ext{h}$, $+3	ext{h}$, $+6	ext{h}$, $+12	ext{h}$, $+24	ext{h}$, and $+48	ext{h}$ pollutant trajectories.
* **3D Atmospheric Globe**: D3-Geo rotating Earth visualization showcasing regional circulation patterns.
* **Live Telemetry & AQI Gauge**: Displays CPCB AQI categories (Good, Satisfactory, Moderate, Poor, Very Poor, Severe) with health advisories.
* **Fail-Safe Offline Mode**: Seamless fallback to high-fidelity mock datasets when operating in offline demo environments.

---

## 9. Quickstart & Execution Guide

### Prerequisites
* Python 3.10+
* Node.js 18+ & NPM

---

### Step 1: Start the Backend Service
```powershell
# Navigate to the repository root
cd "C:\Users\saisu\OneDrive\Desktop\AIRO2SIH\SIH_26_AIR_O2"

# Install backend dependencies
pip install -r "PRODUCTION BACKEND SERVICE/requirements.txt"

# Launch FastAPI server
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```
* Interactive Swagger Docs: `http://localhost:8000/docs`
* Built-in Web UI: `http://localhost:8000/static/index.html`

---

### Step 2: Start the Frontend Application
```powershell
# Navigate to FRONTEND directory
cd "C:\Users\saisu\OneDrive\Desktop\AIRO2SIH\SIH_26_AIR_O2\FRONTEND"

# Install NPM dependencies
npm install

# Start Vite development server
npm run dev
```
* Access Command Center: `http://localhost:5173`

---

## 10. Automated Verification & Golden Tests

Run the complete test suite to verify 100% compliance across model outputs, backend routes, and live providers:

```powershell
# Run all 21 automated tests from the repository root
pytest backend/tests -v
```

### Verified Test Categories:
1. **Golden Compatibility Suite** (13 tests): Asserts that Phase 4 predictions match Phase 3 frozen models within $\le 0.001\,\mu g/m^3$ tolerance.
2. **Live Observation Pipeline Suite** (5 tests): Tests data store caching, missing data fallbacks, and CPCB priority selection.
3. **Early Warning & Webhook Suite** (3 tests): Verifies location-agnostic geocoding, multi-horizon alert triggering, and webhook dispatching.

---

## 11. Compliance & Handoff Checklist

- [x] **Strict 6-Horizon Output**: Emits $+1	ext{h}, +3	ext{h}, +6	ext{h}, +12	ext{h}, +24	ext{h}, +48	ext{h}$ discrete checkpoints without recursive chaining.
- [x] **58-Feature Schema Integrity**: Feature vectors match schema order strictly.
- [x] **Non-Negative Guarantees**: Enforces physical boundaries ($O_3 \ge 0, NO_2 \ge 0$).
- [x] **Standard Physical Units**: All concentrations reported natively in $\mu g/m^3$.
- [x] **Official CPCB AQI Calculation**: Exact linear interpolation sub-index calculation with dominant pollutant identification.
- [x] **Zero Future Leakage**: Temporal expanding-window cross-validation certified.
- [x] **Production Serialization**: Self-contained pickle bundles, JSON schemas, and training metadata included.
- [x] **Enterprise Security**: Rate limiting, CORS, CSP security headers, and structured error envelopes.

---

## 12. Team & Acknowledgments

* **Hackathon**: Smart India Hackathon (SIH 2026)
* **Problem Statement**: SIH 25178
* **Data Sources**: Central Pollution Control Board (CPCB), European Centre for Medium-Range Weather Forecasts (ECMWF ERA5), European Space Agency (Sentinel-5P TROPOMI), Open-Meteo Air Quality API.
