# AIRO2 — COMPLETE REPOSITORY FOLDER STRUCTURE & FILE DIRECTORY

**Project**: Smart India Hackathon (SIH 25178) — Ground-Level Ozone ($O_3$) and Nitrogen Dioxide ($NO_2$) Multi-Horizon Forecasting System  
**Repository**: `SIH_26_AIR_O2`  
**Generated Date**: August 2026  

---

## 1. High-Level Architectural Tree

```
SIH_26_AIR_O2/
├── MASTER_PHASE1_CPCB_AND_ERA5.md
├── MASTER_PHASE1_SENTINEL5P_AND_GEOSPATIAL.md
├── README.md
├── FOLDER STRUCTURE.md
│
├── DATASET FUSION/                          # Phase 2 Data Harmonization & Spatio-Temporal Pipeline
│   ├── config/
│   ├── docs/
│   ├── metadata/
│   └── scripts/
│
├── DATASET VALIDATION/                      # Phase 2 Rigorous QA, Leakage Audit & Stream Validators
│   ├── 01_SOURCE_STREAM_VALIDATORS/
│   ├── 02_FUSION_INTEGRITY_AND_LEAKAGE/
│   ├── 03_QUALITY_AND_AUDIT_REPORTING/
│   ├── DOCUMENTATION/
│   └── RESULTS/
│
├── FINAL DATASET/                           # Harmonized Production Parquet Datasets & Data Dictionaries
│   ├── metadata/
│   └── quality_reports/
│
├── MODEL_ARCHITECTURE_RESEARCH/             # Atmospheric Physics & Multi-Model Research Whitepapers
│
├── MODEL CODE/                              # Phase 3 Machine Learning & Deep Learning Core Pipelines
│   ├── 01_MACHINE_LEARNING_MODELS/
│   ├── 02_DEEP_LEARNING_MODELS/
│   ├── 03_ENSEMBLE_AND_META_STACKING/
│   ├── 04_DIURNAL_CALIBRATION_MODEL/
│   ├── 05_TRAINING_PIPELINE_AND_CV/
│   ├── 06_PRODUCTION_INFERENCE_SERVICES/
│   ├── 07_PRODUCTION_MODEL_BUNDLES/
│   └── 08_MODEL_DOCUMENTATION/
│
├── MODEL RESULTS/                           # Phase 3 Validation Metrics, SHAP Plots & Evaluation Audits
│   ├── 01_BENCHMARK_AND_METRICS_CSVS/
│   ├── 02_VISUALIZATIONS_AND_SHAP/
│   └── 03_EVALUATION_AND_ACCURACY_REPORTS/
│
├── MODEL OUTPUT VALIDATION/                 # Phase 3 -> Phase 4 Golden Verification & Fit-for-Use Certs
│   ├── 01_GOLDEN_COMPATIBILITY_TESTS/
│   ├── 02_PHYSICAL_PLAUSIBILITY_AND_INVARIANTS/
│   └── 03_READINESS_AND_FIT_FOR_USE_CERTIFICATES/
│
├── PRODUCTION BACKEND SERVICE/              # Phase 4 Production FastAPI REST Server, Live Ingestion & Scheduler
│   ├── app/
│   │   ├── api/
│   │   ├── data/
│   │   ├── middleware/
│   │   ├── providers/
│   │   ├── routers/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── static/
│   │   └── utils/
│   └── tests/
│
└── FRONTEND/                                # Phase 7 React + TypeScript + Vite Interactive Control Center
    ├── public/
    └── src/
        ├── components/
        ├── data/
        └── lib/
```

---

## 2. Detailed Folder and File Breakdown

### Root Directory
| File | Description |
|---|---|
| `MASTER_PHASE1_CPCB_AND_ERA5.md` | Master specification document for Phase 1 data ingestion, detailing ground-truth Central Pollution Control Board (CPCB) monitoring stations and ECMWF ERA5 meteorological reanalysis data processing. |
| `MASTER_PHASE1_SENTINEL5P_AND_GEOSPATIAL.md` | Master specification document for Sentinel-5P TROPOMI satellite columns ($NO_2$, $O_3$) and static GIS layers (DEM elevation, road network density, population density, land use). |
| `README.md` | Entry-point repository overview describing the SIH AIRO2 mission, technical stack, system architecture, and setup instructions. |
| `FOLDER STRUCTURE.md` | Exhaustive directory tree documentation detailing every folder, module, and file in the codebase. |

---

### `DATASET FUSION/`
*Phase 2 multi-stream data harmonization, temporal alignment, and spatial aggregation engine.*

