# PHASE 3 → PHASE 4
# MODEL HANDOFF & BACKEND INTEGRATION REQUIREMENTS

**Project:** SIH 25178 — Ground-Level O₃ & NO₂ Forecasting System

**Purpose:** Final engineering handoff from the completed Phase 3 ML system to the Phase 4 Backend team.

**Status:** Phase 3 model artifacts and integration contract are FROZEN for Phase 4.

---

# 1. PURPOSE

Phase 3 has completed the core machine-learning system for forecasting:

- NO₂
- O₃

The production model system contains:

- LightGBM / GBDT
- BiLSTM + Multi-Head Attention
- NNLS simplex stacking
- direct multi-horizon forecasting
- walk-forward validation
- held-out H2 2025 evaluation
- SHAP explainability
- production model bundles
- feature schema
- model metadata
- evaluation artifacts
- reproducibility reference

Phase 4 must now build the backend and database around this frozen model system.

The purpose of this document is to define exactly:

1. what Phase 4 receives from Phase 3
2. what Phase 4 is allowed to do
3. what Phase 4 must NOT change
4. how inference must work
5. how predictions must be represented
6. how the Phase 3 → Phase 4 reproducibility test must work
7. what the backend must expose to Phase 7

---

# 2. PHASE 3 STATUS

Phase 3 is considered complete for model serving purposes.

The production artifacts have been generated and validated.

The architecture report confirms:

- 36 underlying trained model artifacts
- 12 LightGBM models
- 12 BiLSTM + Attention models
- 12 NNLS stackers
- 2 production model bundles
- NO₂ production bundle
- O₃ production bundle
- feature schema
- model metadata
- training/evaluation pipeline
- leakage audit
- explainability artifacts

The two production bundles are the artifacts that Phase 4 should consume.

Do NOT make the backend reconstruct the ensemble from the individual training artifacts unless specifically required.

The production serving interface is the bundled model interface.

---

# 3. PRODUCTION MODEL ARCHITECTURE

The production architecture is:

                        58 INPUT FEATURES
                               │
                               ▼
                    ┌────────────────────┐
                    │                    │
                    │    LightGBM GBDT   │
                    │                    │
                    └─────────┬──────────┘
                              │
                              │
                    ┌─────────▼──────────┐
                    │                    │
                    │ BiLSTM + Attention │
                    │                    │
                    └─────────┬──────────┘
                              │
                              ▼
                    ┌────────────────────┐
                    │                    │
                    │ NNLS Simplex       │
                    │ Stacking           │
                    │                    │
                    └─────────┬──────────┘
                              │
                              ▼
                    FINAL PREDICTION

The production system uses the two model families together.

The NNLS stacker combines their predictions using non-negative weights whose sum is 1.

The architecture report confirms the BiLSTM branch uses:

- 24-hour sequence window
- station embedding
- 4-head self-attention
- SmoothL1 loss

The LightGBM branch uses:

- 127 leaves
- L1 loss
- 2500 trees

The final production output is produced by the ensemble.

---

# 4. IMPORTANT: DIRECT MULTI-HORIZON FORECASTING

The system does NOT recursively predict:

    +1h
      ↓
    +2h
      ↓
    +3h
      ↓
    ...

Instead, the model uses direct forecasting.

The production horizons are:

    +1h
    +3h
    +6h
    +12h
    +24h
    +48h

Each horizon is directly predicted.

This is deliberate.

The model does NOT feed a previous prediction back into the next prediction.

Therefore:

DO NOT implement recursive forecasting in Phase 4.

DO NOT call the +1h prediction and feed it back into the model to create +2h.

DO NOT create synthetic intermediate horizons.

---

# 5. AUTHORITATIVE FORECAST CONTRACT

The backend must expose exactly these six horizons:

```text
1h
3h
6h
12h
24h
48h
```

for:

```text
NO₂
O₃
```

Therefore the full forecast matrix is:

```text
NO₂:
1h
3h
6h
12h
24h
48h

O₃:
1h
3h
6h
12h
24h
48h
```

---

# 6. IMPORTANT — THIS IS NOT 48 HOURLY PREDICTIONS

The model provides six discrete forecast checkpoints.

