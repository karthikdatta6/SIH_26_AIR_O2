# SIH 25178 — Phase 3 Model Developer Specification & Coding Blueprint
## Complete Engineering Specification, Folder Architecture & Phase 4 API Handoff Contract

> **Project Title:** Short-Term Forecasting of Ground-Level Ozone (O₃) and Nitrogen Dioxide (NO₂) Using Satellite Observations and Meteorological Reanalysis  
> **Problem Statement ID:** SIH 25178  
> **Target Audience:** External Model Developers, Algorithm Engineers & Co-Programmers  
> **Document Purpose:** Complete, self-contained engineering blueprint for writing the Phase 3 training and forecasting codebase. Defines folder contracts, strict data rules, defensive exception handling, evaluation templates, and the Phase 4 FastAPI handoff schema.  
> **Target Benchmark:** $R^2 \ge 0.95$ on held-out test data for short-term horizons ($t+1\text{h}$ to $t+6\text{h}$) and strong skill at headline horizons ($24\text{h}$ and $48\text{h}$) without overfitting, memorization, or data leakage.  

---

## 📑 TABLE OF CONTENTS
1. [Developer Mission & Core Directives](#1-developer-mission--core-directives)
2. [Input Dataset Interface & Exact Row Counts](#2-input-dataset-interface--exact-row-counts)
3. [Exact Folder, File & Output Architecture](#3-exact-folder-file--output-architecture)
4. [Strict Coding Rules & Data Constraints](#4-strict-coding-rules--data-constraints)
5. [Feature Engineering Contract (38 Features)](#5-feature-engineering-contract-38-features)
6. [Forecasting Horizons & Direct Multi-Step Strategy](#6-forecasting-horizons--direct-multi-step-strategy)
7. [Candidate Model Architectures & Simplex Stacking](#7-candidate-model-architectures--simplex-stacking)
8. [Automated Error & Exception Handling Framework](#8-automated-error--exception-handling-framework)
9. [Standard Results Reporting & Persistence Baseline Benchmark](#9-standard-results-reporting--persistence-baseline-benchmark)
10. [Required Documentation & Report Deliverables](#10-required-documentation--report-deliverables)
11. [Phase 4 Backend / Forecast API Handoff Contract](#11-phase-4-backend--forecast-api-handoff-contract)
12. [Contingency Playbook: What If Accuracy Falls Below Target?](#12-contingency-playbook-what-if-accuracy-falls-below-target)
13. [CLI Execution Commands & How to Run](#13-cli-execution-commands--how-to-run)

---

## 1. DEVELOPER MISSION & CORE DIRECTIVES

Your goal as the model developer is to write the Phase 3 modeling scripts to train, validate, and export high-performance forecasting models for ground-level $\text{O}_3$ and $\text{NO}_2$ across 10 Delhi CAAQMS stations.

### 🛡️ Five Non-Negotiable Rules:
1. **Zero Temporal Leakage:**
   - At forecast issue time $T$, the model may only see predictors and ground lags from $t_{\text{obs}} \le T$.
   - Never use future target values or centered rolling windows in the feature matrix $\mathbf{X}$.
2. **Pure Ground Truth Targets:**
   - Ground targets (`OZONE_ground`, `NO2_ground`) are **pure CPCB measurements**. Missing values are real IEEE 754 `NaN`s. Never train on or evaluate artificially imputed targets.
3. **Generalization Over Memorization:**
   - The model must generalize across all 4 seasons and all 10 stations without overfitting or data memorization.
4. **Mandatory Persistence Baseline Benchmark ($\Delta R^2$):**
   - Because air pollution is autocorrelated ($\rho \approx 0.90$ at 1 hour), you must always benchmark against the **Persistence Model** ($\hat{y}_{T+h} = y_T$). Evaluators judge skill by $\Delta R^2 = R^2_{\text{model}} - R^2_{\text{persistence}}$.
5. **Phase 4 Handoff Readiness:**
   - Exported model artifacts must include `model.pkl`, `feature_schema.json`, and `metadata.json` for immediate consumption by the Phase 4 FastAPI service.

---

## 2. INPUT DATASET INTERFACE & EXACT ROW COUNTS

### 2.1 File Locations & Loading
- **Master Fused Dataset:** `data/fused/station_hourly_fused.parquet` (263,040 rows $\times$ 45 columns, 14.73 MB)
- **Pilot Prototyping Dataset:** `data/fused/pilot/anand_vihar_pilot.parquet` (744 rows — Jan 2023)

Load efficiently with `pandas` / `pyarrow`:
```python
import pandas as pd
df = pd.read_parquet("data/fused/station_hourly_fused.parquet")
df["timestamp_utc"] = pd.to_datetime(df["timestamp_utc"])
```

### 2.2 Exact Row Counts & Temporal Partitions
The dataset covers **3 full years (2023-01-01 00:00 to 2025-12-31 23:00 UTC)** across **10 stations** ($26,304\text{ hours/station} \times 10 = 263,040\text{ rows}$):

| Split Name | Date Range (UTC) | Duration | Rows per Station | Total Rows (10 Stations) | Primary Purpose |
|---|---|---|---|---|---|
| **`TRAIN`** | `2023-01-01 00:00` to `2024-12-31 23:00` | 731 days *(2024 Leap Year)* | 17,544 | **175,440** (66.7%) | Model training across 2 full seasonal cycles |
| **`VAL`** | `2025-01-01 00:00` to `2025-06-30 23:00` | 181 days (H1 2025) | 4,344 | **43,440** (16.5%) | Hyperparameter tuning, early stopping & CV |
| **`TEST`** | `2025-07-01 00:00` to `2025-12-31 23:00` | 184 days (H2 2025) | 4,416 | **44,160** (16.8%) | Final untouched evaluation benchmark |
| **TOTAL** | `2023-01-01` to `2025-12-31` | 1,096 days (3 years) | 26,304 | **263,040** (100%) | Complete dense hourly matrix |

```python
train_df = df[df["timestamp_utc"] < "2025-01-01"].copy()
val_df   = df[(df["timestamp_utc"] >= "2025-01-01") & (df["timestamp_utc"] < "2025-07-01")].copy()
test_df  = df[df["timestamp_utc"] >= "2025-07-01"].copy()

assert len(train_df) == 175440, f"Expected 175,440 train rows, got {len(train_df)}"
assert len(val_df)   == 43440,  f"Expected 43,440 val rows, got {len(val_df)}"
assert len(test_df)  == 44160,  f"Expected 44,160 test rows, got {len(test_df)}"
```

---

## 3. EXACT FOLDER, FILE & OUTPUT ARCHITECTURE

Your code must strictly conform to the project structure below:

```
PROJECT-AIRO2/
├── scripts/
│   └── phase3/
│       ├── 00_eda_analysis.py            # Generates exploratory data analysis reports
│       ├── 01_feature_engineering.py     # Lags, rolling stats, cyclical time, physical proxies
│       ├── 02_cross_validation.py        # Blocked walk-forward CV with dynamic purge scaling
│       ├── 03_train_lightgbm.py          # Multi-horizon LightGBM regressors (Stage 1)
│       ├── 04_train_deep_learning.py     # PyTorch TFT and BiLSTM+Attention (Stage 1)
│       ├── 05_ensemble_stacking.py       # Simplex-constrained NNLS meta-learner (Stage 2)
│       ├── 06_evaluate_and_benchmark.py  # Test set metrics vs Persistence baseline
│       ├── 07_shap_and_visualizations.py # SHAP attribution & forecast comparison curves
│       └── run_phase3_pipeline.py        # Master orchestrator script
│
├── models/
│   ├── NO2/                              # Final NO2 model artifacts for Phase 4 API
│   │   ├── model.pkl                     # Serialized LightGBM/Ensemble model bundle
│   │   ├── feature_schema.json           # Input schema, dtypes, units, ordering
│   │   └── metadata.json                 # Model version, train dates, horizons, metrics
│   │
│   ├── O3/                               # Final O3 model artifacts for Phase 4 API
│   │   ├── model.pkl                     # Serialized LightGBM/Ensemble model bundle
│   │   ├── feature_schema.json           # Input schema, dtypes, units, ordering
│   │   └── metadata.json                 # Model version, train dates, horizons, metrics
│   │
│   ├── lightgbm/                         # Intermediate per-horizon checkpoints (O3_h1.pkl, etc.)
│   ├── deep_learning/                    # Saved PyTorch .pt / .ckpt weights
│   └── ensemble/                         # Meta-learner weights and stacking config
│
├── reports/
│   ├── phase3_eda/                       # EDA CSV reports and distribution charts
│   │   ├── target_distribution.csv
│   │   ├── missingness.csv
│   │   ├── station_statistics.csv
│   │   ├── hourly_statistics.csv
│   │   └── monthly_statistics.csv
│   │
│   └── phase3/                           # Quality and audit reports
│       ├── leakage_report.md             # 6-point automated leakage audit
│       └── error_analysis.md             # Diagnostic breakdown of high-pollution & episodic events
│
├── experiments/
│   └── experiment_log.csv                # Experiment tracking log (run_id, model, params, metrics)
│
├── results/
│   ├── metrics/                          # CSV evaluation summaries & CV fold stability
│   │   ├── phase3_evaluation_summary.csv
│   │   ├── station_evaluation_summary.csv
│   │   └── cv_stability_report.csv
│   ├── forecasts/                        # Parquet files containing predicted vs actual values
│   └── figures/                          # PNG plots: SHAP summary, time-series forecast curves
│
└── docs/
    ├── MODEL_CONTRACT.md                 # Handoff schema contract for Phase 4 FastAPI service
    ├── phase3/
    │   ├── FEATURE_SELECTION.md          # Scientific rationale for every feature
    │   └── FORECASTING_SCENARIO.md       # Exact definition of issue time T and available data
    ├── PHASE_3_MODEL_DEVELOPER_SPECIFICATION.md
    ├── PHASE_3_SUDHITH_IMPLEMENTATION_PLAN.md
    └── PHASE_3_ML_RESEARCHER_HANDOUT.md
```

---

## 4. STRICT CODING RULES & DATA CONSTRAINTS

When writing the Python scripts, follow these strict rules:

### ⚠️ Rule 1: Always Apply `log1p` Transformation to Targets
Because ground $\text{O}_3$ and $\text{NO}_2$ concentrations have heavy right-skew, training directly with MSE loss causes the model to underpredict peak pollution events.
```python
# During training:
y_train_trans = np.log1p(np.clip(y_train, 0, None))

# During inference / evaluation:
y_pred_orig = np.expm1(y_pred_trans)
y_pred_orig = np.clip(y_pred_orig, 0, None)  # Physical constraint: concentration >= 0
```

### ⚠️ Rule 2: Compute Lags & Rolling Statistics STRICTLY Per-Station
Never compute lags on the global DataFrame without grouping by `station_id` first!
```python
# CORRECT:
df = df.sort_values(["station_id", "timestamp_utc"]).reset_index(drop=True)
df["OZONE_lag_1h"] = df.groupby("station_id")["OZONE_ground"].shift(1)

# WRONG (Causes station boundary contamination):
df["OZONE_lag_1h"] = df["OZONE_ground"].shift(1)  # DO NOT DO THIS!
```

### ⚠️ Rule 3: Use Trailing Windows Only (Never Centered)
Rolling statistics must represent past information only. Always apply `shift(1)` before `.rolling()`.
```python
# CORRECT (Strictly trailing window):
df["OZONE_roll_mean_6h"] = (
    df.groupby("station_id")["OZONE_ground"]
    .shift(1)
    .rolling(window=6, min_periods=3)
    .mean()
)

# WRONG (Causes lookahead leakage):
df["OZONE_roll_mean_6h"] = df.groupby("station_id")["OZONE_ground"].rolling(6, center=True).mean()
```

### ⚠️ Rule 4: Dynamic Purge Gap Scaling
In blocked cross-validation, the purge gap between training and validation folds must scale with the maximum lag window used:
```python
purge_gap_hours = max(lag_windows_used)  # e.g., max([1, 3, 6, 12, 24]) = 24h
```

### ⚠️ Rule 5: Explicit Missingness Policy
- **For Tree Models (LightGBM / CatBoost):** Leave missing values as native `np.nan`. LightGBM natively routes NaNs to the optimal split branch. Do NOT zero-fill.
- **For Neural Networks (PyTorch):** Do NOT use `np.nan_to_num(x, 0.0)` for physical features (e.g. $0^\circ\text{C}$ temperature is a real number, not missing). Use a binary missingness mask indicator + feature mean imputation.

### ⚠️ Rule 6: Respect Chemical Precursor Units
- `NOx_ground` is in **$\text{ppb}$**; all other ground pollutants are in **$\mu\text{g/m}^3$**; `CO_ground` is in **$\text{mg/m}^3$**.
- Never add or divide precursor columns directly without unit harmonization.
- Satellite column densities (`sat_NO2`, `sat_CO`, `sat_HCHO`) are in $\text{mol/m}^2$. The ratio `sat_HCHO / sat_NO2` is unit-consistent.

### ⚠️ Rule 7: Simplex-Constrained Ensemble Stacking (NNLS)
The meta-learner must combine base model predictions with non-negative weights that sum to 1:
```python
from scipy.optimize import nnls

# Solve min ||Xw - y||^2 subject to w >= 0
weights, _ = nnls(oof_predictions_matrix, y_true_log)
weights = weights / (np.sum(weights) + 1e-12)  # Normalize to simplex (sum to 1)
```

---

## 5. FEATURE ENGINEERING CONTRACT (38 INPUT FEATURES)

The feature engineering script (`01_feature_engineering.py`) must generate these **38 curated features**:

```
1. Ground Chemistry (7):
   - NO_ground, NOx_ground, CO_ground, PM2.5_ground, PM10_ground, SO2_ground, NH3_ground

2. ERA5 Atmospheric Meteorology (11):
   - era5_temperature_c, era5_dewpoint_c, era5_u10, era5_v10, era5_wind_speed,
     wind_sin, wind_cos, era5_relative_humidity, era5_surface_pressure_hpa,
     era5_boundary_layer_height, era5_solar_radiation_w_m2, era5_total_precipitation_mm

3. Satellite Remote Sensing & Availability (6):
   - sat_NO2, sat_CO, sat_HCHO, satellite_age_hours,
     sat_NO2_available, sat_CO_available

4. Static OpenStreetMap Urban Context (4):
   - geo_dist_to_nearest_road_m, geo_road_length_1km_buffer_m,
     geo_road_length_3km_buffer_m, geo_dist_to_nearest_railway_m

5. Derived Physical & Cyclical Temporal Features (5):
   - ventilation_coeff = era5_boundary_layer_height * era5_wind_speed
   - photo_index       = era5_solar_radiation_w_m2 / 1024.0
   - hour_sin, hour_cos (diurnal photolysis cycle)
   - doy_sin, doy_cos   (seasonal meteorological cycle)

6. Historical Target Memory / Lags (14):
   - OZONE_lag_1h, OZONE_lag_3h, OZONE_lag_6h, OZONE_lag_12h, OZONE_lag_24h
   - OZONE_roll_mean_6h, OZONE_roll_mean_24h
   - NO2_lag_1h, NO2_lag_3h, NO2_lag_6h, NO2_lag_12h, NO2_lag_24h
   - NO2_roll_mean_6h, NO2_roll_mean_24h

7. Station Identity (1):
   - station_enc (Label encoded integer 0-9)
```

---

## 6. FORECASTING HORIZONS & DIRECT MULTI-STEP STRATEGY

### 6.1 Required Forecast Horizons
The pipeline must independently train and evaluate models for:
- **Immediate Tier:** $t+1\text{h}, t+3\text{h}, t+6\text{h}$
- **Short-Term Tier (Primary Benchmark):** $t+12\text{h}, t+24\text{h}$
- **Extended Tier (Headline Demonstration):** $t+48\text{h}$

### 6.2 Direct Multi-Horizon vs. Recursive Formulation
- **Direct Multi-Horizon (Primary):** Separate models $\text{Model}_h$ are trained for each horizon $h$. This avoids accumulating recursive prediction error over 48 hours.
- **Target Construction:** For target $y$ at horizon $h$:
  $$\text{target}_h(T) = y(T + h)$$
- **Purity Guarantee:** Targets are taken directly from the un-imputed ground series. Training instances where future target $y(T+h)$ is missing (`NaN`) are excluded from loss computation for horizon $h$.

---

## 7. CANDIDATE MODEL ARCHITECTURES & SIMPLEX STACKING

### 7.1 Stage 1: Base Model Suite
1. **LightGBM Multi-Horizon Regressors (`03_train_lightgbm.py`):**
   - Direct GBDT models per horizon.
   - `objective='regression_l1'`, `num_leaves=127`, `learning_rate=0.03`, `feature_fraction=0.7`, `bagging_fraction=0.8`, `reg_alpha=0.1`, `reg_lambda=1.0`.
2. **Deep Learning Suite (`04_train_deep_learning.py`):**
   - **BiLSTM + Multi-Head Attention:** 2-layer bidirectional LSTM with 8-head self-attention and 72h sequence lookback.
   - **Temporal Fusion Transformer (TFT):** Separates known future inputs (ERA5 weather forecasts) from observed ground chemistry.

### 7.2 Stage 2: Simplex Stacking Meta-Learner (`05_ensemble_stacking.py`)
- Out-of-fold validation predictions from base models are combined via **Non-Negative Least Squares (NNLS)**:
  $$\min_{\mathbf{w}} \|\mathbf{y}_{\text{true}} - \hat{\mathbf{Y}}_{\text{OOF}} \mathbf{w}\|_2^2 \quad \text{subject to } w_i \ge 0, \quad \sum w_i = 1$$
- Eliminates negative and unbounded coefficients, producing a stable, convex combination of forecasts.

---

## 8. AUTOMATED ERROR & EXCEPTION HANDLING FRAMEWORK

Wrap evaluation and data processing with defensive safeguards:

```python
import os, sys, traceback
import numpy as np

def safe_evaluate_metrics(y_true, y_pred):
    """Safely calculates RMSE, MAE, R2, sMAPE, Willmott d ignoring NaNs."""
    try:
        mask = (~np.isnan(y_true)) & (~np.isnan(y_pred))
        if np.sum(mask) == 0:
            return {"rmse": np.nan, "mae": np.nan, "r2": np.nan, "smape": np.nan, "willmott_d": np.nan}
        
        yt = y_true[mask]
        yp = y_pred[mask]
        
        # Calculate metrics
        rmse = np.sqrt(np.mean((yt - yp) ** 2))
        mae  = np.mean(np.abs(yt - yp))
        
        ss_res = np.sum((yt - yp) ** 2)
        ss_tot = np.sum((yt - np.mean(yt)) ** 2)
        r2 = 1.0 - (ss_res / (ss_tot + 1e-12))
        
        # sMAPE
        smape = 100.0 * np.mean(2.0 * np.abs(yp - yt) / (np.abs(yt) + np.abs(yp) + 1e-12))
        
        # Willmott's Index of Agreement (d)
        d_denom = np.sum((np.abs(yp - np.mean(yt)) + np.abs(yt - np.mean(yt))) ** 2)
        willmott_d = 1.0 - (ss_res / (d_denom + 1e-12))
        
        return {
            "rmse": round(float(rmse), 3),
            "mae": round(float(mae), 3),
            "r2": round(float(r2), 4),
            "smape": round(float(smape), 2),
            "willmott_d": round(float(willmott_d), 4)
        }
    except Exception as e:
        print(f"[ERROR in metric evaluation]: {e}")
        traceback.print_exc()
        return {"rmse": np.nan, "mae": np.nan, "r2": np.nan, "smape": np.nan, "willmott_d": np.nan}
```

### Defensive Safeguards:
1. **GPU OOM Guard:** Catch `torch.cuda.OutOfMemoryError`, clear cache via `torch.cuda.empty_cache()`, and automatically fallback to batch size halving or CPU.
2. **Directory Creation Guard:** Always call `os.makedirs(os.path.dirname(path), exist_ok=True)` before saving any model or metric CSV.
3. **Column Assertion:** Assert all 38 expected feature columns exist before fitting.

---

## 9. STANDARD RESULTS REPORTING & PERSISTENCE BENCHMARK

Your evaluation script (`06_evaluate_and_benchmark.py`) must generate a comprehensive results table at `results/metrics/phase3_evaluation_summary.csv`:

| Horizon | Target Pollutant | Model R² | Persistence R² | Skill Gain (ΔR²) | RMSE (µg/m³) | MAE (µg/m³) | sMAPE (%) | Willmott Index (d) | CV Mean R² (±Std) |
|---|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **$t+1\text{h}$** | $\text{O}_3$ | $\ge 0.950$ | $0.885$ | $+0.065$ | $< 8.5$ | $< 5.2$ | $< 18.0$ | $\ge 0.985$ | $0.948 \pm 0.012$ |
| **$t+1\text{h}$** | $\text{NO}_2$ | $\ge 0.950$ | $0.892$ | $+0.058$ | $< 9.2$ | $< 5.8$ | $< 16.5$ | $\ge 0.988$ | $0.951 \pm 0.010$ |
| **$t+3\text{h}$** | $\text{O}_3$ | $\ge 0.930$ | $0.780$ | $+0.150$ | $< 11.0$ | $< 7.1$ | $< 22.0$ | $\ge 0.970$ | $0.925 \pm 0.015$ |
| **$t+6\text{h}$** | $\text{O}_3$ | $\ge 0.900$ | $0.650$ | $+0.250$ | $< 14.5$ | $< 9.5$ | $< 26.0$ | $\ge 0.950$ | $0.895 \pm 0.018$ |
| **$t+24\text{h}$** | $\text{O}_3$ | $\ge 0.850$ | $0.420$ | $+0.430$ | $< 18.0$ | $< 12.0$ | $< 32.0$ | $\ge 0.910$ | $0.842 \pm 0.022$ |
| **$t+48\text{h}$** | $\text{O}_3$ | $\ge 0.800$ | $0.280$ | $+0.520$ | $< 22.5$ | $< 15.0$ | $< 38.0$ | $\ge 0.870$ | $0.795 \pm 0.025$ |

Also generate `results/metrics/station_evaluation_summary.csv` reporting performance across each of the 10 individual stations.

---

## 10. REQUIRED DOCUMENTATION & REPORT DELIVERABLES

The codebase must automatically produce the following documentation and report artifacts:

1. **`reports/phase3_eda/`:**
   - `target_distribution.csv` (mean, median, std, min, max, percentiles per pollutant)
   - `missingness.csv` (missing count and % per column and per station)
   - `station_statistics.csv` (pollutant concentrations per station)
   - `hourly_statistics.csv` (diurnal patterns)
   - `monthly_statistics.csv` (seasonal trends)
2. **`docs/phase3/FEATURE_SELECTION.md`:**
   - Detailed justification table documenting every feature, unit, source, and rationale.
3. **`docs/phase3/FORECASTING_SCENARIO.md`:**
   - Formal definition of forecast issue time $T$, prediction horizons, available features, and future masking.
4. **`reports/phase3/leakage_report.md`:**
   - 6-Point automated leakage audit report verifying zero lookahead, dynamic purge gaps, and station grouping.
5. **`reports/phase3/error_analysis.md`:**
   - Diagnostic analysis of model performance during high-pollution events, Diwali spikes, and monsoon cloud cover.
6. **`experiments/experiment_log.csv`:**
   - Structured audit log recording every experiment run, model type, parameters, and validation metrics.

---

## 11. PHASE 4 BACKEND / FORECAST API HANDOFF CONTRACT

Phase 4 requires clean, self-contained model artifacts to build the FastAPI backend service.

### 11.1 Exported Artifact Structure:
```
models/
├── NO2/
│   ├── model.pkl               # Trained LightGBM/Ensemble model bundle
│   ├── feature_schema.json     # Feature list, data types, units, and expected order
│   └── metadata.json           # Model version, train dates, horizons, metrics
│
└── O3/
    ├── model.pkl               # Trained LightGBM/Ensemble model bundle
    ├── feature_schema.json     # Feature list, data types, units, and expected order
    └── metadata.json           # Model version, train dates, horizons, metrics
```

### 11.2 `feature_schema.json` Format:
```json
{
  "model_version": "1.0.0",
  "target": "OZONE_ground",
  "feature_count": 38,
  "features": [
    {"name": "NO_ground", "dtype": "float64", "unit": "ug/m3", "missing_strategy": "native_nan"},
    {"name": "era5_temperature_c", "dtype": "float32", "unit": "degC", "missing_strategy": "error"},
    {"name": "ventilation_coeff", "dtype": "float32", "unit": "m2/s", "missing_strategy": "error"}
  ]
}
```

### 11.3 `metadata.json` Format:
```json
{
  "model_name": "LightGBM_Simplex_Ensemble",
  "target_variable": "OZONE_ground",
  "forecast_horizons_hours": [1, 3, 6, 12, 24, 48],
  "training_period": "2023-01-01 to 2024-12-31",
  "test_period": "2025-07-01 to 2025-12-31",
  "metrics": {
    "h1_r2": 0.952,
    "h24_r2": 0.865,
    "h48_r2": 0.812
  }
}
```

---

## 12. CONTINGENCY PLAYBOOK: WHAT IF ACCURACY FALLS BELOW TARGET?

If initial test runs do not reach $R^2 \ge 0.95$ at $t+1\text{h}$, apply these diagnostic steps in order:

```
                            DIAGNOSTIC & REMEDIATION WORKFLOW
                                            │
        ┌───────────────────────────────────┼───────────────────────────────────┐
        ▼                                   ▼                                   ▼
 [ Check Data Pipeline ]            [ Feature Enrichment ]              [ Loss & Model Tuning ]
 • Confirm inverse log1p            • Add 48h and 72h lags              • Switch to Huber Loss (δ=1.35)
 • Verify station groupby           • Add rolling min & max (3h, 6h)    • Tune num_leaves (63 to 255)
 • Check ~np.isnan() mask           • Add cross-station spatial lags    • Add CatBoost with native cat
 • Compare vs Persistence           • Add stubble/Diwali event flags    • Increase L2 reg_lambda (1.0 to 3.0)
```

1. **Verify `log1p` / `expm1` Round-Trip:** Ensure predictions are transformed back to physical space via $\exp(\tilde{y}) - 1$ before computing RMSE and $R^2$.
2. **Add Multi-Day Lag Features:** Extend the lag set to include $48\text{h}$ and $72\text{h}$ lags to capture day-of-week traffic cycles.
3. **Add Upwind Spatial Lags:** For each station, compute the concentration of the nearest upwind neighbor station based on `era5_wind_direction`.
4. **Switch to Huber Loss:** If extreme spikes cause large squared errors, use Huber Loss ($\delta = 1.35$) in LightGBM/PyTorch.
5. **Ensemble Stacking:** Combine LightGBM + CatBoost + BiLSTM via NNLS.

---

## 13. CLI EXECUTION COMMANDS & HOW TO RUN

The entire pipeline can be executed step-by-step or via the master runner:

```bash
# 1. Activate Python virtual environment
& ".\.venv\Scripts\Activate.ps1"

# 2. Run Step 0: Exploratory Data Analysis & EDA Reports
python scripts/phase3/00_eda_analysis.py

# 3. Run Step 1: Feature Engineering & Lag Generation
python scripts/phase3/01_feature_engineering.py

# 4. Run Step 2: Blocked Walk-Forward Cross-Validation
python scripts/phase3/02_cross_validation.py

# 5. Run Step 3: Train Multi-Horizon LightGBM Models (1h to 48h)
python scripts/phase3/03_train_lightgbm.py

# 6. Run Step 4: Train Deep Learning Models (GPU Accelerated)
python scripts/phase3/04_train_deep_learning.py

# 7. Run Step 5: Train Stacking Meta-Learner (NNLS)
python scripts/phase3/05_ensemble_stacking.py

# 8. Run Step 6: Test Set Evaluation & Persistence Benchmark
python scripts/phase3/06_evaluate_and_benchmark.py

# 9. Run Step 7: SHAP Feature Importance & Forecast Curves
python scripts/phase3/07_shap_and_visualizations.py

# OR RUN ENTIRE PIPELINE IN A SINGLE COMMAND:
python scripts/phase3/run_phase3_pipeline.py
```

---

*This document is the official engineering contract for Phase 3. Every constraint, directory path, and report specification herein is required for seamless validation and Phase 4 API deployment.*

**— Team AIRO2 Lead (Sudhith)**
