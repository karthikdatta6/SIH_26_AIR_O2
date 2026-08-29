# MODEL CONTRACT SPECIFICATION
## Phase 3 (ML Models) $\rightarrow$ Phase 4 (FastAPI Backend Service)

> **Document Version:** 1.0.0  
> **Last Updated:** 2026-08-22  
> **Applicable Models:** Ground-Level $\text{O}_3$ and $\text{NO}_2$ Multi-Horizon Forecasters

---

## 1. Overview & Handoff Contract

This contract defines the immutable interface between the Phase 3 ML model artifacts and the Phase 4 production FastAPI backend service. 

Phase 4 **MUST NOT** retrain or alter model architectures. It consumes the exported serialization bundles directly.

---

## 2. Directory Structure & Artifact Locations

Phase 3 exports two standalone model directories under `models/`:

```
models/
├── NO2/
│   ├── model.pkl              # Pickled bundle: multi-horizon models (1h, 3h, 6h, 12h, 24h, 48h)
│   ├── feature_schema.json    # Exact feature names, types, order, and NaN handling rules
│   └── metadata.json          # Model version, test R², RMSE, training timeframe
└── O3/
    ├── model.pkl              # Pickled bundle: multi-horizon models (1h, 3h, 6h, 12h, 24h, 48h)
    ├── feature_schema.json    # Exact feature names, types, order, and NaN handling rules
    └── metadata.json          # Model version, test R², RMSE, training timeframe
```

---

## 3. Feature Schema & Preprocessing Contract

### 3.1 Input Transformation
- **Training Transformation:** $\tilde{y} = \ln(1 + \max(y, 0))$ (`log1p`).
- **Inference Transformation:** The raw model output $\hat{y}_{\text{log}}$ must be inverted to physical units ($\mu\text{g/m}^3$) via:
  $$\hat{y}_{\text{physical}} = \max(\exp(\hat{y}_{\text{log}}) - 1, 0)$$ (`expm1` with lower bound 0).

### 3.2 Feature Ordering
The feature DataFrame or NumPy array passed to `model.predict()` must match the exact sequence and names defined in `feature_schema.json`.

---

## 4. Supported Forecast Horizons

The exported models provide direct multi-step forecasting for the following horizons:
- $t+1\text{h}$
- $t+3\text{h}$
- $t+6\text{h}$
- $t+12\text{h}$
- $t+24\text{h}$
- $t+48\text{h}$ (Headline multi-day demonstration)

---

## 5. Inference Invocation Code Example (FastAPI Backend)

```python
import pickle
import numpy as np
import pandas as pd

# Load model artifact bundle
with open("models/O3/model.pkl", "rb") as f:
    bundle = pickle.load(f)

horizon_models = bundle["horizon_models"]   # Dict mapping horizon (int) -> model bundle
feature_schema = bundle["feature_schema"]

# Predict for t+1h
h1_model = horizon_models[1]["model"]
feature_cols = horizon_models[1]["feature_cols"]

# X_input: pd.DataFrame formatted according to feature_schema
raw_log_pred = h1_model.predict(X_input[feature_cols])
physical_pred = np.expm1(np.clip(raw_log_pred, 0, None))  # Returns µg/m³
```