It does NOT provide:

```text
1h
2h
3h
4h
...
48h
```

The backend must not generate those missing values.

DO NOT:

- interpolate
- smooth
- resample
- duplicate
- forward-fill
- create artificial hourly predictions

The Phase 7 frontend has already been aligned with the six-horizon contract.

The dashboard should therefore visualize:

```text
1h → 3h → 6h → 12h → 24h → 48h
```

as six actual model outputs.

---

# 7. PRODUCTION MODEL ARTIFACTS

The canonical production model location is:

```text
models/
```

The production bundles are:

```text
models/NO2/model.pkl
models/O3/model.pkl
```

These are the authoritative serving artifacts.

The previous nested:

```text
PHASE_2_3_SUDHITH/2_MODELS/
```

location is no longer the production source of truth.

Do not create another copy.

Do not point the backend back to the old nested directory.

---

# 8. MODEL BUNDLE INTERFACE

The production model bundles expose the model inference interface.

The backend should treat them as production inference objects.

Conceptually:

```python
model = load_model(...)

prediction = model.predict(features)
```

The backend should NOT import:

- training notebooks
- training scripts
- cross-validation code
- hyperparameter search
- EDA code
- SHAP generation code

into the production inference path.

---

# 9. TWO PRODUCTION SERVING MODELS

The backend should understand the production system as two pollutant-specific bundles:

```text
NO₂ model bundle
    ├── 1h
    ├── 3h
    ├── 6h
    ├── 12h
    ├── 24h
    └── 48h

O₃ model bundle
    ├── 1h
    ├── 3h
    ├── 6h
    ├── 12h
    ├── 24h
    └── 48h
```

Do not make the API dependent on the internal 36-file training artifact structure.

The backend should interact with the production bundle.

---

# 10. FEATURE COUNT — 58

The authoritative production feature count is:

```text
58
```

This is confirmed by the actual production:

```text
feature_schema.json
```

The old "38 features" documentation is obsolete.

Phase 4 must use:

```text
feature_schema.json
```

as the source of truth.

Never use a hard-coded list copied from old documentation.

---

# 11. FEATURE BREAKDOWN

The 58 features consist of:

| Feature group | Count |
|---|---:|
| CPCB ground chemistry | 7 |
| ERA5 meteorology | 10 |
| Physics-derived features | 2 |
| Sentinel-5P satellite features | 6 |
| OSM geospatial features | 4 |
| Land-use one-hot features | 4 |
| Station identity | 1 |
| Cyclical time features | 6 |
| NO₂ lag/rolling features | 9 |
| O₃ lag/rolling features | 9 |
| **Total** | **58** |

The actual production schema remains authoritative over this summary.

---

# 12. FEATURE SCHEMA VALIDATION

Before inference, Phase 4 must validate:

- feature count
- feature names
- feature order
- data types
- missing values

Expected:

```text
58 features
```

If the feature vector does not match the production schema:

```text
DO NOT RUN INFERENCE
```

Return an appropriate error.

Do not silently:

- drop features
- add features
- reorder features
- rename features
- substitute values

---

# 13. FEATURE ORDER

Feature order is part of the model contract.

The backend must load the authoritative:

```text
feature_schema.json
```

and construct the model input according to that schema.

Do not rely on:

```python
dict.keys()
```

or arbitrary dataframe column ordering.

Do not manually maintain a second independent feature-order list.

---

# 14. FEATURE SOURCES

The production model consumes features derived from:

### CPCB

Ground-level chemistry including:

```text
PM2.5
PM10
NO
NOx
NH3
SO₂
CO
```

### ERA5

Meteorological information including:

```text
temperature
dew point
u10
v10
wind speed
relative humidity
pressure
boundary-layer height
solar radiation
precipitation
```

### Physics-derived

```text
ventilation_coeff
photo_index
```

### Sentinel-5P

Satellite-derived features including:

```text
NO₂ column
CO column
HCHO column
availability indicators
satellite age
```

### OSM

Geospatial information including:

```text
nearest road distance
nearest railway distance
road-length buffers
```

### Land-use

One-hot features:

```text
commercial
grass
park
residential
```

### Station

```text
station_enc
```

### Time