| Path / File | Purpose & Contents |
|---|---|
| `README.md` | Setup instructions, usage manual, and architecture overview for the Phase 2 dataset fusion pipeline. |
| `requirements.txt` | Python package dependencies (`pandas`, `pyarrow`, `pyyaml`, `scipy`, `numpy`) required to run dataset fusion. |
| `config/phase2.yaml` | Master pipeline configuration specifying date ranges (2019–2024), coordinate bounds, resolution grids, feature definitions, and thresholds. |
| `config/stations.csv` | Reference catalog of the 10 target Delhi NCR CPCB stations with station codes, geographical coordinates (lat/lon), and site classifications. |
| `docs/PHASE_2_COMPLETE_DOCUMENTATION.md` | Comprehensive documentation of data processing rules, outlier rejection filters, missing data interpolation logic, and QA/QC gates. |
| `docs/PHASE_2_FUSION_METHODOLOGY.md` | Mathematical and algorithmic specification of spatial nearest-neighbor / inverse-distance weighting (IDW) and hourly timestamp alignment. |
| `metadata/data_dictionary.csv` | Field-by-field schema dictionary defining feature names, physical units, data types, and source stream origins. |
| `metadata/station_locations.csv` | Official latitude and longitude coordinates for all monitoring sites. |
| `metadata/station_metadata.csv` | Detailed station metadata including elevation, surrounding land use (industrial, residential, traffic), and sensor commissioning details. |
| `scripts/build_fused_dataset.py` | Core ETL script merging raw CPCB ground measurements, ERA5 meteorology, Sentinel-5P satellite rasters, and GIS static layers into unified Parquet tables. |
| `scripts/run_phase2_pipeline.py` | CLI orchestrator executing the entire extraction, harmonization, feature construction, and audit verification pipeline end-to-end. |
| `scripts/validate_inputs.py` | Pre-fusion sanity checker verifying raw file existence, format validity, column headers, and timestamp continuity. |
| `scripts/validate_cpcb.py` | Ground truth validator screening CPCB sensor data for negative values, stuck-sensor values, physical limit exceedances, and sensor dropouts. |
| `scripts/validate_era5.py` | Meteorology validator checking physical plausibility of temperature ($K$), wind $u/v$ components, boundary layer height ($m$), and relative humidity. |
| `scripts/validate_sentinel5p.py` | Satellite product QA filter enforcing `qa_value >= 0.5` on TROPOMI tropospheric $NO_2$ and total column $O_3$ granules. |
| `scripts/validate_geospatial.py` | GIS validator verifying CRS coordinate reference systems, bounding box limits, and spatial alignment across Delhi NCR. |
| `scripts/leakage_check.py` | Temporal integrity test ensuring that rolling aggregates and lag features do not leak future information into historical records. |
| `scripts/missingness_analysis.py` | Audit script computing missing value distributions across all sensors, stations, and temporal blocks. |
| `scripts/independent_audit.py` | Autonomous integrity checker evaluating value distributions, z-score bounds, and statistical consistency across the fused dataset. |

---

### `DATASET VALIDATION/`
*Comprehensive QA testing suites, independent integrity audits, and empirical verification reports.*

| Path / File | Purpose & Contents |
|---|---|
| `README.md` | Guide to the validation suite, testing frameworks, benchmark thresholds, and execution instructions. |
| `run_all_validations.py` | Master validation test harness executing all source validators, leakage audits, and quality report generators in automated sequence. |
| `01_SOURCE_STREAM_VALIDATORS/` | Modular validators for CPCB (`validate_cpcb.py`), ERA5 (`validate_era5.py`), Geospatial (`validate_geospatial.py`), Sentinel-5P (`validate_sentinel5p.py`), and Inputs (`validate_inputs.py`). |
| `02_FUSION_INTEGRITY_AND_LEAKAGE/` | Deep integrity verification scripts: `leakage_check.py` (zero temporal leakage), `missingness_analysis.py` (data completeness), `independent_audit.py` (cross-stream consistency), and `inspection_station_pilot.py` (single-station deep dive). |
| `03_QUALITY_AND_AUDIT_REPORTING/` | Automated report compilation scripts (`audit_cpcb.py`, `build_download_log.py`, `build_quality_report.py`, `compile_reports.py`, `final_ultra_report.py`, `full_quality_analysis.py`, `generate_master_report.py`, `merge_station_logs.py`). |
| `DOCUMENTATION/PHASE_2_AUDIT_REPORT.md` | Formal audit report certifying 100% data fidelity, zero future leakage, and statistical completeness. |
| `DOCUMENTATION/PHASE_2_FUSION_METHODOLOGY.md` | Comprehensive methodological whitepaper on multi-modal spatio-temporal fusion. |
| `RESULTS/` | 12 published validation benchmark CSV reports: `cpcb_quality_report.csv`, `era5_quality_report.csv`, `fusion_quality_report.csv`, `geospatial_quality_report.csv`, `independent_dataset_audit.csv`, `leakage_report.csv`, `missingness_report.csv`, `phase2_input_inventory.csv`, `sentinel5p_quality_report.csv`, `spatial_matching_report.csv`, `station_coverage_report.csv`, and `temporal_matching_report.csv`. |

