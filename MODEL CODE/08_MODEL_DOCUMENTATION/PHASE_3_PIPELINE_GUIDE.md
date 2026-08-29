# SIH 25178 — Phase 3 — Feature Engineering & Model Development

## 1. PURPOSE

Phase 3 converts the Phase 2 model-ready fused dataset into a
forecasting system for short-term prediction of ground-level:

- NO₂
- O₃

Phase 3 has two major responsibilities:

1. Build scientifically valid predictive features.
2. Develop, compare and select forecasting models.

The output of Phase 3 becomes the input to Phase 4.

The overall flow is:

    PHASE 2
    MODEL-READY DATASET
           ↓
    EXPLORATORY DATA ANALYSIS
           ↓
    FEATURE ENGINEERING
           ↓
    BASELINE MODELS
           ↓
    ADVANCED MODELS
           ↓
    TIME-SERIES EVALUATION
           ↓
    MODEL SELECTION
           ↓
    EXPLAINABILITY
           ↓
    FINAL MODEL ARTIFACT
           ↓
    PHASE 4

---

## 2. CORE OBJECTIVE

The project should answer:

> Given the information available at forecast time T, how accurately
> can we predict NO₂ and O₃ for future hours?

The model must learn relationships between:

- recent pollution
- meteorology
- satellite observations
- other pollutants
- temporal patterns
- station characteristics
- approved geospatial information

The model must never use information that would not have been
available when the forecast was generated.

---

## 3. INPUT FROM PHASE 2

The primary input is:

    data/fused/station_hourly_fused.parquet

Also read:

- Phase 2 data dictionary
- Phase 2 fusion methodology
- Phase 2 quality reports
- Phase 2 leakage report
- Phase 2 configuration

Before doing any modelling:

### Verify Phase 2

- [ ] Phase 2 quality gate passed
- [ ] Dataset exists
- [ ] All 10 stations are present
- [ ] Timestamp frequency is understood
- [ ] Units are understood
- [ ] Targets are CPCB-derived
- [ ] Missingness is understood
- [ ] Phase 2 leakage audit passed

Do not modify the Phase 2 raw or fused dataset directly.

---

## 4. CURRENT PROJECT SCOPE

The approved stations are:

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

Primary targets:

    NO2_ground
    OZONE_ground

The exact target column names must be confirmed from the Phase 2
data dictionary before implementation.

---

## 5. FORECAST HORIZONS

The project forecasts ground-level NO₂ and O₃ at:

- 1 hour
- 3 hours
- 6 hours
- 12 hours
- 24 hours
- 48 hours

The project demonstration focuses on the 24–48 hour forecasting
window — this is the project's headline claim (see the root
README's objective and the Phase 7 dashboard) and must be backed
by an actual trained and validated model, not just a UI label.

The 24-hour horizon is the primary short-term benchmark.

The 48-hour horizon is the extended forecasting horizon and must
be independently trained, validated and evaluated — it is not
derived from, or assumed equivalent to, the 24-hour model.

Do NOT assume that a model that performs well at 1 hour, or even
at 24 hours, will perform equally well at 48 hours.

Report performance separately for every horizon.

### Multi-horizon modeling strategy

There are two legitimate ways to produce the 1h–48h forecasts:

**Direct multi-horizon models** — a separate model per horizon:

    Features at T
        ├──→ model_1h  → T+1
        ├──→ model_3h  → T+3
        ├──→ model_6h  → T+6
        ├──→ model_12h → T+12
        ├──→ model_24h → T+24
        └──→ model_48h → T+48

**Recursive forecasting** — each step's prediction is fed back in
as input to predict the next step, out to T+48.

Start by evaluating direct multi-horizon forecasting: it avoids
accumulating recursive prediction error across the full 48-hour
window. Still compare it against a recursive baseline rather than
assuming direct forecasting is automatically superior, and document
the comparison and the reasoning behind the final choice.

---

## 6. FIRST TASK — UNDERSTAND THE DATA

Do not start with LSTM, Transformer or XGBoost.

First perform exploratory data analysis.

Investigate:

### Target distributions

- mean
- median
- standard deviation
- minimum
- maximum
- percentiles

### Temporal behaviour

- hourly pattern
- daily pattern
- weekly pattern
- monthly pattern
- seasonal pattern

### Station behaviour

Compare all 10 stations.

Determine:

- which stations have higher NO₂
- which stations have higher O₃
- how variable each station is
- whether stations behave differently

### Missingness

Analyse:

- target missingness
- predictor missingness
- station-specific missingness
- temporal gaps

### Relationships

Investigate relationships between:

- NO₂ and O₃
- NO₂ and NO
- NO₂ and NOx
- NO₂ and PM₂.₅
- NO₂ and PM₁₀
- O₃ and solar radiation
- O₃ and temperature
- O₃ and wind
- pollutants and boundary-layer conditions
- satellite observations and ground observations

Do not treat correlation as proof of causation.

---

## 7. CREATE AN EDA REPORT

Create:

    reports/phase3_eda/

Recommended outputs:

    target_distribution.csv
    missingness.csv
    station_statistics.csv
    hourly_statistics.csv
    monthly_statistics.csv

Also create appropriate visualisations.

The EDA report should answer:

> What does the dataset actually look like before modelling?

---

## 8. FEATURE GROUPS

Candidate feature groups include:

### A. Historical pollution

Examples:

    NO2_lag_1
    NO2_lag_2
    NO2_lag_3
    NO2_lag_6
    NO2_lag_12
    NO2_lag_24

Similarly for O₃ and other useful CPCB pollutants.

Do not automatically create dozens of lags.

Test whether they add useful information.

---

### B. Rolling statistics

Examples:

    NO2_rolling_mean_3h
    NO2_rolling_mean_6h
    NO2_rolling_mean_12h
    NO2_rolling_mean_24h

Potential statistics:

- mean
- median
- minimum
- maximum
- standard deviation

IMPORTANT:

Rolling features must only use information available at the
prediction time.

Correct:

    rolling window ending at T

Incorrect:

    centered rolling window around T

---

### C. Meteorological features

Potential variables:

- temperature
- dewpoint
- relative humidity
- wind speed
- wind direction
- pressure
- boundary-layer height
- precipitation
- solar radiation

Derived features may include:

- wind components
- temperature/dewpoint difference
- hour of day
- meteorological interactions

Every derived feature must be documented.

---

### D. Satellite features

Potential:

- satellite NO₂
- satellite CO
- satellite HCHO
- satellite observation age
- satellite valid-pixel count
- satellite availability indicator

Remember:

Sentinel-5P observations are not hourly.

Do not fabricate hourly satellite values.

Respect the Phase 2 satellite methodology.

---

### E. Other CPCB pollutants

Potential predictors:

- CO
- NO
- NOx
- SO₂
- PM₂.₅
- PM₁₀

Do not assume every pollutant should be included.

Evaluate whether each feature improves the model without introducing
future information.

---

### F. Temporal features

Potential features:

- hour
- day of week
- month
- day of year
- weekend
- season

Cyclical encoding may be useful:

    sin(hour)
    cos(hour)

and:

    sin(day_of_year)
    cos(day_of_year)

Choose representations based on model type and validation results.

---

### G. Station / Spatial features

Potential:

- station ID
- latitude
- longitude
- road-related features
- railway proximity
- land-use information

Determine whether the model should:

1. train one global model for all stations
2. train one model per station
3. use a global model with station information
4. use a hybrid approach

Do not decide based only on convenience.

Compare approaches using time-aware validation.

---

## 9. FEATURE SELECTION

Do not simply use every column.

For every candidate feature ask:

1. Is it available at prediction time?
2. Is its timestamp correct?
3. Is it scientifically meaningful?
4. Is it redundant?
5. Does it improve validation performance?
6. Does it generalize across stations?
7. Does it increase inference complexity unnecessarily?

Create:

    docs/phase3/FEATURE_SELECTION.md

Document:

    Feature
    Source
    Reason for inclusion
    Availability at prediction time
    Transformation
    Unit
    Missing-data behaviour
    Final decision