Cyclical temporal features.

### Historical pollutant features

Lag and rolling features for:

```text
NO₂
O₃
```

---

# 15. PHASE 4 MUST NOT REIMPLEMENT PHASE 2

Phase 4 is NOT responsible for:

- downloading Sentinel-5P
- processing Sentinel-5P pixels
- spatially matching satellite observations
- performing satellite quality filtering
- calculating OSM buffers
- calculating land-use features
- rebuilding the Phase 2 fusion pipeline

Those operations belong to Phase 2.

Phase 4 must consume the approved Phase 2 / Phase 3 feature pipeline.

---

# 16. PREPROCESSING CONTRACT

The Phase 3 architecture uses preprocessing and target transformation.

The backend must preserve the exact preprocessing behavior used during training.

The architecture report confirms the target transformation:

```text
training:
log1p(target)

inference:
expm1(prediction)
```

with the resulting physical concentration clipped at zero.

Do not implement a different target transformation.

Do not apply another logarithm.

Do not apply another exponential transformation.

Do not modify the output after the production model's inverse transformation.

---

# 17. MODEL UNITS — FINAL DECISION

The authoritative model output unit is:

```text
NO₂ → µg/m³
O₃  → µg/m³
```

This is the final project decision.

There is NO:

```text
µg/m³ → ppb
```

conversion in Phase 4.

The backend must preserve the model's native units.

The frontend has already been updated to consume:

```text
µg/m³
```

Therefore:

```text
Phase 3
    ↓
µg/m³
    ↓
Phase 4
    ↓
µg/m³
    ↓
Phase 7
    ↓
µg/m³
```

Do not introduce a conversion layer.

Do not modify model outputs to satisfy an obsolete frontend contract.

---

# 18. MODEL OUTPUT VALIDATION

Every prediction returned by the model must be validated for:

- finite numeric value
- non-negative value
- correct pollutant
- correct horizon
- correct unit

If the production model guarantees non-negative output through its inverse transform, the backend should still validate the final value.

Do not silently replace invalid predictions with zero.

If an invalid model output occurs:

```text
log the error
mark forecast unavailable
return appropriate API status
```

---

# 19. STATION COVERAGE

The model covers the 10 approved stations.

Canonical IDs:

```text
ANAND_VIHAR
ITO
OKHLA_PHASE_2
AYA_NAGAR
RK_PURAM
DHYAN_CHAND_STADIUM
MANDIR_MARG
PUNJABI_BAGH
JAHANGIRPURI
DWARKA_SECTOR_8
```

Do not introduce aliases.

The station encoding used by the model must map consistently to these IDs.

---

# 20. STATION ENCODING

The BiLSTM branch uses a learned station embedding.

The architecture report confirms:

```text
10 stations
embedding dimension = 8
```

Therefore the backend must use the exact station encoding expected by the production model.

Do NOT alphabetically reassign station IDs.

Do NOT create a new encoding.

Do NOT assume the database primary key equals the model's encoded station index.

Create an explicit mapping if required.

---

# 21. MODEL VERSION

Every production prediction must be traceable to:

```text
model version
feature schema version
```

Where available, also retain:

```text
training data version
```

Do not silently replace the production model.

If a future model is introduced:

```text
v1 → v2
```

the backend must be able to identify which version generated each forecast.

---

# 22. MODEL METADATA

The backend should load the actual Phase 3 metadata.

At minimum expose:

```text
model name
model version
pollutants
horizons
feature count
feature schema version
native units
```

Where available also expose:

```text
training period
validation period
test period
framework
training data version
```

Do not invent metadata.

---

# 23. ACTUAL REPORTED PERFORMANCE

The Phase 3 report provides held-out H2 2025 evaluation.

These metrics are reported by the model team's evaluation pipeline.

### NO₂

| Horizon | R² | RMSE µg/m³ |
|---|---:|---:|
| 1h | 0.9191 | 10.64 |
| 3h | 0.8489 | 14.55 |
| 6h | 0.8058 | 16.50 |
| 12h | 0.7908 | 17.13 |
| 24h | 0.7662 | 18.12 |
| 48h | 0.7155 | 20.01 |

### O₃