---

### `FINAL DATASET/`
*Production-ready Parquet tables, feature stores, and authoritative metadata dictionaries.*

| Path / File | Purpose & Contents |
|---|---|
| `README.md` | Parquet dataset documentation, row counts, memory footprints, and loading code snippets in Python/DuckDB. |
| `station_hourly_fused.parquet` | Master hourly fused dataset (2019–2024) across 10 Delhi CPCB stations combining ground readings, ERA5 meteorology, and Sentinel-5P columns. |
| `features_engineered.parquet` | Complete engineered feature store containing 138 features including multi-scale lags (1h–72h), rolling statistics (mean/std/min/max), solar angles, and atmospheric stability indicators. |
| `station_static_features.parquet` | Static geospatial characteristics per station (elevation, road density, building footprint density, land-cover percentages). |
| `anand_vihar_pilot.parquet` | Standalone high-resolution pilot dataset for Anand Vihar used for rapid baseline testing. |
| `metadata/data_dictionary.csv` | Full data dictionary defining all 138 features, descriptions, data types, and physical units. |
| `metadata/station_locations.csv` | Reference table of station codes, station names, latitude, and longitude. |
| `metadata/station_metadata.csv` | Metadata table detailing land-use class, altitude, and surrounding microclimate parameters. |
| `quality_reports/` | Mirror of the 12 QA benchmark CSV reports validating dataset completeness and zero leakage. |

---

### `MODEL_ARCHITECTURE_RESEARCH/`
*Theoretical research, photochemical formulation, atmospheric boundary layer physics, and comparative studies.*

| Path / File | Purpose & Contents |
|---|---|
| `README.md` | Overview of research literature, mathematical formulations, and comparative studies conducted for AIRO2. |
| `MODEL_ARCHITECTURE_RESEARCH.md` | Comprehensive research survey evaluating tree ensembles (LightGBM, XGBoost, CatBoost), recurrent neural architectures (LSTM, BiLSTM, GRU), and Temporal Transformers. |
| `ML_RESEARCHER_THEORETICAL_ANALYSIS.md` | Theoretical formulation of the non-linear photochemical Leighton relationship between $NO$, $NO_2$, and $O_3$, and boundary layer ventilation dynamics. |
| `DIURNAL_CALIBRATION_ANALYSIS.md` | Empirical analysis of the diurnal photolytic cycle, nighttime ozone titrations ($O_3 + NO ightarrow NO_2 + O_2$), and afternoon photochemical peaks. |
| `COMPARATIVE_ANALYSIS_LIVE_DATA_INGESTION_METHODS.md` | Technical trade-off analysis between polling REST APIs, Webhooks, and Event Streams for live near-real-time ingestion. |
| `MODEL_BUILD_RECOMMENDATIONS_ANALYSIS.md` | ML recommendations covering loss function selection (Huber vs MSE vs Quantile Pinball), multi-step forecasting strategies, and sample weighting. |
| `PROPOSAL_HYBRID_SATELLITE_VS_CPCB.md` | Mathematical framework for weighting sparse, coarse satellite observations against continuous, localized ground sensor feeds. |
| `SUDHITH_EXTRA_FEATURES_ANALYSIS.md` | Deep dive into specialized atmospheric physics features: boundary layer ventilation index, wind shear vectors, and photochemical age metrics. |

---

### `MODEL CODE/`
*Core Machine Learning, Deep Learning, Meta-Stacking Ensemble, and production inference codebase.*