---

## 10. CRITICAL — DEFINE THE FORECASTING SCENARIO

Before creating features, define exactly what:

    "forecast at time T"

means.

For example:

    Forecast issue time = 10:00
    Target = NO2 at 14:00

Then every predictor must represent information available
by 10:00.

Create:

    docs/phase3/FORECASTING_SCENARIO.md

Clearly define:

- forecast issue time
- target time
- forecast horizon
- available predictors
- unavailable future information

This document becomes the reference for all leakage tests.

---

## 11. TARGET CONSTRUCTION

For a horizon H:

    target_H(t) = pollutant(t + H)

Example:

For a 6-hour forecast:

    target_6h(t) = NO2(t + 6h)

For the 48-hour forecast — this must exist as an actual model
output, not merely as a UI label:

    target_48h(t) = pollutant(t + 48h)

The 48-hour target is constructed and trained independently from
the 24-hour target — never derived by chaining 24-hour predictions.

The target must come from the CPCB ground measurement.

Do not use:

- Sentinel-5P as target
- ERA5 as target
- interpolated target
- model-generated target

If the future target is unavailable, that training example may need
to be excluded according to the documented missing-target policy.

Never fill missing future targets with predictions.

---

## 12. TIME-SERIES SPLITTING

DO NOT use a random train/test split.

Never use:

    train_test_split(..., shuffle=True)

for the primary forecasting evaluation.

Use chronological splitting.

A recommended starting structure is:

    2023 → TRAIN
    2024 → VALIDATION
    2025 → TEST

However, the exact split must be confirmed against the actual
available Phase 2 period and documented.

The test set must remain untouched until model selection is complete.

---

## 13. WALK-FORWARD VALIDATION

Where practical, use walk-forward validation.

Example:

    Train: 2023
    Validate: early 2024

    Train: 2023 + early 2024
    Validate: later 2024

    Train: 2023 + 2024
    Test: 2025

The exact folds must be documented.

The purpose is to simulate how the model would behave in the real
world.

---

## 14. PREPROCESSING RULE

Any learned preprocessing must be fitted only on the training data.

Examples:

- StandardScaler
- MinMaxScaler
- PCA
- learned imputation
- target encoding

Correct:

    TRAIN
      ↓
    fit preprocessing
      ↓
    transform TRAIN
    transform VALIDATION
    transform TEST

Incorrect:

    fit preprocessing on TRAIN + VALIDATION + TEST

This can leak information.

---

## 15. MISSING DATA

Follow the Phase 2 missing-data policy.

Do not automatically:

    fillna(0)

Zero is a real physical value and must not be used as a generic
missing-data marker.

For every missing feature:

- determine whether the model supports NaN
- use an approved imputation method
- ensure imputation is causal where required
- document the strategy

Targets must never be fabricated.

---

## 16. BASELINE MODELS

Before advanced models, create baselines.

### Baseline 1 — Persistence

For example:

    NO2(t+1) = NO2(t)

This is extremely important.

If an advanced model cannot beat persistence, it may not be useful.

---

### Baseline 2 — Historical/Seasonal Baseline

Where appropriate, compare against a simple historical baseline.

Example:

    same hour/day historical average

The exact baseline must be documented.

---

### Baseline 3 — Linear Model

Use a simple model such as:

    Linear Regression

This establishes a basic benchmark.

---

## 17. TREE-BASED MODELS

Evaluate appropriate models such as:

- Random Forest
- Gradient Boosting
- XGBoost
- LightGBM

Do not automatically select the most complex model.

For tabular fused data, tree-based models may perform extremely well.

Compare them against the baselines.

---

## 18. DEEP LEARNING MODELS

Consider only if justified by the data and experiment results.

Potential models:

- LSTM
- GRU
- Temporal CNN
- Transformer-based architecture

Do not use deep learning merely because it sounds more advanced.

Before selecting a deep-learning model, verify:

- sufficient training samples
- appropriate sequence construction
- computational resources
- validation methodology
- inference latency
- improvement over strong tabular baselines

