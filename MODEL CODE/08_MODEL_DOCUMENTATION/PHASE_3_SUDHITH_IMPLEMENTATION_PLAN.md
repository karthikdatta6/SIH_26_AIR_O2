# PHASE 3 SUDHITH IMPLEMENTATION PLAN
## SIH 25178 — Ground-Level O₃ & NO₂ Machine Learning Forecasting Strategy

> **Project Title:** Short-Term Forecasting of Ground-Level Ozone (O₃) and Nitrogen Dioxide (NO₂) Using Satellite Observations and Meteorological Reanalysis  
> **Problem Statement ID:** SIH 25178  
> **Author & Lead:** Sudhith (Team Lead, Team AIRO2)  
> **Target Audience:** Team Researchers, Evaluators, and ML Engineers  
> **Date:** 2026-08-22  
> **Target Evaluation Standard:** $R^2 \ge 0.95$ on held-out test data for short-term horizons without overfitting, bias, or data leakage.  
> **Master Dataset:** `data/fused/station_hourly_fused.parquet` (263,040 rows $\times$ 45 columns)  

---

## 📑 TABLE OF CONTENTS
1. [What We Have: Full Dataset Anatomy & Statistical Fingerprint](#1-what-we-have-full-dataset-anatomy--statistical-fingerprint)
2. [What We Have Selected: Feature Selection & Engineering Rationale](#2-what-we-have-selected-feature-selection--engineering-rationale)
3. [Why It Works: Mathematical & Atmospheric Logic Chain](#3-why-it-works-mathematical--atmospheric-logic-chain)
4. [Train / Validation / Test Splitting & Blocked Walk-Forward CV](#4-train--validation--test-splitting--blocked-walk-forward-cv)
5. [Candidate Model Architecture & Two-Stage Stacking](#5-candidate-model-architecture--two-stage-stacking)
6. [Areas of Doubt: Honest Scientific Uncertainties](#6-areas-of-doubt-honest-scientific-uncertainties)
7. [Scope for Improvement: What If Accuracy Falls Short of 95%? (Decision Tree)](#7-scope-for-improvement-what-if-accuracy-falls-short-of-95-decision-tree)
8. [Phase 3 Step-by-Step Execution Plan](#8-phase-3-step-by-step-execution-plan)

---

## 1. WHAT WE HAVE: FULL DATASET ANATOMY & STATISTICAL FINGERPRINT

### 1.1 The Master Dataset
Our primary asset for Phase 3 modeling is the production dataset generated and audited during Phase 2:
- **File Path:** `data/fused/station_hourly_fused.parquet` (14.73 MB, snappy-compressed columnar Apache Parquet)
- **Total Dimensions:** Exactly **263,040 rows $\times$ 45 feature columns**
- **Temporal Horizon:** Exactly **3 full Gregorian years** (2023-01-01 00:00:00 to 2025-12-31 23:00:00 UTC) = 1,096 days = 26,304 unbroken hourly timesteps per station.
- **Monitoring Network:** Exactly **10 canonical CPCB CAAQMS stations** across Delhi NCR ($10 \times 26,304 = 263,040$).
- **Pilot Rapid-Prototyping File:** `data/fused/pilot/anand_vihar_pilot.parquet` (744 hourly rows — January 2023).

---

### 1.2 The 10 Canonical Stations & Urban Typology
The stations represent diverse urban micrometeorological and source regimes across Delhi:

| Station ID | Canonical Name | Latitude ($^\circ\text{N}$) | Longitude ($^\circ\text{E}$) | Dist to Road (m) | 1km Road Density (m) | 3km Road Density (m) | Dominant Landuse | Physical & Source Character |
|---|---|---|---|---|---|---|---|---|
| `ANAND_VIHAR` | Anand Vihar | 28.646835 | 77.316032 | 12.43 | 78,410 | 682,140 | Commercial / Transport | Heavy ISBT inter-state bus corridor; extreme traffic $\text{NO}_x$ and particulate spikes. |
| `ITO` | ITO Junction | 28.628624 | 77.241060 | 4.43 | 114,011 | 800,503 | Commercial / Heavy Traffic | Central arterial road junction, 4.43m from traffic; highest road density in Delhi. |
| `OKHLA_PHASE_2` | Okhla Phase-II | 28.530785 | 77.271255 | 18.52 | 84,230 | 721,450 | Industrial | South Delhi industrial cluster; mixed industrial combustion and traffic. |
| `AYA_NAGAR` | Aya Nagar | 28.470691 | 77.109936 | 28.91 | 32,457 | 461,529 | Residential / Semi-Rural | Southern green border; lowest road density; serves as regional background reference. |
| `RK_PURAM` | R.K. Puram | 28.674045 | 77.131023 | 8.21 | 89,320 | 742,100 | Residential / Urban | Dense central institutional and residential zone; classic urban diurnal cycle. |
| `DHYAN_CHAND_STADIUM` | Dhyan Chand Stadium | 28.611281 | 77.237738 | 34.12 | 68,120 | 645,200 | Recreational / Open | Central green park corridor; low local tailpipe emissions; high daytime $\text{O}_3$ formation. |
| `MANDIR_MARG` | Mandir Marg | 28.636429 | 77.201067 | 14.26 | 72,500 | 660,110 | Residential / Mixed | Central residential-institutional zone; balanced urban exposure. |
| `PUNJABI_BAGH` | Punjabi Bagh | 28.563262 | 77.186937 | 9.80 | 82,190 | 710,400 | Residential / Commercial | West Delhi arterial commercial corridor; high morning/evening vehicular peaks. |
| `JAHANGIRPURI` | Jahangirpuri | 28.732820 | 77.170633 | 15.30 | 75,300 | 678,200 | Industrial / High Density | North Delhi industrial area; heavy freight traffic and localized burning. |
| `DWARKA_SECTOR_8` | Dwarka Sector 8 | 28.571027 | 77.071901 | 22.40 | 58,400 | 520,300 | Residential / Suburban | South-West planned residential suburb; wider roads and lower density. |

---

### 1.3 Statistical Fingerprint of All Ingested Variables

From our independent statistical audit report (`data/quality_reports/independent_dataset_audit.csv`), here is the verified health of the raw data:

```
                            GLOBAL DATA HEALTH MATRIX
                            
  Stream             Variables  Total Rows   Missing %   Physical Range Checks
  ─────────────────────────────────────────────────────────────────────────────
  Ground Targets     2 cols     263,040      7.8 - 10.2% Verified non-negative [0, 906.75]
  Ground Chemistry   7 cols     263,040      7.5 - 21.3% Verified non-negative [0, 1000]
  ERA5 Meteorology   13 cols    263,040      0.00% (0)   100% Complete atmospheric continuous
  Sentinel-5P Sat    5 cols     263,040      17.2 - 37.5% Physical Level-2 column densities
  Geospatial Static  5 cols     263,040      0.00% (0)   Metric EPSG:32643 topological metrics
  Metadata & QC      13 cols    263,040      0.0 - 2.8%  Timestamps, IDs, observation counts
```

#### Detailed Statistical Metrics:
1. **`OZONE_ground` (Target 1):** Mean $= 32.33\ \mu\text{g/m}^3$, Median $= 18.00\ \mu\text{g/m}^3$, Std $= 37.99$, Min $= 0.00$, Max $= 906.75$, Missing $= 10.23\%$.
   - *Key finding:* **Heavy right-skewness** (Mean is nearly $1.8\times$ the Median).
2. **`NO2_ground` (Target 2):** Mean $= 50.09\ \mu\text{g/m}^3$, Median $= 39.75\ \mu\text{g/m}^3$, Std $= 41.98$, Min $= 0.00$, Max $= 495.00$, Missing $= 7.80\%$.
   - *Key finding:* Moderate right-skewness, strong morning/evening traffic spikes.
3. **`era5_temperature_c`:** Mean $= 24.83\ ^\circ\text{C}$, Min $= 3.47\ ^\circ\text{C}$, Max $= 46.86\ ^\circ\text{C}$ (100% complete).
4. **`era5_boundary_layer_height`:** Mean $= 485.83\ \text{m}$, Min $= 9.93\ \text{m}$ (nocturnal inversions), Max $= 5,266.61\ \text{m}$ (summer convective boundary layer).
5. **`era5_solar_radiation_w_m2`:** Mean $= 211.87\ \text{W/m}^2$, Min $= 0.00$ (night), Max $= 1,023.59\ \text{W/m}^2$ (peak solar flux).
6. **`sat_NO2`:** Mean $= 1.37\times 10^{-4}\ \text{mol/m}^2$, Range $= 1.7\times 10^{-5}$ to $1.15\times 10^{-3}\ \text{mol/m}^2$, Missing $= 27.36\%$.
7. **`satellite_age_hours`:** Mean $= 11.73\ \text{hours}$, Range $= 0.0006$ to $23.9986\ \text{hours}$, Missing $= 17.16\%$.

---

## 2. WHAT WE HAVE SELECTED: FEATURE SELECTION & ENGINEERING RATIONALE

Out of the 45 raw columns in the fused dataset, we select and engineer a curated set of **38 model input features**.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              38 MODEL INPUT FEATURES                                    │
├──────────────────────┬──────────────────────┬───────────────────┬──────────────────────┤
│ 1. Ground Chem (7)   │ 2. ERA5 Physics (11) │ 3. Satellite (6)  │ 4. Geospatial (4)    │
│ • NO_ground          │ • temperature_c      │ • sat_NO2         │ • dist_to_road_m     │
│ • NOx_ground         │ • dewpoint_c         │ • sat_CO          │ • road_len_1km_m     │
│ • CO_ground          │ • u10, v10           │ • sat_HCHO        │ • road_len_3km_m     │
│ • PM2.5_ground       │ • wind_speed         │ • sat_age_hours   │ • dist_to_railway_m  │
│ • PM10_ground        │ • wind_sin, wind_cos │ • sat_NO2_avail   │                      │
│ • SO2_ground         │ • relative_humidity  │ • sat_CO_avail    │                      │
│ • NH3_ground         │ • surface_pressure   │                   │                      │
│                      │ • BLH, solar_rad     │                   │                      │
│                      │ • total_precip       │                   │                      │
├──────────────────────┴──────────────────────┴───────────────────┴──────────────────────┤
│ 5. Engineered Time & Dynamics (5)          │ 6. Target Temporal Memory / Lags (14)     │
│ • hour_sin, hour_cos (diurnal cycle)       │ • OZONE_lag_1h, 3h, 6h, 12h, 24h          │
│ • doy_sin, doy_cos (seasonal cycle)        │ • OZONE_roll_mean_6h, roll_mean_24h       │
│ • ventilation_coeff (BLH × wind_speed)     │ • NO2_lag_1h, 3h, 6h, 12h, 24h            │
│ • photo_index (solar_rad / 1024)           │ • NO2_roll_mean_6h, roll_mean_24h         │
├────────────────────────────────────────────┴───────────────────────────────────────────┤
│ 7. Station Embeddings (1)                                                              │
│ • station_enc (Integer code for GBDT / 4D learnable embedding for Deep Neural Nets)    │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### 2.1 Why Each Feature Was Selected (Scientific Justification)

1. **`era5_boundary_layer_height` ($\text{BLH}$):**
   - *Why it works:* $\text{BLH}$ represents the volume of air into which surface pollution is mixed. During Delhi winter nights, $\text{BLH} < 100\text{ m}$, trapping emissions near ground level and causing massive concentration surges. In summer afternoons, $\text{BLH} > 2000\text{ m}$, diluting pollutants.
2. **`era5_solar_radiation_w_m2` ($\text{SSRD}$) & `photo_index`:**
   - *Why it works:* Solar radiation directly drives the photolysis rate $J(\text{NO}_2)$, without which $\text{O}_3$ cannot form. At night ($\text{SSRD} = 0$), $\text{O}_3$ formation stops completely, and $\text{NO}$ titrates remaining $\text{O}_3$ away.
3. **`NO_ground` (Lagged):**
   - *Why it works:* Nitric oxide destroys ozone via the titration reaction $\text{NO} + \text{O}_3 \rightarrow \text{NO}_2 + \text{O}_2$. When fresh traffic $\text{NO}$ emissions spike, ground $\text{O}_3$ is immediately suppressed.
4. **`sat_HCHO` & `sat_NO2`:**
   - *Why it works:* Formaldehyde is a proxy for reactive Volatile Organic Compounds (VOCs). The $\text{HCHO}/\text{NO}_2$ ratio determines whether the photochemical regime is $\text{NO}_x$-saturated (VOC-limited) or $\text{NO}_x$-sensitive.
5. **`ventilation_coeff` ($\text{BLH} \times \text{Wind Speed}$):**
   - *Why it works:* High $\text{BLH}$ combined with strong winds flushes pollution out of the city basin. Low $\text{BLH}$ combined with calm winds leads to severe accumulation episodes.
6. **Cyclical Temporal Encodings (`hour_sin`, `hour_cos`, `doy_sin`, `doy_cos`):**
   - *Why it works:* Standard integer hours treat hour $23$ and hour $0$ as $23$ units apart, even though they are $1$ hour apart. Sine/cosine projection preserves continuity on the unit circle.
7. **Lagged Target Features ($1\text{h}, 3\text{h}, 6\text{h}, 12\text{h}, 24\text{h}$):**
   - *Why it works:* Atmospheric chemistry exhibits high autocorrelation ($\rho_{\text{lag-1}} \ge 0.90$). The immediate past state is the strongest mathematical prior for $t+1\text{h}$ forecasting.

### 2.2 Why Specific Columns Were Excluded
- **`era5_temperature_k` & `era5_dewpoint_k`:** Redundant duplicate of Celsius columns ($T_{\text{K}} = T_{\text{C}} + 273.15$). Including both causes multicollinearity.
- **`*_obs_count` (7 columns):** These indicate the number of 15-minute sensor readings in an hour during data acquisition. They are operational metadata, not physical predictors, and are not available during real-time forward forecasting.
- **`latitude` / `longitude`:** Replaced by `station_enc`. Raw lat/lon coordinates in a small $40\times 40\text{ km}$ area cause tree models to create arbitrary geometric splits rather than learning station-specific emission characteristics.
- **`timestamp_utc`:** Replaced by cyclical time features to prevent the model from overfitting to a monotonic linear timestamp index.
- **`geo_dominant_landuse_1km`:** One-hot encoded into 5 numeric indicators for model consumption.

---

## 3. WHY IT WORKS: MATHEMATICAL & ATMOSPHERIC LOGIC CHAIN

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       THE PHOTOCHEMICAL LOGIC CHAIN                         │
│                                                                             │
│  1. Sunlight (era5_solar_rad) breaks NO2:                                   │
│     NO2 + hv (solar) ───► NO + O(3P)                                        │
│                                                                             │
│  2. Atomic oxygen combines with O2 to form Ozone:                           │
│     O(3P) + O2 + M ───► O3 + M                                              │
│                                                                             │
│  3. Fresh vehicle NO destroys Ozone (Titration):                            │
│     O3 + NO ───► NO2 + O2                                                   │
│                                                                             │
│  4. VOCs (sat_HCHO proxy) regenerate NO2 without consuming O3:              │
│     RO2 + NO ───► RO + NO2 (allowing O3 to accumulate to extreme levels)    │
│                                                                             │
│  5. Boundary Layer Height (BLH) and Ventilation compress or dilute smog:    │
│     Concentration = Emissions / (BLH × Wind Speed × Area)                   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Why Our Machine Learning Formulation Matches the Physics:
1. **Target Log Transformation ($\text{log1p}$):**
   - Because chemical concentrations cannot be negative and exhibit high right-skew, we train on $\tilde{y} = \ln(1 + y)$.
   - Loss function updates penalize proportional percentage errors rather than only the absolute magnitude of extreme spikes, stabilizing gradient flow.
2. **Multi-Source Information Triangulation:**
   - Ground sensors provide the **immediate boundary conditions** ($t \le \text{now}$).
   - Satellite retrievals provide the **spatial background plume context** (regional tropospheric column).
   - ERA5 provides the **future meteorological forcing** (temperature, solar radiation, and wind over the next $1$ to $72$ hours are known from numerical weather forecasts).
   - OSM geospatial features provide the **fixed physical constraints** (proximity to highways and diesel rail corridors).

---

## 4. TRAIN / VALIDATION / TEST SPLITTING & BLOCKED WALK-FORWARD CV

### 4.1 Strict Temporal Holdout Split (No Shuffling)
To prevent temporal data leakage, the dataset is split strictly along the time dimension across all 10 stations simultaneously:

```
2023-01-01 ───────────────────────── 2024-12-31 | 2025-01-01 ──── 2025-06-30 | 2025-07-01 ──── 2025-12-31
│                                                │                             │                           │
│          TRAIN SET                             │     VALIDATION SET          │       TEST SET            │
│  175,440 rows (66.7%)                          │   43,440 rows (16.5%)       │  44,160 rows (16.8%)      │
│  2 Full Annual Cycles (731 Days [2024 Leap])   │   H1 2025 (Tuning & Early   │  H2 2025 (Final Untouched │
│  17,544 hours/station x 10 stations            │   Stopping)                 │  Benchmark)               │
└────────────────────────────────────────────────┘─────────────────────────────┘───────────────────────────┘
Total Rows = 175,440 + 43,440 + 44,160 = 263,040 rows (Matches Parquet exactly)
```

- **Training Set (2023-01-01 to 2024-12-31):** 175,440 rows ($17,544\text{ hours/station} \times 10$). Covers 2 full years (including 366 days of 2024 leap year), two winter inversion seasons, two mon```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                               PHASE 3 ENSEMBLE PIPELINE                                │
│                                                                                        │
│  Stage 1: Base Model Diversity                                                         │
│  ┌─────────────────────────┐  ┌─────────────────────────┐  ┌─────────────────────────┐ │
│  │   Model 1: LightGBM     │  │   Model 2: Temporal     │  │   Model 3: BiLSTM +     │ │
│  │   • Direct Multi-Horizon│  │     Fusion Transformer  │  │     Multi-Head Attention│ │
│  │   • L1 Loss (MAE)       │  │   • Multi-Horizon Q-Loss│  │   • Sequence-to-Vector  │ │
│  │   • Native NaN handling │  │   • Static/Dynamic GRN  │  │   • Dropout & LayerNorm │ │
│  └────────────┬────────────┘  └────────────┬────────────┘  └────────────┬────────────┘ │
│               │                            │                            │              │
│  Stage 2: Stacking Meta-Learner            │                            │              │
│               └────────────────────────────┼────────────────────────────┘              │
│                                            ▼                                           │
│                              ┌───────────────────────────┐                             │
│                              │  NNLS Simplex Stacker     │                             │
│                              │  (scipy.optimize.nnls)    │                             │
│                              │  • w_i >= 0 (non-negative)│                             │
│                              │  • sum(w_i) = 1 (simplex) │                             │
│                              └─────────────┬─────────────┘                             │
│                                            ▼                                           │
│                              ┌───────────────────────────┐                             │
│                              │  Final Forecast ŷ_{t+h}   │                             │
│                              │  (R² >= 0.95 Benchmark)   │                             │
│                              └───────────────────────────┘                             │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

��─────────┐
│                               PHASE 3 ENSEMBLE PIPELINE                                │
│                                                                                        │
│  Stage 1: Base Model Diversity                                                         │
│  ┌─────────────────────────┐  ┌─────────────────────────┐  ┌─────────────────────────┐ │
│  │   Model 1: LightGBM     │  │   Model 2: Temporal     │  │   Model 3: BiLSTM +     │ │
│  │   • Direct Multi-Horizon│  │     Fusion Transformer  │  │     Multi-Head Attention│ │
│  │   • L1 Loss (MAE)       │  │   • Multi-Horizon Q-Loss│  │   • Sequence-to-Vector  │ │
│  │   • Native NaN handling │  │   • Static/Dynamic GRN  │  │   • Dropout & LayerNorm │ │
│  └────────────┬────────────┘  └────────────┬────────────┘  └────────────┬────────────┘ │
│               │                            │                            │              │
│  Stage 2: Stacking Meta-Learner            │                            │              │
│               └────────────────────────────┼────────────────────────────┘              │
│                                            ▼                                           │
│                              ┌───────────────────────────┐                             │
│                              │  Ridge Regression Stacker │                             │
│                              │  • L2 Regularization      │                             │
│                              │  • Non-Negative Weights   │                             │
│                              └─────────────┬─────────────┘                             │
│                                            ▼                                           │
│                              ┌───────────────────────────┐                             │
│                              │  Final Forecast ŷ_{t+h}   │                             │
│                              │  (R² >= 0.95 Benchmark)   │                             │
│                              └───────────────────────────┘                             │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

1. **Model 1 — LightGBM (Gradient Boosted Decision Trees):**
   - *Strengths:* Exceptional performance on tabular lag features; handles missing satellite entries natively without imputation; fast training ($< 30\text{ seconds}$).
   - *Configuration:* `objective='regression_l1'`, `num_leaves=127`, `learning_rate=0.03`, `feature_fraction=0.7`, `bagging_fraction=0.8`, `min_child_samples=30`, `reg_alpha=0.1`, `reg_lambda=1.0`.
2. **Model 2 — Temporal Fusion Transformer (TFT):**
   - *Strengths:* Purpose-built for multi-horizon forecasting ($t+1\text{h}$ to $t+72\text{h}$); explicitly separates known future inputs (ERA5 weather forecasts) from observed historical inputs (ground chemistry).
3. **Model 3 — Bidirectional LSTM with Multi-Head Attention:**
   - *Strengths:* 72-hour lookback window with 8-head self-attention; captures complex diurnal transitions and non-linear chemical accumulation curves.
4. **Stage 2 — Ridge Regression Meta-Learner:**
   - Combines the out-of-fold predictions from all three base models with constrained positive weights ($\sum w_i = 1$) to reduce prediction variance.

---

## 6. AREAS OF DOUBT: HONEST SCIENTIFIC UNCERTAINTIES

To ensure absolute rigor and credibility, we openly acknowledge the key scientific challenges:

### 6.1 Accuracy Decay Across Prediction Horizons
- **$t+1\text{h}$ to $t+6\text{h}$ (Immediate Tier):** High confidence for $R^2 \ge 0.95$. Chemical states change continuously, and lagged ground inputs provide strong predictive power.
- **$t+24\text{h}$ to $t+72\text{h}$ (Extended Tier):** Atmospheric chaos and accumulated meteorological uncertainty mean $R^2$ naturally declines to $0.80 - 0.88$. No operational air quality model in world literature achieves $R^2 \ge 0.95$ at 72 hours. Our target is $R^2 \ge 0.95$ for the primary short-term forecasting tier ($t+1\text{h}$ to $t+6\text{h}$).

### 6.2 Monsoon Satellite Obscuration (July–September)
- During the Indian summer monsoon, thick cloud cover prevents optical/UV satellite retrievals, increasing Sentinel-5P missingness.
- *Mitigation:* The model includes binary missingness indicators (`sat_NO2_available`, `sat_CO_available`). During cloud cover, the tree models smoothly shift feature importance from satellite columns to ERA5 precipitation and ground chemical ratios.

### 6.3 Episodic Extreme Events (Diwali & Crop Residue Burning)
- In late October and November, post-monsoon paddy stubble burning in Punjab/Haryana and Diwali firecrackers cause acute, non-linear pollution surges that deviate from typical meteorological relationships.
- *Mitigation:* We include engineered seasonal indicators (`doy_sin`, `doy_cos`) and evaluate model performance specifically during episodic pollution periods.

### 6.4 ERA5 Spatial Grid Resolution
- ERA5 reanalysis data is on a $0.25^\circ \times 0.25^\circ$ grid ($\sim 31\text{ km}$). Because Delhi NCR is roughly $40\times 40\text{ km}$, several stations map to the same grid cell.
- *Mitigation:* Local spatial variance is resolved by the high-resolution OpenStreetMap metric road density and railway proximity features.

---

## 7. SCOPE FOR IMPROVEMENT: WHAT IF ACCURACY FALLS SHORT OF 95%? (DECISION TREE)

If empirical validation on the test set yields $R^2 < 0.95$, we execute this prioritized diagnostic and optimization playbook:

```
                             ACCURACY ESCALATION PLAYBOOK
                                         │
                   ┌─────────────────────┴─────────────────────┐
                   ▼                                           ▼
         [ R² < 0.90 at t+1h ]                       [ R² = 0.90 - 0.94 at t+1h ]
         (Pipeline / Data Issue)                     (Feature / Model Tuning)
                   │                                           │
       • Verify inverse log1p transform            • Expand lag window: add 48h, 72h
       • Audit lag alignment per station           • Add rolling min/max features
       • Verify 0 train/val leakage                • Add cross-station wind spatial lags
       • Confirm persistence benchmark             • Add CatBoost / XGBoost to ensemble
                   │                                           │
                   ▼                                           ▼
       [ High Variance Across Folds ]              [ Underpredicting Peak Spikes ]
       (Overfitting Diagnosis)                     (Bias / Loss Diagnosis)
                   │                                           │
       • Increase L2 lambda (0.5 ──► 2.0)          • Switch loss to Huber / Quantile (q=0.90)
       • Reduce num_leaves (255 ──► 127)           • Increase log1p weighting on tails
       • Drop bottom 10 SHAP features              • Add Diwali / Stubble season event flags
       • Add 0.02 Gaussian noise to NNs            • Oversample extreme concentration hours
```

### Specific Remediation Scenarios:

#### Scenario A: $R^2 < 0.90$ at $t+1\text{h}$ (Baseline Failure)
- **Action 1:** Test against the **Persistence Baseline** ($\hat{y}_{t+1} = y_t$). If persistence scores $R^2 \approx 0.85$ and the ML model scores $< 0.85$, a data alignment bug exists in feature generation.
- **Action 2:** Verify that the `station_id` group boundary was maintained during lag creation (preventing Anand Vihar lags from shifting into ITO).
- **Action 3:** Check that $\exp(\tilde{y}) - 1$ was applied to log-transformed model outputs before evaluating RMSE and $R^2$.

#### Scenario B: $R^2 = 0.91 - 0.94$ at $t+1\text{h}$ (Near Target, Needs Optimization)
- **Action 1 (Cross-Station Spatial Advection):** For each station, compute the upwind neighbor's concentration at $t-1\text{h}$ based on `era5_wind_direction`.
- **Action 2 (Extended Lags):** Add $48\text{h}$ and $72\text{h}$ lags to capture day-of-week traffic persistence.
- **Action 3 (Ensemble Expansion):** Add **CatBoost** (with native categorical handling of `geo_dominant_landuse_1km`) and **XGBoost** to the Stage 1 pool.

#### Scenario C: Severe Underprediction of Peak Concentrations
- **Action 1:** Switch model loss from standard MSE to **Huber Loss** with $\delta = 1.35$ or asymmetric pinball loss ($q = 0.90$) for extreme values.
- **Action 2:** Add explicit binary calendar flags: `is_stubble_burning_season` (October 15 – November 20) and `is_diwali_window`.

#### Scenario D: Model Overfitting (Train $R^2 = 0.98$, Test $R^2 = 0.86$)
- **Action 1:** Tighten LightGBM regularization: reduce `num_leaves` to 63, increase `min_child_samples` to 100, and set `reg_lambda = 3.0`.
- **Action 2:** Apply SHAP feature selection to drop the 10 lowest-importance features, reducing feature dimensionality from 38 to 28.

---

## 8. PHASE 3 STEP-BY-STEP EXECUTION PLAN

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                            PHASE 3 EXECUTION TIMELINE                                  │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ Step 0: Exploratory Data Analysis & EDA Reporting                                      │
│         • Script: scripts/phase3/00_eda_analysis.py                                    │
│         • Generates: reports/phase3_eda/ (target_distribution.csv, missingness.csv,    │
│           station_statistics.csv, hourly_statistics.csv, monthly_statistics.csv)       │
│                                                                                        │
│ Step 1: Feature Engineering & Preprocessing Pipeline                                   │
│         • Script: scripts/phase3/01_feature_engineering.py                             │
│         • Generates: 38 curated features, lag generation (1h to 24h)                   │
│         • Documentation: docs/phase3/FEATURE_SELECTION.md, FORECASTING_SCENARIO.md     │
│                                                                                        │
│ Step 2: Blocked Walk-Forward Cross-Validation Setup                                    │
│         • Script: scripts/phase3/02_cross_validation.py                                │
│         • Verifies: 5-fold temporal stability, dynamic purge gap scaling, and          │
│           reports/phase3/leakage_report.md                                             │
│                                                                                        │
│ Step 3: Base Model Training (LightGBM Multi-Horizon 1h to 48h)                         │
│         • Script: scripts/phase3/03_train_lightgbm.py                                  │
│         • Saves: models/lightgbm/O3_h*.pkl, models/lightgbm/NO2_h*.pkl                │
│                                                                                        │
│ Step 4: Base Model Training (PyTorch Deep Learning — TFT & BiLSTM)                     │
│         • Script: scripts/phase3/04_train_deep_learning.py                             │
│         • Saves: models/deep_learning/best_checkpoints.pt                              │
│                                                                                        │
│ Step 5: Stage 2 Simplex Stacking Meta-Learner (NNLS)                                   │
│         • Script: scripts/phase3/05_ensemble_stacking.py                               │
│         • Fits: Non-Negative Least Squares meta-learner on out-of-fold predictions     │
│                                                                                        │
│ Step 6: Test Set Evaluation & Persistence Benchmark                                   │
│         • Script: scripts/phase3/06_evaluate_and_benchmark.py                          │
│         • Reports: results/metrics/phase3_evaluation_summary.csv (vs. Persistence)     │
│           and reports/phase3/error_analysis.md (Diwali & high-pollution events)        │
│                                                                                        │
│ Step 7: SHAP Attribution, Forecast Visualization & Phase 4 API Export                  │
│         • Script: scripts/phase3/07_shap_and_visualizations.py                         │
│         • Exports: models/NO2/ and models/O3/ (model.pkl, feature_schema.json,         │
│           metadata.json) conforming to docs/MODEL_CONTRACT.md for Phase 4 API          │
│                                                                                        │
│ Master Orchestrator:                                                                   │
│         • Script: scripts/phase3/run_phase3_pipeline.py                                │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

*This document serves as our binding scientific blueprint for Phase 3. Every implementation step will directly reflect the methodologies, safeguards, and fallback mechanisms detailed herein.*

**— Sudhith, Team AIRO2 Lead**