| Path / File | Purpose & Contents |
|---|---|
| `README.md` | Architecture guide, model training steps, and inference instructions for the Phase 3 ML suite. |
| `01_MACHINE_LEARNING_MODELS/feature_engineering.py` | Domain feature generation module constructing 138 lag, rolling, cyclical time, and meteorological interaction features. |
| `01_MACHINE_LEARNING_MODELS/train_lightgbm.py` | LightGBM multi-horizon training pipeline with hyperparameter tuning, early stopping, and separate models per target ($NO_2$, $O_3$). |
| `02_DEEP_LEARNING_MODELS/train_bilstm_attention.py` | PyTorch Bidirectional LSTM model with temporal self-attention mechanism for sequential pattern learning across multi-horizon forecasts. |
| `03_ENSEMBLE_AND_META_STACKING/nnls_simplex_stacking.py` | Non-Negative Least Squares (NNLS) meta-learner performing convex combination ($\sum w_i = 1, w_i \ge 0$) to blend LightGBM and BiLSTM predictions safely. |
| `04_DIURNAL_CALIBRATION_MODEL/diurnal_calibration.py` | Post-processing diurnal calibrator adjusting raw model predictions using fitted hour-of-day solar radiation curves. |
| `04_DIURNAL_CALIBRATION_MODEL/fit_diurnal_weights.py` | Script fitting station-specific hourly diurnal weight matrices on historical training data. |
| `05_TRAINING_PIPELINE_AND_CV/run_master_pipeline.py` | Master pipeline orchestrator executing feature engineering, cross-validation, model training, stacking, and bundle serialization. |
| `05_TRAINING_PIPELINE_AND_CV/temporal_cross_validation.py` | Strict 5-fold expanding-window temporal cross-validation framework preventing look-ahead bias. |
| `05_TRAINING_PIPELINE_AND_CV/evaluation_metrics.py` | Metric computation module calculating $R^2$, RMSE, MAE, sMAPE, Peak-F1, and Directional Accuracy. |
| `05_TRAINING_PIPELINE_AND_CV/eda_analysis.py` | Automated exploratory data analysis script generating statistical correlation matrices and seasonal pollutant profiles. |
| `05_TRAINING_PIPELINE_AND_CV/shap_attribution.py` | Explainability module computing TreeSHAP feature importance rankings and generating summary plots for model transparency. |
| `06_PRODUCTION_INFERENCE_SERVICES/model_service.py` | Production model inference runtime loading serialized model bundles and executing sub-10ms predictions. |
| `06_PRODUCTION_INFERENCE_SERVICES/feature_builder.py` | Real-time feature generator transforming live raw sensor inputs and weather forecasts into model-ready tensors. |
| `06_PRODUCTION_INFERENCE_SERVICES/aqi_calculator.py` | Indian National Air Quality Index (NAQI) calculator using official CPCB linear interpolation piecewise formulas. |
| `07_PRODUCTION_MODEL_BUNDLES/NO2/` | Production artifact directory containing `model.pkl` (serialized ensemble weights), `feature_schema.json` (expected feature order), and `metadata.json` (model metrics and training hashes) for $NO_2$. |
| `07_PRODUCTION_MODEL_BUNDLES/O3/` | Production artifact directory containing `model.pkl`, `feature_schema.json`, and `metadata.json` for $O_3$. |
| `08_MODEL_DOCUMENTATION/MODEL_ARCHITECTURE.md` | Comprehensive architectural blueprint of the stacked hybrid ensemble system. |
| `08_MODEL_DOCUMENTATION/MODEL_CONTRACT.md` | Strict input/output interface contract defining parameter constraints, units ($\mu g/m^3$), and response formats. |
| `08_MODEL_DOCUMENTATION/PHASE_3_COMPLETE_MASTER_HANDOUT.md` | Executive summary handout detailing Phase 3 model performance, benchmarks, and key findings. |
| `08_MODEL_DOCUMENTATION/PHASE_3_MODEL_DEVELOPER_SPECIFICATION.md` | Developer specification with code examples and integration instructions for downstream services. |
| `08_MODEL_DOCUMENTATION/PHASE_3_PIPELINE_GUIDE.md` | Step-by-step operations manual for retraining, evaluating, and exporting models. |
| `08_MODEL_DOCUMENTATION/PHASE_3_SUDHITH_IMPLEMENTATION_PLAN.md` | Technical design and execution plan for the modeling phase. |
| `08_MODEL_DOCUMENTATION/PHASE_3_TO_PHASE_4_HANDOFF_REQUIREMENTS.md` | Exhaustive engineering handoff document defining the 6 discrete horizons (+1h, +3h, +6h, +12h, +24h, +48h), latency targets, and fallback strategies. |

---

### `MODEL RESULTS/`
*Empirical evaluation benchmarks, SHAP explainability charts, and audit reports.*