If an XGBoost model performs similarly or better and is easier
to deploy, that is a valid outcome.

---

## 19. MODEL SELECTION

Compare models using:

- MAE
- RMSE
- R²

Use additional metrics only when justified.

For MAPE:

DO NOT use it blindly when target values can approach zero.

Evaluate:

- overall performance
- each pollutant
- each forecast horizon
- each station

Also inspect high-pollution events.

---

## 20. STATION-LEVEL EVALUATION

Report metrics separately for:

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

A model that performs well overall may perform poorly at
individual stations.

Do not hide station-level weaknesses behind a single global metric.

---

## 21. POLLUTANT-SPECIFIC EVALUATION

Evaluate separately:

    NO2

and:

    O3

Do not assume the same model architecture or feature set must
be optimal for both pollutants.

Compare:

- best features
- best model
- MAE
- RMSE
- R²
- forecast degradation with horizon

---

## 22. FORECAST-HORIZON EVALUATION

Create a table similar to:

    Model | Pollutant | Horizon | MAE | RMSE | R²

Example:

    XGBoost | NO2 | 1h  | ...
    XGBoost | NO2 | 6h  | ...
    XGBoost | NO2 | 24h | ...
    XGBoost | NO2 | 48h | ...

Do this for O₃ as well.

The project should explicitly show how accuracy changes
as the forecast horizon increases, including the degradation from
24h to 48h — the demo's headline claim rests on this window.

---

## 23. HIGH-POLLUTION EVENT EVALUATION

Overall average error is not enough.

Evaluate model behaviour during:

- high NO₂ events
- high O₃ events
- rapid pollution increases
- rapid pollution decreases

This is important because the SIH system is intended to provide
useful warnings.

Document:

- event definition
- number of events
- prediction performance
- missed events

Do not invent arbitrary event thresholds.

Use an approved standard or a statistically justified definition.

---

## 24. ERROR ANALYSIS

For poor predictions, investigate:

- unusual weather
- missing satellite data
- station-specific behaviour
- sudden emission events
- extreme pollution
- sensor/data quality
- seasonal changes

Create:

    reports/phase3/error_analysis.md

The objective is not only:

"Which model is best?"

but:

"Where does the model fail?"

---

## 25. FEATURE IMPORTANCE

For the final model, provide appropriate explainability.

Depending on the model:

- feature importance
- permutation importance
- SHAP
- partial dependence where appropriate

The goal is to answer:

> Why did the model predict pollution to increase?

Example:

    Recent NO2 ↑
    Wind speed ↓
    Boundary-layer height ↓
    PM2.5 ↑

The explanation must come from actual model features.

Do not create narrative explanations that are not supported by the model.

---

## 26. AVOID FALSE CAUSAL CLAIMS

Feature importance does NOT automatically prove causation.

Do not write:

    "Low wind caused the pollution increase"

merely because wind has high feature importance.

Prefer:

    "Low wind speed was an important predictor associated with the
     model's higher forecast."

Scientific interpretation must remain appropriately cautious.

---

## 27. EXPERIMENT TRACKING

Every model experiment must record:

    experiment_id
    model
    pollutant
    horizon
    feature_version
    training_period
    validation_period
    parameters
    metrics
    notes

Create:

    experiments/experiment_log.csv

Do not select a model based on memory.

---

## 28. HYPERPARAMETER TUNING

Tune only after establishing strong baselines.

Use validation data.

Do NOT tune against the final test set.

For example:

    TRAIN
       ↓
    TUNING
       ↓
    VALIDATION
       ↓
    FINAL MODEL
       ↓
    TEST ONCE

Avoid extremely large hyperparameter searches unless justified.

---

## 29. FINAL MODEL SELECTION

The final model should balance:

- forecasting accuracy
- stability
- generalization
- inference speed
- memory
- interpretability
- implementation complexity

Do not select:

> "The model with the highest R²"

without considering the above factors.

The final model must be practical for Phase 4 deployment.

---

## 30. MODEL ARTIFACTS