| Horizon | R² | RMSE µg/m³ |
|---|---:|---:|
| 1h | 0.8689 | 13.01 |
| 3h | 0.7911 | 16.43 |
| 6h | 0.7609 | 17.58 |
| 12h | 0.7600 | 17.62 |
| 24h | 0.7559 | 17.78 |
| 48h | 0.6975 | 19.83 |

These are model-team reported metrics.

Phase 4 must NOT recalculate or alter them.

Do not present them as independently reproduced unless they have actually been independently reproduced.

---

# 24. MODEL PERFORMANCE API

If the backend exposes model performance, preserve the dimensions:

```text
pollutant
horizon
metric
evaluation dataset
```

Do not collapse the metrics into one overall accuracy number.

For example:

```text
NO₂ 1h R² = 0.9191
```

must never be represented as:

```text
NO₂ model accuracy = 91.91%
```

R² is not an "accuracy percentage."

---

# 25. MODEL LIMITATIONS

The backend/dashboard may expose model performance information.

However, the following must remain clear:

```text
48h predictions have lower reported performance than short horizons.
```

The degradation with horizon is visible in the reported evaluation results.

Do not hide this from the model-information layer.

Do not claim the 48h forecast is equally accurate to the 1h forecast.

---

# 26. SHAP / MODEL DRIVERS

Phase 3 contains SHAP explainability artifacts.

If machine-readable SHAP information is available, Phase 4 may expose it.

Use terminology such as:

```text
Model Drivers
Features Contributing to Prediction
```

Do NOT use:

```text
Cause
Root Cause
Pollution Cause
```

unless a causal methodology exists.

SHAP importance is not causal proof.

---

# 27. UNCERTAINTY

Do not invent uncertainty.

Do not generate:

```text
confidence = 92%
```

unless Phase 3 actually provides a validated confidence methodology.

Do not create:

```text
prediction ± 10%
```

without scientific justification.

If Phase 3 has no validated prediction interval:

```text
No uncertainty field should be fabricated.
```

---

# 28. GOLDEN INFERENCE REFERENCE

Phase 3 must provide a frozen reference case for Phase 4.

Required structure:

```text
integration_test/
└── GOLDEN_001/
    ├── input.json
    ├── expected_output.json
    └── README.md
```

The golden reference must contain a real production inference.

It must NOT contain manually invented values.

---

# 29. GOLDEN INPUT

The input must identify:

```text
test_id
station_id
forecast_generated_at
model_version
feature_schema_version
exact feature vector
```

The feature vector must contain the actual production 58-feature input.

Example:

```json
{
  "test_id": "GOLDEN_001",
  "station_id": "ANAND_VIHAR",
  "forecast_generated_at": "2026-08-25T10:00:00+05:30",
  "model_version": "v1.0.0",
  "feature_schema_version": "v1.0",
  "features": {
    "...": "actual production values"
  }
}
```

---

# 30. GOLDEN OUTPUT

The expected output must be generated by the actual production model.

It must contain:

```text
NO₂
  +1h
  +3h
  +6h
  +12h
  +24h
  +48h

O₃
  +1h
  +3h
  +6h
  +12h
  +24h
  +48h
```

Each output must contain:

```text
pollutant
horizon_hours
target_timestamp
prediction
unit
model_version
```

---

# 31. GOLDEN TEST PURPOSE

The Golden Test is NOT a model accuracy test.

It verifies:

```text
Phase 3 model
        ↓
correctly integrated
        ↓
Phase 4
```

It detects problems such as:

- wrong model artifact
- wrong model version
- wrong feature order
- wrong feature count
- wrong preprocessing
- wrong station encoding
- wrong missing-value behavior
- wrong timestamp handling
- wrong target transformation
- wrong output mapping

---

# 32. PHASE 4 REPRODUCIBILITY TEST

Once Phase 4 is implemented:

```text
GOLDEN_001/input.json
        ↓
Phase 4 inference service
        ↓
Phase 4 API output
```

must be compared against:

```text
GOLDEN_001/expected_output.json
```

Expected:

```text
Phase 3 output ≈ Phase 4 output
```

within the documented numerical tolerance.

---

# 33. IMPORTANT — PHASE 4 OWNS THIS TEST