| Path / File | Purpose & Contents |
|---|---|
| `README.md` | Guide to the benchmark metrics, figures, and accuracy reports. |
| `FINAL_DOC.md` | Master document synthesizing all model evaluation metrics, cross-validation scores, and research insights. |
| `01_BENCHMARK_AND_METRICS_CSVS/phase3_evaluation_summary.csv` | Master performance summary across all models, pollutants, and forecast horizons. |
| `01_BENCHMARK_AND_METRICS_CSVS/lightgbm_evaluation_summary.csv` | Detailed LightGBM benchmark metrics ($R^2$, RMSE, MAE) per horizon. |
| `01_BENCHMARK_AND_METRICS_CSVS/bilstm_evaluation_summary.csv` | Detailed BiLSTM + Attention benchmark metrics per horizon. |
| `01_BENCHMARK_AND_METRICS_CSVS/ensemble_evaluation_summary.csv` | Stacked ensemble benchmark results demonstrating performance gain over individual models. |
| `01_BENCHMARK_AND_METRICS_CSVS/station_evaluation_summary.csv` | Granular performance metrics broken down across all 10 individual CPCB stations. |
| `01_BENCHMARK_AND_METRICS_CSVS/cv_fold_boundaries.csv` | Exact timestamp boundaries for each of the 5 expanding-window cross-validation folds. |
| `02_VISUALIZATIONS_AND_SHAP/forecast_vs_actual_NO2_ITO.png` | Time-series chart comparing forecasted vs ground-truth $NO_2$ concentrations at ITO station. |
| `02_VISUALIZATIONS_AND_SHAP/forecast_vs_actual_O3_ITO.png` | Time-series chart comparing forecasted vs ground-truth $O_3$ concentrations at ITO station. |
| `02_VISUALIZATIONS_AND_SHAP/horizon_degradation_NO2.png` | Accuracy degradation curve showing $R^2$ across +1h to +48h horizons for $NO_2$. |
| `02_VISUALIZATIONS_AND_SHAP/horizon_degradation_O3.png` | Accuracy degradation curve showing $R^2$ across +1h to +48h horizons for $O_3$. |
| `02_VISUALIZATIONS_AND_SHAP/shap_summary_NO2.png` | Global SHAP beeswarm plot illustrating top feature drivers for $NO_2$ predictions. |
| `02_VISUALIZATIONS_AND_SHAP/shap_summary_O3.png` | Global SHAP beeswarm plot illustrating top feature drivers (solar radiation, temperature) for $O_3$. |
| `02_VISUALIZATIONS_AND_SHAP/shap_top10_NO2.csv` | Ranked top 10 most influential features for $NO_2$ with mean absolute SHAP values. |
| `02_VISUALIZATIONS_AND_SHAP/shap_top10_O3.csv` | Ranked top 10 most influential features for $O_3$ with mean absolute SHAP values. |
| `03_EVALUATION_AND_ACCURACY_REPORTS/FINAL_EXECUTION_REPORT.md` | Executive sign-off report validating model compliance with SIH problem statements. |
| `03_EVALUATION_AND_ACCURACY_REPORTS/PHASE_3_EVALUATION_REPORT.md` | In-depth evaluation report reviewing cross-validation metrics, error distributions, and edge cases. |
| `03_EVALUATION_AND_ACCURACY_REPORTS/PHASE_3_INTEGRITY_AND_ACCURACY_REPORT.md` | Verification report certifying physical plausibility and absence of impossible predictions ($O_3 < 0$). |
| `03_EVALUATION_AND_ACCURACY_REPORTS/ULTRA_DETAILED_EVALUATION_METRICS_AND_RESEARCH_AUDIT.md` | Comprehensive research audit document analyzing atmospheric science alignment and feature sensitivity. |

---

### `MODEL OUTPUT VALIDATION/`
*Integration testing harnesses, golden compatibility tests, and readiness certificates.*