Export:

    models/
    ├── NO2/
    │   ├── model.pkl / model.joblib
    │   ├── metadata.json
    │   └── feature_schema.json
    │
    └── O3/
        ├── model.pkl / model.joblib
        ├── metadata.json
        └── feature_schema.json

The exact format depends on the model framework.

---

## 31. MODEL METADATA

Every final model must have metadata containing:

- model name
- model version
- target
- forecast horizons
- training period
- validation period
- test period
- features
- preprocessing version
- metrics
- training date
- software/environment information

---

## 32. FEATURE SCHEMA

Create:

    feature_schema.json

It must specify:

- feature name
- data type
- unit
- expected order
- transformation
- missing-data behaviour

Phase 4 will use this schema for inference validation.

---

## 33. REPRODUCIBILITY

A new team member must be able to reproduce the final model from:

- Phase 2 dataset
- feature-generation code
- configuration
- experiment settings
- dependency versions

Document:

    python version
    package versions
    random seeds
    configuration
    training command

---

## 34. LEAKAGE AUDIT

Before declaring Phase 3 complete, perform a dedicated leakage audit.

Verify:

- no future target values
- no future predictors
- no centered rolling windows
- no future interpolation
- no test-set fitting
- no test-set tuning
- no future satellite observations
- no future meteorological observations
- no leakage through normalization
- no leakage through station statistics

Create:

    reports/phase3/leakage_report.md

A single critical leakage issue blocks Phase 3 completion.

---

## 35. MODEL ROBUSTNESS

Where practical, test:

- different stations
- different seasons
- high pollution periods
- missing satellite observations
- missing predictor conditions

The goal is to determine whether the model is robust or merely
performing well under ideal conditions.

---

## 36. MODEL LIMITATIONS

Document known limitations.

Examples:

- satellite temporal sparsity
- station coverage
- unseen extreme events
- missing predictors
- forecast degradation at longer horizons
- station-specific generalization

Do not hide poor performance.

A transparent limitation is better than an unsupported claim.

---

## 37. RECOMMENDED DIRECTORY

    phase3/
    │
    ├── data/
    │
    ├── notebooks/
    │
    ├── src/
    │   ├── eda/
    │   ├── features/
    │   ├── baselines/
    │   ├── models/
    │   ├── evaluation/
    │   └── explainability/
    │
    ├── experiments/
    │   └── experiment_log.csv
    │
    ├── models/
    │   ├── NO2/
    │   └── O3/
    │
    ├── reports/
    │   └── phase3/
    │
    ├── configs/
    │
    ├── tests/
    │
    └── README.md

---

## 38. PHASE 3 VALIDATION CHECKLIST

### Data

- [ ] Phase 2 quality gate verified
- [ ] Dataset schema verified
- [ ] Target columns verified
- [ ] Units verified
- [ ] Missingness analysed
- [ ] Station coverage verified

### EDA

- [ ] Target distributions analysed
- [ ] Temporal patterns analysed
- [ ] Station differences analysed
- [ ] Feature relationships analysed
- [ ] EDA report generated

### Features

- [ ] Forecast scenario defined
- [ ] Lag features documented
- [ ] Rolling features documented
- [ ] Meteorological features documented
- [ ] Satellite features documented
- [ ] CPCB pollutant features documented
- [ ] Temporal features documented
- [ ] Spatial features documented
- [ ] Feature selection documented

### Leakage

- [ ] No future targets
- [ ] No future predictors
- [ ] No centered rolling features
- [ ] No future interpolation
- [ ] Preprocessing fitted only on training data
- [ ] Test set untouched during tuning
- [ ] Satellite causality preserved
- [ ] Leakage report passed

### Models

- [ ] Persistence baseline
- [ ] Simple statistical baseline
- [ ] Linear baseline
- [ ] Tree-based models
- [ ] Advanced model evaluated where justified
- [ ] Models compared fairly

### Evaluation

- [ ] Chronological split
- [ ] Walk-forward validation where appropriate
- [ ] NO₂ metrics
- [ ] O₃ metrics
- [ ] 1h metrics
- [ ] 3h metrics
- [ ] 6h metrics
- [ ] 12h metrics
- [ ] 24h metrics
- [ ] 48h metrics
- [ ] Station-level metrics
- [ ] High-pollution evaluation
- [ ] Error analysis