Phase 3 has completed its responsibility when:

```text
golden input exists
golden output exists
environment is documented
reproduction instructions exist
tolerance is defined
```

Phase 4 is responsible for:

```text
loading the artifacts
running the golden input
calling the API
comparing outputs
investigating differences
```

Do not require Phase 3 to test an API that does not exist yet.

---

# 34. FORECAST API CONTRACT

Recommended endpoint:

```text
GET /api/v1/stations/{station_id}/forecast
```

The response should contain:

```json
{
  "station_id": "ANAND_VIHAR",
  "generated_at": "...",
  "model": {
    "name": "...",
    "version": "...",
    "feature_schema_version": "...",
    "feature_count": 58
  },
  "forecasts": {
    "NO2": [
      {
        "horizon_hours": 1,
        "target_timestamp": "...",
        "prediction": 82.4,
        "unit": "µg/m³"
      }
    ],
    "O3": []
  }
}
```

The exact schema may be adapted to the backend framework.

The scientific meaning must remain unchanged.

---

# 35. CURRENT VS PREDICTED DATA

The backend must maintain a strict distinction between:

```text
OBSERVED
```

and:

```text
PREDICTED
```

Observed values originate from sources such as CPCB.

Predicted values originate from the Phase 3 model.

Never write predictions into an observation record.

Never represent a prediction as a CPCB observation.

---

# 36. FORECAST TIMESTAMPS

Every prediction must contain:

```text
forecast_generated_at
target_timestamp
```

For example:

```text
generated:
2026-08-25 10:00

+1h:
2026-08-25 11:00

+3h:
2026-08-25 13:00

+6h:
2026-08-25 16:00

+12h:
2026-08-25 22:00

+24h:
2026-08-26 10:00

+48h:
2026-08-27 10:00
```

Use timezone-aware timestamps.

---

# 37. DATABASE FORECAST RECORD

If forecasts are persisted, each forecast record should retain:

```text
station_id
forecast_generated_at
target_timestamp
pollutant
horizon_hours
prediction
unit
model_version
feature_schema_version
```

This makes every prediction traceable.

---

# 38. MODEL SERVICE

Phase 4 should create a dedicated model-serving abstraction.

Conceptually:

```text
ModelService
     ↓
ModelLoader
     ↓
NO₂ production bundle
O₃ production bundle
```

The API layer should not directly load `.pkl` files.

---

# 39. MODEL LOADING

Models should be loaded once during application startup or through a controlled lazy-loading mechanism.

Do NOT load the 82 MB NO₂ bundle and 34 MB O₃ bundle on every API request.

The backend should maintain the loaded production models in memory where appropriate.

---

# 40. MODEL HEALTH

The health system should verify:

```text
API process
database
NO₂ model
O₃ model
```

Example:

```json
{
  "status": "ok",
  "database": "ok",
  "models": {
    "NO2": "loaded",
    "O3": "loaded"
  }
}
```

If the models cannot load:

```text
ready = false
```

or an equivalent degraded state.

Do not report full readiness when model inference is unavailable.

---

# 41. MODEL CACHE / FORECAST CACHE

The backend may cache generated forecasts.

The purpose is:

```text
avoid unnecessary repeated inference
```

Do NOT cache forever.

Forecast freshness must be documented.

The cache policy should be based on the actual data refresh strategy.

Do not invent a scientific forecast refresh interval.

---

# 42. DATABASE REQUIREMENTS

At minimum the backend database should support:

```text
stations
observations
forecasts
model_versions
```

Optional:

```text
forecast_runs
ingestion_runs
```

only if useful.

---

# 43. STATION DATABASE

The station database should contain the canonical:

```text
station_id
name
latitude
longitude
active
```

plus any approved metadata.

Do not duplicate station coordinates across frontend, backend and model configuration.

Maintain one canonical station registry.

---

# 44. OBSERVATION DATABASE

The observation layer should support:

```text
timestamp
station_id
NO₂
O₃
CO
NO
NOx
SO₂
PM2.5
PM10
```

and other approved source fields.

Do not invent values for unavailable fields.

---

# 45. DATA PROVENANCE

Where possible retain:

```text
source
source_file
source_timestamp
ingestion_timestamp
quality/status
```

This is important for debugging and Phase 6 validation.

---

# 46. FORECAST INSIGHTS

Phase 4 may derive deterministic summaries from the six model outputs.

Examples:

```text
current value
predicted peak
peak horizon
peak timestamp
minimum
minimum horizon
trend
change from current
```

These are backend calculations.

They are NOT new ML predictions.

---

# 47. TREND CLASSIFICATION

If the backend provides:

```text
RISING
FALLING
STABLE
```

the rule must be documented.

Do not invent scientifically meaningful thresholds.

If the classification is only for visualization, label it as a dashboard/business rule.

---

# 48. NO FABRICATED AQI / RISK LOGIC

Do not copy arbitrary thresholds from frontend mock data.

If AQI or pollutant severity is required:

1. identify the approved methodology
2. document the source
3. implement it centrally
4. test it

Do not use arbitrary formulas simply to make the dashboard visually interesting.

---

# 49. API VERSIONING

Use:

```text
/api/v1/
```

for production API endpoints.

Recommended:

```text
GET /api/v1/stations
GET /api/v1/stations/current
GET /api/v1/stations/{id}
GET /api/v1/stations/{id}/current
GET /api/v1/stations/{id}/history
GET /api/v1/stations/{id}/forecast
GET /api/v1/model
GET /health
```

---

# 50. FRONTEND CONTRACT

The Phase 7 frontend has already been updated to match the model contract.

Therefore the backend should provide:

```text
NO₂ → µg/m³
O₃  → µg/m³
```

and:

```text
1h
3h
6h
12h
24h
48h
```

Do not reintroduce:

```text
ppb
```

or:

```text
1h ... 48h hourly points
```

---

# 51. PHASE 4 DOES NOT CHANGE PHASE 3

Phase 4 must NOT:

- retrain models
- modify model architecture
- change hyperparameters
- change feature engineering
- change target construction
- change model units
- change forecast horizons
- change station encoding
- change preprocessing
- modify the production artifacts

If Phase 4 discovers a model integration problem:

```text
STOP
DOCUMENT
REPORT
```

Do not silently patch the model.

---

# 52. TESTING REQUIREMENTS

Phase 4 must implement:

## Unit tests

Test:

```text
feature validation
station mapping
forecast transformation
timestamp generation
insight calculations
error handling
```

## Integration tests

Test:

```text
database → API
model → service
service → API
forecast → database
```

## Golden compatibility test

Test:

```text
Phase 3 Golden Reference
            vs
Phase 4 inference
```

---

# 53. GOLDEN COMPATIBILITY TEST

Create:

```text
tests/
└── test_phase3_phase4_compatibility.py
```

The test must:

1. load GOLDEN_001
2. send the same input through Phase 4
3. collect all 12 predictions
4. compare them with Phase 3
5. verify model version
6. verify horizons
7. verify units
8. verify station
9. verify timestamps

The test should fail loudly on unexplained drift.

---

# 54. REQUIRED OUTPUT COUNT

For one station and one forecast generation time:

```text
2 pollutants × 6 horizons = 12 predictions
```

Therefore a complete forecast run should contain:

```text
12 prediction points
```

not:

```text
96
```

and not:

```text
48 × 2
```

---

# 55. MODEL INFORMATION ENDPOINT

The backend should expose actual Phase 3 information.

Example:

```json
{
  "model_name": "air_quality_forecaster",
  "pollutants": ["NO2", "O3"],
  "horizons_hours": [1, 3, 6, 12, 24, 48],
  "feature_count": 58,
  "native_unit": "µg/m³",
  "architecture": [
    "LightGBM",
    "BiLSTM+Attention",
    "NNLS"
  ],
  "model_version": "..."
}
```

Use actual metadata values.

---

# 56. MODEL EXPLAINABILITY ENDPOINT

If the Phase 3 SHAP artifacts are made machine-readable, expose them through an endpoint such as:

```text
GET /api/v1/stations/{id}/forecast/explanation
```

Return:

```text
feature
importance
direction
```

where available.

Do not claim causality.

---

# 57. PERFORMANCE REQUIREMENTS

Benchmark:

```text
single-station inference
10-station inference
```

Record:

```text
average inference time
p95 inference time
memory usage
hardware
```

Do not invent latency claims.

---

# 58. PRODUCTION INFERENCE PATH

The production backend path must be:

```text
Current approved data
        ↓
Feature preparation
        ↓
58-feature validation
        ↓
Production model bundle
        ↓
NO₂ / O₃ predictions
        ↓
Forecast validation
        ↓
Database/cache
        ↓
API
        ↓
Frontend
```

The production path must NOT execute:

```text
EDA
cross-validation
training
hyperparameter search
SHAP generation
```

---

# 59. PHASE 4 ACCEPTANCE CRITERIA

Phase 4 model integration is complete only when:

```text
[ ] canonical models/ path used
[ ] NO₂ production bundle loads
[ ] O₃ production bundle loads
[ ] feature_schema.json loaded
[ ] 58 features validated
[ ] feature ordering validated
[ ] station encoding validated
[ ] preprocessing validated
[ ] target transformation preserved
[ ] units preserved as µg/m³
[ ] six horizons returned
[ ] no interpolation
[ ] no recursive forecasting
[ ] 12 predictions produced per forecast run
[ ] model version returned
[ ] feature schema version returned
[ ] timestamps correct
[ ] Golden Inference test passes
[ ] database stores forecast metadata
[ ] API returns correct forecast contract
[ ] frontend can consume real API
```

---

# 60. PHASE 3 → PHASE 4 RESPONSIBILITY BOUNDARY

## Phase 3 owns:

```text
model architecture
training
feature engineering definition
preprocessing definition
model artifacts
model evaluation
SHAP
model version
feature schema
inference reference
```

## Phase 4 owns:

```text
model loading
model serving
feature availability validation
database
forecast storage
API
caching
forecast summaries
peak/trend calculations
health monitoring
frontend data delivery
```

## Phase 7 owns:

```text
visualization
charts
maps
cards
dashboard interaction
presentation
```

---

# 61. IMPORTANT SCIENTIFIC BOUNDARY

The backend may interpret model outputs.

It must not change their scientific meaning.

VALID:

```text
NO₂ forecast peak:
103.7 µg/m³ at +24h
```

NOT VALID:

```text
NO₂ will definitely reach 103.7
```

The backend is serving a prediction, not a certainty.

---

# 62. FINAL ARCHITECTURE

```text
                    PHASE 2
              FUSED FEATURE DATA
                       │
                       ▼
              ┌─────────────────┐
              │     PHASE 3     │
              │                 │
              │ 58 features     │
              │                 │
              │ LightGBM        │
              │ BiLSTM+Attention│
              │ NNLS Stack      │
              │                 │
              │ NO₂ / O₃        │
              │ 1/3/6/12/24/48h │
              └────────┬────────┘
                       │
                 VERSIONED
               MODEL OUTPUT
                       │
                       ▼
              ┌─────────────────┐
              │     PHASE 4     │
              │                 │
              │ Model Service   │
              │ Feature Check   │
              │ Database        │
              │ Forecast Store  │
              │ API             │
              │ Insights        │
              │ Cache           │
              └────────┬────────┘
                       │
                       ▼
              ┌─────────────────┐
              │     PHASE 7     │
              │                 │
              │ Dashboard       │
              │ Map             │
              │ Forecast        │
              │ History         │
              │ Insights        │
              │ Model Drivers   │
              └─────────────────┘
```

---

# 63. FINAL KEY RULE

> **Phase 3 owns prediction. Phase 4 owns serving and deterministic interpretation. Phase 7 owns visualization.**

The backend must consume the **actual frozen Phase 3 production model**, not recreate it.

The backend must preserve:

```text
58 features
NO₂ + O₃
1h / 3h / 6h / 12h / 24h / 48h
µg/m³
```

The backend must provide a reproducible path from:

```text
Phase 3 Golden Reference
        ↓
Phase 4 inference
        ↓
Phase 4 API
        ↓
Phase 7 dashboard
```

The Phase 3 → Phase 4 handoff is considered technically successful only when:

```text
same input
    ↓
Phase 3 output
    ≈
Phase 4 output
```

within the documented tolerance.