| Path / File | Purpose & Contents |
|---|---|
| `README.md` | Instructions for executing golden test suites and verifying backend readiness before deployment. |
| `verify_model_readiness.py` | Automated CLI test script validating bundle integrity, inference speed, and prediction bounds. |
| `01_GOLDEN_COMPATIBILITY_TESTS/input.json` | Standardized reference test payload representing live station observations and meteorological forecasts. |
| `01_GOLDEN_COMPATIBILITY_TESTS/expected_output.json` | Golden expected response containing exact 12 predictions (2 pollutants $	imes$ 6 horizons) and AQI sub-indices. |
| `01_GOLDEN_COMPATIBILITY_TESTS/test_phase3_phase4_compatibility.py` | PyTest test suite executing golden payload tests and asserting numeric tolerance ($\le 10^{-4}$). |
| `01_GOLDEN_COMPATIBILITY_TESTS/README.md` | Guide to running golden compatibility tests. |
| `02_PHYSICAL_PLAUSIBILITY_AND_INVARIANTS/MODEL_OUTPUT_INVARIANTS_CHECKLIST.md` | Audit checklist verifying non-negativity, diurnal peak alignment, and boundary layer inverse correlations. |
| `02_PHYSICAL_PLAUSIBILITY_AND_INVARIANTS/PHASE_3_INTEGRITY_AND_ACCURACY_REPORT.md` | Scientific integrity assessment of model outputs across extreme weather events. |
| `02_PHYSICAL_PLAUSIBILITY_AND_INVARIANTS/test_live_observation_pipeline.py` | Test suite validating live pipeline behavior with missing data feeds and noisy sensor inputs. |
| `03_READINESS_AND_FIT_FOR_USE_CERTIFICATES/MODEL_FIT_FOR_USE_CERTIFICATE.md` | Formal engineering certificate declaring the ML model production-ready for deployment. |
| `03_READINESS_AND_FIT_FOR_USE_CERTIFICATES/FINAL_MASTER_AUDIT_REPORT.md` | Consolidated audit report certifying end-to-end model pipeline stability and compliance. |
| `03_READINESS_AND_FIT_FOR_USE_CERTIFICATES/ULTRA_DETAILED_EVALUATION_METRICS_AND_RESEARCH_AUDIT.md` | Deep research audit validating physical plausibility of predictions under varying atmospheric regimes. |

---

### `PRODUCTION BACKEND SERVICE/` (and `backend/`)
*Production FastAPI server, real-time data ingestion pipelines, background schedulers, and REST APIs.*

| Path / File | Purpose & Contents |
|---|---|
| `README.md` | Comprehensive backend setup guide, API endpoint documentation, and deployment instructions. |
| `requirements.txt` | Python package dependencies (`fastapi`, `uvicorn`, `pydantic`, `scikit-learn`, `lightgbm`, `requests`, `pytest`). |
| `app/config.py` | Configuration settings (server host/port, model bundle filepaths, CORS origins, API keys, poll intervals). |
| `app/main.py` | FastAPI application entry point, lifecycle management, CORS middleware setup, router mounting, and static assets mounting. |
| `app/scheduler.py` | Background scheduler periodically triggering live data ingestion and running hourly 48-hour forecast updates. |
| `app/api/deps.py` | FastAPI dependency injection providers for database sessions and authentication helpers. |
| `app/data/forecast_store.db` | SQLite database storing persistent logs of all generated forecasts, timestamps, and AQI evaluations. |
| `app/data/live_observations.db` | SQLite database storing real-time ingested CPCB, CAMS, and weather observations. |
| `app/middleware/error_handler.py` | Centralized exception handling middleware formatting errors into uniform JSON error responses. |
| `app/middleware/security.py` | Security headers middleware applying Content Security Policy (CSP), X-Frame-Options, and rate limiting. |
| `app/providers/base.py` | Abstract base class (`BaseProvider`) defining standard interfaces for real-time and historical data providers. |
| `app/providers/historical.py` | Historical data replay provider used for offline demonstration mode and testing. |
| `app/providers/live/live_provider.py` | Master live provider aggregating ground, satellite, and meteorological data streams in real time. |
| `app/providers/live/cpcb_manual.py` | Ingestion provider handling live CPCB station data scraping and manual measurement overrides. |
| `app/providers/live/weather.py` | Real-time weather provider fetching temperature, wind speed/direction, humidity, and solar radiation from Open-Meteo API. |
| `app/providers/live/cams.py` | Atmospheric composition provider integrating Copernicus Atmosphere Monitoring Service (CAMS) forecasts. |
| `app/providers/live/sentinel.py` | Satellite provider pulling latest Sentinel-5P TROPOMI overpass columns. |
| `app/providers/live/store.py` | Real-time observation data access object (DAO) caching recent readings with sliding window lookbacks. |
| `app/routers/stations.py` | Core REST router serving station metadata, latest sensor readings, and **48-hour discrete horizon forecasts** (`/api/v1/stations/{id}/forecast`). |
| `app/routers/explain.py` | Explainability router returning SHAP feature attribution rankings and drivers for any specific forecast. |
| `app/routers/simulate.py` | Policy simulation / "What-If" sandbox API allowing users to model traffic reduction and industrial emission curtailments. |
| `app/routers/spatial.py` | Spatial interpolation router computing 2D continuous air quality heatmaps and hotspot clusters across Delhi NCR. |
| `app/routers/alerts.py` | Alert management router supporting webhook registrations, threshold configurations, and breach notifications. |
| `app/routers/model.py` | Model status router serving model bundle metadata, training timestamps, and validation metrics. |
| `app/routers/report.py` | Automated report generation router exporting consolidated air quality summary reports in PDF and CSV formats. |
| `app/schemas/forecast.py` | Pydantic data schemas validating forecast requests, 12 discrete predictions (+1h, +3h, +6h, +12h, +24h, +48h), and AQI responses. |
| `app/schemas/station.py` | Pydantic data schemas validating station information, geo-coordinates, and operational status. |
| `app/services/model_service.py` | High-performance inference service loading frozen LightGBM + NNLS models and generating predictions in sub-10ms. |
| `app/services/feature_service.py` | Live feature extraction service transforming raw observation histories into 138-dimensional model feature vectors. |
| `app/services/forecast_database.py` | Database service managing persistent storage and retrieval of generated forecasts in SQLite. |
| `app/utils/aqi.py` | CPCB National Air Quality Index (NAQI) calculation utility computing sub-indices and identifying the dominant pollutant. |
| `app/utils/feature_builder.py` | Feature construction utility assembling lag vectors, rolling statistics, and cyclical solar features. |
| `app/static/index.html` | Complete interactive single-page Web UI / Dashboard featuring Leaflet map, forecast charts, SHAP cards, and simulation tools. |
| `tests/test_phase3_phase4_compatibility.py` | PyTest integration test suite verifying 100% adherence to Phase 3 ML contract requirements. |
| `tests/test_live_observation_pipeline.py` | Test suite validating live observation ingestion, caching, and fallback logic. |
| `tests/test_location_and_webhook_alerts.py` | Test suite verifying alert trigger rules, coordinate matching, and webhook delivery. |