### Final model

- [ ] Final model selected
- [ ] Selection justified
- [ ] Model artifact exported
- [ ] Feature schema exported
- [ ] Metadata exported
- [ ] Explainability generated
- [ ] Reproducibility verified

---

## 39. DEFINITION OF DONE

Phase 3 is complete only when:

    PHASE 2 DATA
          ↓
    EDA COMPLETE
          ↓
    FORECASTING SCENARIO DEFINED
          ↓
    FEATURES ENGINEERED
          ↓
    LEAKAGE CHECK PASSED
          ↓
    BASELINES ESTABLISHED
          ↓
    ADVANCED MODELS COMPARED
          ↓
    TIME-SERIES VALIDATION COMPLETE
          ↓
    FINAL MODEL SELECTED
          ↓
    EXPLAINABILITY COMPLETE
          ↓
    MODEL ARTIFACT EXPORTED
          ↓
    FEATURE SCHEMA EXPORTED
          ↓
    PHASE 4 HANDOFF

Do NOT mark Phase 3 complete simply because a model trained successfully.

---

## 40. PHASE 3 QUALITY GATE

The following are blocking requirements:

- [ ] No data leakage
- [ ] Chronological validation used
- [ ] Test set not used for model selection
- [ ] Targets remain CPCB-derived
- [ ] Feature generation is reproducible
- [ ] Baselines established
- [ ] Final model beats or meaningfully justifies its position against baselines
- [ ] NO₂ evaluated
- [ ] O₃ evaluated
- [ ] 24-hour forecasting evaluated
- [ ] 48-hour forecasting evaluated independently (not assumed from 24h)
- [ ] Station-level performance reported
- [ ] Model limitations documented
- [ ] Model artifact reproducible
- [ ] Feature schema complete
- [ ] Phase 4 inference requirements documented

If any critical item fails:

    PHASE 3 = NOT READY

---

## 41. HANDOFF TO PHASE 4

Phase 3 must provide:

    MODEL
    +
    PREPROCESSING PIPELINE
    +
    FEATURE SCHEMA
    +
    MODEL METADATA
    +
    EVALUATION METRICS
    +
    INFERENCE CODE
    +
    MODEL VERSION

Specifically provide:

### 1. Model artifact

The exact trained model.

### 2. Feature pipeline

The exact transformations required before inference.

### 3. Feature schema

Names, types, units and order.

### 4. Model contract

What input the model expects and what output it produces.

### 5. Metrics

Performance by:

- pollutant
- horizon
- station

### 6. Explainability

Feature importance / SHAP or equivalent.

### 7. Limitations

Known conditions where performance degrades.

---

## 42. PHASE 4 MUST BE ABLE TO DO THIS

Phase 4 should be able to take:

    station
    +
    latest valid features
    +
    forecast issue time

and produce:

    predicted NO2
    predicted O3
    forecast timestamps
    model version

without modifying the Phase 3 model.

---

## 43. FINAL PRINCIPLE

Phase 3 has one responsibility:

> TURN TRUSTWORTHY DATA INTO A TRUSTWORTHY FORECASTING MODEL.

The complete process is:

    PHASE 2
    TRUSTWORTHY DATA
         ↓
    PHASE 3
    FEATURE ENGINEERING
         ↓
    BASELINES
         ↓
    MACHINE LEARNING
         ↓
    TIME-SERIES VALIDATION
         ↓
    MODEL SELECTION
         ↓
    EXPLAINABILITY
         ↓
    MODEL ARTIFACT
         ↓
    PHASE 4
    FORECAST API

The goal is NOT:

    "Build the most complicated model."

The goal is:

    ACCURATE
    +
    LEAKAGE-FREE
    +
    GENERALIZABLE
    +
    EXPLAINABLE
    +
    DEPLOYABLE

Only after these conditions are satisfied should Phase 3 be
handed to Phase 4.
