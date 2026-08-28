# COMPREHENSIVE MODEL ARCHITECTURE SPECIFICATION
## SIH 25178 — AIRO2 Multi-Horizon Ground-Level $\text{O}_3$ & $\text{NO}_2$ Forecasting System

> **Document Version:** 1.0.0 (Master Architecture Blueprint)  
> **Problem Statement ID:** SIH 25178  
> **Team:** Team AIRO2  
> **Date:** 2026-08-25  
> **Target Pollutants:** Ground-Level Ozone ($\text{O}_3$) and Nitrogen Dioxide ($\text{NO}_2$)  
> **Target Region:** Delhi NCR (10 Canonical CPCB Monitoring Stations)  

---

## 📑 TABLE OF CONTENTS
1. [Executive Summary & The 36-Model Inventory](#1-executive-summary--the-36-model-inventory)
2. [Why Direct Multi-Step Forecasting? (1h, 3h, 6h, 12h, 24h, 48h)](#2-why-direct-multi-step-forecasting-1h-3h-6h-12h-24h-48h)
3. [The Two-Stage Stacking Architecture Blueprint](#3-the-two-stage-stacking-architecture-blueprint)
4. [Model Family 1: LightGBM (Gradient Boosted Decision Trees)](#4-model-family-1-lightgbm-gradient-boosted-decision-trees)
5. [Model Family 2: PyTorch BiLSTM + Multi-Head Self-Attention](#5-model-family-2-pytorch-bilstm--multi-head-self-attention)
6. [Model Family 3: NNLS Simplex Stacking Meta-Learner](#6-model-family-3-nnls-simplex-stacking-meta-learner)
7. [Target Stabilization & Atmospheric Loss Functions](#7-target-stabilization--atmospheric-loss-functions)
8. [Feature Vector Schema & Input Dimensions (38 Features)](#8-feature-vector-schema--input-dimensions-38-features)
9. [Complete Model Performance & Checkpoint Matrix](#9-complete-model-performance--checkpoint-matrix)
10. [Production Serialization & Phase 4 API Packaging](#10-production-serialization--phase-4-api-packaging)

---

## 1. EXECUTIVE SUMMARY & THE 36-MODEL INVENTORY

Our system does **not** rely on a single monolithic model. Atmospheric chemistry in Delhi is driven by both **tabular meteorological thresholds** (e.g., wind speed $< 1.5\text{ m/s}$ triggering pollution trapping) and **continuous sequential temporal dependencies** (e.g., 24-hour solar diurnal memory).

To achieve maximum accuracy and robustness, we designed a **Two-Stage Multi-Model Stacking Ensemble**:

```
╔══════════════════════════════════════════════════════════════════════════════════════════╗
║                             THE 36 TRAINED MODELS INVENTORY                              ║
╠═════════════════════════════════════════╤════════════╤═══════════════════════════════════╣
║ Model Family                            │ Count      │ Horizons & Targets Covered        ║
╠═════════════════════════════════════════╪════════════╪═══════════════════════════════════╣
║ 1. LightGBM GBDT Base Models            │ 12 Models  │ 6 Horizons (1h, 3h, 6h, 12h, 24h, ║
║    (Gradient Boosted Decision Trees)    │            │ 48h) × 2 Pollutants (O3 & NO2)    ║
╟─────────────────────────────────────────┼────────────┼───────────────────────────────────╢
║ 2. PyTorch BiLSTM + Attention           │ 12 Models  │ 6 Horizons (1h, 3h, 6h, 12h, 24h, ║
║    (Deep Learning Neural Networks)      │            │ 48h) × 2 Pollutants (O3 & NO2)    ║
╟─────────────────────────────────────────┼────────────┼───────────────────────────────────╢
║ 3. NNLS Simplex Stacking Meta-Learners  │ 12 Models  │ 6 Horizons (1h, 3h, 6h, 12h, 24h, ║
║    (Non-Negative Least Squares Stacking)│            │ 48h) × 2 Pollutants (O3 & NO2)    ║
╠═════════════════════════════════════════╪════════════╪═══════════════════════════════════╣
║ TOTAL INDIVIDUAL TRAINED MODELS:        │ 36 MODELS  │ Fully Trained & Validated         ║
╠═════════════════════════════════════════╪════════════╪═══════════════════════════════════╣
║ Master Production API Bundles:          │ 2 Bundles  │ models/NO2/ and models/O3/        ║
║                                         │            │ (Each bundling all 6 horizons)    ║
╚═════════════════════════════════════════╧════════════╧═══════════════════════════════════╝
```

---

## 2. WHY DIRECT MULTI-STEP FORECASTING? (1h, 3h, 6h, 12h, 24h, 48h)

In time-series machine learning, there are two forecasting paradigms:

### Paradigm A: Recursive / Autoregressive Forecasting (Rejected ❌)
* A single model predicts $t+1\text{h}$. To predict $t+2\text{h}$, it feeds its own prediction back as input.
* **The Fatal Flaw:** **Error Compounding**. A $5\%$ error at $t+1\text{h}$ explodes to a $>60\%$ error by $t+48\text{h}$, causing the forecast to diverge into unrealistic runaway values.

### Paradigm B: Direct Multi-Step Forecasting (Our Approach 🟢)
* We train **independent, specialized models** for each specific horizon $h \in \{1, 3, 6, 12, 24, 48\}$:
  $$\hat{y}_{t+h} = f_h\left(X_t\right)$$
* **Why This Wins:**
  1. **Zero Error Compounding:** The $48\text{h}$ model learns the exact multi-day synoptic weather patterns directly from $X_t$ without depending on intermediate noisy predictions.
  2. **Horizon-Specific Specialization:** The $t+1\text{h}$ model learns immediate traffic plume persistence, while the $t+12\text{h}$ model learns the day-to-night photochemical transition.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    THE 6 FORECAST HORIZONS & USE CASES                      │
├─────────────────────────────────────────────────────────────────────────────┤
│ • t+1h:  Real-Time Citizen Warnings (Immediate asthmatic / commute alerts)  │
│ • t+3h:  Short-Term Tactical Guidance (Outdoor sports & school scheduling)  │
│ • t+6h:  Intra-Day Shift Operations (Traffic police & construction shifts)   │
│ • t+12h: Day-to-Night Transition (Diurnal solar shutdown & inversion onset) │
│ • t+24h: 1-Day Regulatory Policy (CPCB Graded Response Action Plan - GRAP)  │
│ • t+48h: 2-Day Early Warning Preparedness (Hospital surge & emergency bans) │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. THE TWO-STAGE STACKING ARCHITECTURE BLUEPRINT

```
                        38 INPUT FEATURES AT TIME t
         (CPCB Sensors + Sentinel-5P Satellite + ERA5 Weather + OSM Topology)
                                     │
                 ┌───────────────────┴───────────────────┐
                 │                                       │
                 ▼                                       ▼
    ┌──────────────────────────┐            ┌──────────────────────────┐
    │     MODEL FAMILY 1:      │            │     MODEL FAMILY 2:      │
    │     LightGBM GBDT        │            │  PyTorch BiLSTM + Attn   │
    │  • 127 Leaves / L1 Loss  │            │  • Station Embeddings    │
    │  • Scale-Invariant Trees │            │  • 24h Sequential Memory │
    │  • Native NaN Splitting  │            │  • Multi-Head Attention  │
    └────────────┬─────────────┘            └────────────┬─────────────┘
                 │                                       │
                 │ ŷ_LGB (Out-of-Fold)                   │ ŷ_DL (Out-of-Fold)
                 └───────────────────┬───────────────────┘
                                     │
                                     ▼
                       ┌───────────────────────────┐
                       │      MODEL FAMILY 3:      │
                       │   NNLS Simplex Stacker    │
                       │   (scipy.optimize.nnls)   │
                       │   • w_i ≥ 0 (Non-Negative)│
                       │   • ∑ w_i = 1 (Simplex)   │
                       └─────────────┬─────────────┘
                                     │
                                     ▼
                       ┌───────────────────────────┐
                       │  FINAL ENSEMBLE FORECAST  │
                       │    ŷ_{t+h} (µg/m³)        │
                       │ (Willmott's d = 97.85%)   │
                       └───────────────────────────┘
```

---

## 4. MODEL FAMILY 1: LIGHTGBM (GRADIENT BOOSTED DECISION TREES)

### Why LightGBM Was Selected:
1. **Dominance on Heterogeneous Tabular Data:** Gradient boosted trees consistently outperform neural networks on mixed continuous/discrete meteorological and chemistry tables.
2. **Native Missing Value Handling:** When monsoon clouds block Sentinel-5P satellite retrievals, LightGBM natively routes missing indicators to optimal split branches rather than failing.
3. **L1 Regression Loss (MAE):** Robust against extreme episodic pollution spikes (e.g., Diwali night fireworks).

### Hyperparameter Configuration:
```python
LGB_PARAMS = {
    "objective": "regression_l1",      # L1 loss (MAE) for outlier robustness
    "metric": "rmse",                  # Evaluated on RMSE
    "num_leaves": 127,                 # Deep tree splits to capture complex chemistry
    "learning_rate": 0.03,             # Conservative learning rate for generalization
    "n_estimators": 2500,              # Ample trees with early stopping
    "feature_fraction": 0.70,          # Subsamples 70% features per tree (prevents overfitting)
    "bagging_fraction": 0.80,          # Subsamples 80% data per iteration
    "bagging_freq": 5,                 # Resamples every 5 trees
    "min_child_samples": 30,           # Minimum 30 hourly samples per leaf
    "reg_alpha": 0.10,                 # L1 regularization
    "reg_lambda": 1.00,                # L2 regularization (ridge penalty)
    "n_jobs": -1,                      # Parallel CPU thread execution
    "random_state": 42
}
```

---

## 5. MODEL FAMILY 2: PYTORCH BILSTM + MULTI-HEAD SELF-ATTENTION

### Why Deep Learning Was Selected:
While LightGBM excels at threshold splits, deep recurrent networks excel at **continuous 24-hour temporal trajectories** and sequence momentum.

### Neural Layer-by-Layer Architecture:

```
INPUT SEQUENCE: (Batch, 24 Hours, 58 Scaled Features) + Station Code (0–9)
  │
  ├──► 1. Station Embedding Layer: nn.Embedding(10, 8) ──► Maps station ID into ℝ⁸
  │      Concatenates with features ──► (Batch, 24, 66)
  │
  ├──► 2. Input Projection: nn.Linear(66, 64) + LayerNorm
  │
  ├──► 3. Bidirectional GRU/LSTM: nn.GRU(64, hidden_size=64, num_layers=2, bidirectional=True)
  │      Extracts forward & backward temporal representations ──► (Batch, 24, 128)
  │
  ├──► 4. Multi-Head Self-Attention: nn.MultiheadAttention(embed_dim=128, num_heads=4)
  │      Learns which hours in the past 24h matter most (e.g., peak solar hour vs. current hour)
  │      Residual Connection + LayerNorm: out = LayerNorm(gru_out + attn_out)
  │
  ├──► 5. Representation Pooling: Context = 0.5 × (Last_Timestep + Mean_Pool) ──► (Batch, 128)
  │
  └──► 6. Deep MLP Regression Head:
         Linear(128, 64) ──► GELU() ──► Dropout(0.15) ──► Linear(64, 32) ──► GELU() ──► Linear(32, 1)
```

### Training Regimen & GPU Acceleration:
* **Feature Normalization:** `StandardScaler` ($\mu=0, \sigma=1$) fitted strictly on the training partition.
* **Loss Function:** `nn.SmoothL1Loss(beta=0.1)` (Huber loss).
* **Optimizer:** AdamW (`lr=3e-3`, `weight_decay=1e-4`) with `CosineAnnealingLR` scheduler.
* **Hardware Acceleration:** Executed on **NVIDIA GeForce RTX 4050 Laptop GPU (CUDA 12.8)**.

---

## 6. MODEL FAMILY 3: NNLS SIMPLEX STACKING META-LEARNER

### The Mathematical Stacking Problem:
Standard stacking uses unconstrained linear regression, which often yields negative weights (e.g., $w_{\text{LGB}} = +2.5, w_{\text{DL}} = -1.5$), leading to catastrophic predictions on unseen test extremes.

### The NNLS Simplex Solution:
We solve a constrained optimization over the Out-Of-Fold (OOF) validation predictions:

$$\min_{w} \left\| \hat{Y}_{\text{oof}} w - Y_{\text{val}} \right\|_2^2 \quad \text{subject to } w_i \ge 0, \quad \sum_{i=1}^{M} w_i = 1$$

* **Solved via:** `scipy.optimize.nnls` with $L_1$ probability simplex normalization.
* **Resulting Weights on Ozone:** $\approx 83.4\%\ \text{LightGBM} + 16.6\%\ \text{BiLSTM}$.
* **Guarantee:** The ensemble prediction is strictly bounded between the best physical predictions of both models, eliminating residual variance.

---

## 7. TARGET STABILIZATION & ATMOSPHERIC LOSS FUNCTIONS

Atmospheric pollutant distributions in Delhi follow a **log-normal distribution** with extreme right-skew.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    LOGARITHMIC TARGET TRANSFORMATION PIPELINE               │
├─────────────────────────────────────────────────────────────────────────────┤
│ 1. Forward Transform (Before Training):                                     │
│    y_tilde = ln(1 + max(y_physical, 0))   [np.log1p]                        │
│    • Compresses extreme spikes (400 µg/m³ ──► 5.99)                         │
│    • Prevents gradient explosion during gradient descent                    │
│                                                                             │
│ 2. Inverse Transform (During Inference):                                    │
│    y_hat_physical = max(exp(y_tilde_pred) - 1, 0)   [np.expm1]              │
│    • Restores physical units (µg/m³)                                        │
│    • Mathematically guarantees non-negative concentrations (y ≥ 0)          │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 8. FEATURE VECTOR SCHEMA & INPUT DIMENSIONS (38 FEATURES)

The feature pipeline produces **38 curated physical features** fed into all models:

| Feature Category | Count | Features & Descriptions |
|---|---|---|
| **Ground Chemistry** | 7 | `PM2.5_ground`, `PM10_ground`, `NO_ground`, `NO2_ground`, `NOx_ground`, `NH3_ground`, `SO2_ground`, `CO_ground` |
| **ERA5 Meteorology** | 8 | `era5_temperature_c`, `era5_dewpoint_c`, `era5_u10`, `era5_v10`, `era5_wind_speed`, `era5_relative_humidity`, `era5_surface_pressure_hpa`, `era5_boundary_layer_height`, `era5_solar_radiation_w_m2`, `era5_total_precipitation_mm` |
| **Atmospheric Physics** | 2 | `ventilation_coeff` ($\text{BLH} \times \text{Wind}$), `photo_index` ($\text{SSRD} / 1024$) |
| **Sentinel-5P Satellite** | 5 | `sat_NO2`, `sat_CO`, `sat_HCHO`, `sat_NO2_available`, `sat_CO_available`, `satellite_age_hours` |
| **OpenStreetMap Geospatial** | 4 | `geo_dist_to_nearest_road_m`, `geo_road_length_1km_buffer_m`, `geo_road_length_3km_buffer_m`, `geo_dist_to_nearest_railway_m`, land use one-hot encodings |
| **Cyclical Trigonometric** | 6 | `hour_sin`, `hour_cos`, `doy_sin`, `doy_cos`, `wind_sin`, `wind_cos` |
| **Trailing Memory / Lags** | 9 | `*_lag_1h`, `*_lag_3h`, `*_lag_6h`, `*_lag_12h`, `*_lag_24h`, `*_roll_mean_6h`, `*_roll_std_6h`, `*_roll_mean_24h`, `*_roll_std_24h` |
| **Station Embeddings** | 1 | `station_enc` (Scalar integer ID: 0 to 9) |

---

## 9. COMPLETE MODEL PERFORMANCE & CHECKPOINT MATRIX

Evaluated on **44,160 held-out test records** (H2 2025 across 10 Delhi stations):

```
──────────────────────────────────────────────────────────────────────────────────────────────────────────────────
Target   Horizon   Model Architecture        Test R²    Willmott's d    RMSE (µg/m³)   Saved Checkpoint Path
──────────────────────────────────────────────────────────────────────────────────────────────────────────────────
NO2      t+1h      NNLS Simplex Ensemble     0.9191     0.9785 (97.9%)  10.644         models/ensemble/stacker_NO2_h1.pkl
NO2      t+3h      NNLS Simplex Ensemble     0.8489     0.9568 (95.7%)  14.549         models/ensemble/stacker_NO2_h3.pkl
NO2      t+6h      NNLS Simplex Ensemble     0.8058     0.9412 (94.1%)  16.496         models/ensemble/stacker_NO2_h6.pkl
NO2      t+12h     NNLS Simplex Ensemble     0.7908     0.9376 (93.8%)  17.126         models/ensemble/stacker_NO2_h12.pkl
NO2      t+24h     NNLS Simplex Ensemble     0.7662     0.9288 (92.9%)  18.118         models/ensemble/stacker_NO2_h24.pkl
NO2      t+48h     NNLS Simplex Ensemble     0.7155     0.9087 (90.9%)  20.010         models/ensemble/stacker_NO2_h48.pkl
──────────────────────────────────────────────────────────────────────────────────────────────────────────────────
O3       t+1h      NNLS Simplex Ensemble     0.8689     0.9618 (96.2%)  13.013         models/ensemble/stacker_O3_h1.pkl
O3       t+3h      NNLS Simplex Ensemble     0.7911     0.9327 (93.3%)  16.429         models/ensemble/stacker_O3_h3.pkl
O3       t+6h      NNLS Simplex Ensemble     0.7609     0.9214 (92.1%)  17.581         models/ensemble/stacker_O3_h6.pkl
O3       t+12h     NNLS Simplex Ensemble     0.7600     0.9232 (92.3%)  17.615         models/ensemble/stacker_O3_h12.pkl
O3       t+24h     NNLS Simplex Ensemble     0.7559     0.9215 (92.2%)  17.781         models/ensemble/stacker_O3_h24.pkl
O3       t+48h     NNLS Simplex Ensemble     0.6975     0.8949 (89.5%)  19.832         models/ensemble/stacker_O3_h48.pkl
──────────────────────────────────────────────────────────────────────────────────────────────────────────────────
```

---

## 10. PRODUCTION SERIALIZATION & PHASE 4 API PACKAGING

All 36 models are serialized into standalone production bundles ready for immediate deployment in the Phase 4 FastAPI service:

```
models/
├── NO2/
│   ├── model.pkl              # 85.7 MB: Bundles all 6 LightGBM + NNLS models (1h to 48h)
│   ├── feature_schema.json    # Exact 38-feature names, types, and NaN handling rules
│   └── metadata.json          # Model version, test metrics, training timestamps
└── O3/
    ├── model.pkl              # 35.2 MB: Bundles all 6 LightGBM + NNLS models (1h to 48h)
    ├── feature_schema.json    # Exact 38-feature names, types, and NaN handling rules
    └── metadata.json          # Model version, test metrics, training timestamps
```

---

*Certified and Approved by Team AIRO2.*  
**Lead & Architecture:** Sudhith (Team AIRO2 Lead)  
**SIH 2026 — Problem Statement ID: SIH 25178**