---

### `FRONTEND/`
*Phase 7 React + TypeScript + Vite interactive Command Center, GIS map visualizations, and AQI analytics.*

| Path / File | Purpose & Contents |
|---|---|
| `package.json` | NPM package dependencies (React 18, TypeScript, Vite, TailwindCSS, Lucide-React, Recharts, D3-Geo, Leaflet). |
| `package-lock.json` | Exact dependency lockfile ensuring reproducible frontend builds. |
| `vite.config.ts` | Vite build tool configuration, dev-server settings, and path aliases. |
| `tsconfig.json` & `tsconfig.app.json` | TypeScript compiler options, strict type checking, and JSX configuration. |
| `tsconfig.node.json` | TypeScript configuration for Node-based Vite plugins. |
| `index.html` | Root HTML template mounting the React virtual DOM. |
| `.gitignore` | Ignores `node_modules/`, `dist/`, `.env`, and build artifacts. |
| `.oxlintrc.json` | Linter rules configuration. |
| `public/favicon.svg` | Application SVG favicon. |
| `public/icons.svg` | Vector sprite icon library. |
| `src/main.tsx` | Main application bootstrap entry point mounting React 18 into `index.html`. |
| `src/App.tsx` | Main application shell orchestrating navigation, active station state, and layout views. |
| `src/index.css` | Global Tailwind CSS styles, custom scrollbars, futuristic HUD animations, and glow filters. |
| `src/components/common/LiveClock.tsx` | High-precision real-time IST clock component with milliseconds and status indicators. |
| `src/components/common/ScrambleText.tsx` | Cyberpunk-style animated text scrambler effect for titles and data updates. |
| `src/components/common/SectionHeader.tsx` | Standardized section header with badge indicators and title typography. |
| `src/components/common/SegmentBar.tsx` | Segmented visual bar visualizing concentration levels relative to national standards. |
| `src/components/common/StatusPill.tsx` | Colored status badge component indicating station operational health (Active, Warning, Offline). |
| `src/components/common/TrendChart.tsx` | Recharts-based multi-line trend chart rendering historical and forecasted pollutant curves. |
| `src/components/common/TypewriterText.tsx` | Dynamic typewriter animation effect for announcements and model insights. |
| `src/components/hero/Hero.tsx` | Landing header banner showcasing project title, real-time Delhi average AQI, and live radar animation. |
| `src/components/hero/Globe.tsx` | Interactive 3D D3-Geo rotating Earth globe illustrating regional atmospheric circulation. |
| `src/components/hero/PixelTransition.tsx` | Futuristic pixel-grid transition animation component for smooth view switching. |
| `src/components/layout/Topbar.tsx` | Application top navigation bar with project branding, system status, and links. |
| `src/components/layout/Ticker.tsx` | Continuous horizontal ticker tape streaming live station AQI scores across Delhi. |
| `src/components/layout/Footer.tsx` | Footer component with SIH attribution, data source acknowledgments, and GitHub link. |
| `src/components/map/RealDelhiMap.tsx` | Interactive Leaflet GIS map rendering Delhi NCR boundary, live station markers, AQI color coding, and popup cards. |
| `src/components/map/DelhiMap.tsx` | SVG vector fallback map of Delhi with clickable station pins. |
| `src/components/map/ScanOverlay.tsx` | Radar scanline animation overlay adding a high-tech monitoring aesthetic to the map. |
| `src/components/map/StationInfoPanel.tsx` | Slide-over drawer displaying selected station telemetry, land-use details, and quick stats. |
| `src/components/station/StationDashboard.tsx` | Master station analytics dashboard presenting detailed charts, pollutant breakdown, and forecasts. |
| `src/components/station/ForecastPanel.tsx` | Discrete horizon card panel displaying +1h, +3h, +6h, +12h, +24h, and +48h $O_3$ and $NO_2$ predictions. |
| `src/components/station/ReadingCard.tsx` | High-impact telemetry card showing current pollutant concentration, delta vs baseline, and AQI category. |
| `src/components/station/QuickScanTable.tsx` | Compact tabular comparison matrix of all 10 monitoring stations with sorting capabilities. |
| `src/components/station/HistoryPanel.tsx` | Historical trend inspection panel allowing multi-day pollutant comparison. |
| `src/data/delhi_boundary.json` | High-precision GeoJSON polygon boundary of National Capital Territory (NCT) of Delhi. |
| `src/data/countries-110m.json` | Low-resolution world landmass GeoJSON topology used for the 3D rotating globe. |
| `src/lib/api.ts` | Frontend REST API client for interacting with the FastAPI backend (`/api/v1/*`). |
| `src/lib/aqi.ts` | Frontend implementation of CPCB AQI breakpoints, color scale mappings, and health advisory text. |
| `src/lib/stations.ts` | Static station registry with coordinates, official names, and sensor capabilities. |
| `src/lib/mockData.ts` | High-fidelity fallback mock dataset enabling rich offline demo functionality when backend is unreachable. |
| `src/lib/alerts.ts` | Alert evaluation rules and threshold checking utility for client-side notifications. |
| `src/lib/delhiBoundary.ts` | Helper utilities for spatial calculations and GeoJSON boundary rendering. |
| `src/lib/time.ts` | Date/time formatting utilities for UTC/IST conversions and horizon timestamp generation. |
| `src/lib/trend.ts` | Mathematical trend calculators computing rate-of-change and slope indicators. |
| `src/lib/useInView.ts` | Custom React hook observing element visibility for performant viewport animations. |
| `src/lib/PageTransition.tsx` | Page transition wrapper managing animated route transitions. |

---

## 3. Summary of Key Architectural Modules

| Subsystem | Primary Directory | Key Technologies | Core Responsibilities |
|---|---|---|---|
| **Data Ingestion & Fusion** | `DATASET FUSION/`, `DATASET VALIDATION/` | Python, Pandas, PyArrow, NetCDF4 | Harmonizes CPCB ground data, ERA5 weather, and Sentinel-5P satellite rasters into Parquet feature tables with zero temporal leakage. |
| **Machine Learning Engine** | `MODEL CODE/`, `MODEL RESULTS/` | LightGBM, PyTorch (BiLSTM), Scipy (NNLS), SHAP | Trains multi-horizon models, performs expanding-window cross-validation, stacks models via convex optimization, and computes feature attributions. |
| **Inference & Backend** | `PRODUCTION BACKEND SERVICE/` | FastAPI, Uvicorn, SQLite, Pydantic | Serves sub-10ms discrete horizon forecasts (+1h to +48h), live data ingestion, background job scheduling, SHAP explanations, and simulation sandbox. |
| **Interactive Frontend** | `FRONTEND/` | React 18, TypeScript, Vite, TailwindCSS, Leaflet | Provides an interactive command center with live GIS Delhi mapping, real-time station analytics, forecast horizon cards, and radar visualizations. |
