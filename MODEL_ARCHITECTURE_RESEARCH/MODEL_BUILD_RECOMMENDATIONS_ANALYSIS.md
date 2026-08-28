# Phase 3 — Recommendations to Build the Best Model
## SIH 25178 — Consolidated Review of ML Researcher Handout + Sudhith's Implementation Plan

> Source documents reviewed: `PHASE_3_ML_RESEARCHER_HANDOUT.md`, `PHASE_3_SUDHITH_IMPLEMENTATION_PLAN.md`
> Purpose: fix the gaps in the current plan and give a concrete, ordered build sequence.

---

## 0. Verdict

The existing plan is methodologically strong (correct temporal splitting, walk-forward CV, physically motivated features, honest uncertainty section). It is **not** broken, but it has specific gaps that will silently produce wrong or inflated numbers if not fixed first. Fix Section 1 items before writing any training code.

---

## 1. Critical fixes (do these before running any script)

### 1.1 Row-count arithmetic error
Train split (`timestamp_utc < 2025-01-01`) spans 2023 + 2024. 2024 is a leap year, so that's **731 days = 17,544 h/station = 175,440 rows**, not the documented 175,200 (730 days). Verify: 175,440 + 43,440 + 44,160 = 263,040 (matches total exactly); the documented figures sum to 262,800 (240 rows short). Fix the numbers in both docs before they go in front of evaluators.

### 1.2 Purge gap must scale with the longest lag feature
The CV scheme uses a fixed 24h purge gap, but the escalation plan (Scenario B) proposes adding 48h/72h lag features. If those are added, a fixed 24h gap lets a 48h/72h lag reach across the boundary and leak validation-period signal into training.
**Fix:** `purge_gap_hours = max(lag_windows_used)`, recomputed whenever the feature set changes.

### 1.3 No leakage test for engineered lag/rolling target features
The handout's 5 leakage tests only cover satellite causality. Nothing verifies:
- rolling windows are **trailing** (`shift(1)` then `.rolling()`), not centered
- lags/rolls are computed **within each `station_id` group**, not across station boundaries
**Fix:** add a 6th automated test, e.g. `LAG_FEATURE_CAUSALITY_CHECK` — assert that for every row, no lag/rolling feature value could have been computed from data at or after that row's timestamp, per station.

### 1.4 Missing-value cascade through lag features has no stated policy
`OZONE_ground`/`NO2_ground` are 7.8–10.2% missing → `*_lag_1h/3h/6h/12h/24h` inherit and compound that missingness. Pick and document one policy:
- **GBDT path:** leave as native `NaN` (LightGBM handles it) — do not impute.
- **NN path:** learnable missingness mask/embedding, as already described for raw predictors — apply the *same* rule to lag/rolling features, not just raw sensor columns.
- **Never** silently forward-fill lag features without a documented max fill horizon — it manufactures false persistence signal.

### 1.5 Don't ship the handout's quickstart `np.nan_to_num(x, 0.0)`
That snippet is explicitly a "quick test" in the handout. Zero-filling temperature/BLH/pollutant values is physically wrong (0 is a real, meaningful value for these fields, not "missing"). Production training code must use the masked-embedding approach the plan itself recommends elsewhere.

### 1.6 Ridge stacker as specified isn't plain `sklearn.Ridge`
"Non-negative weights summing to 1" is a simplex-constrained regression, not vanilla L2 Ridge. Implement with `scipy.optimize.nnls` + renormalization, or a small QP/`cvxpy` solve. Flag this explicitly in `06_ensemble_stacking.py` so it isn't silently swapped for plain Ridge (which would allow negative/unbounded weights).

### 1.7 Always report R² against a persistence baseline
At t+1h, autocorrelation alone (ρ≈0.90+) can produce R²≈0.90+ without real model skill. Promote the persistence-baseline check (currently only in the failure-diagnosis tree) to a **standard column in every results table**: report `R²_model`, `R²_persistence`, and `ΔR² = R²_model − R²_persistence` for every horizon/pollutant/station. This is what makes the eventual 0.95 number credible to evaluators instead of looking gamed.

---

## 2. Feature engineering checklist

- Compute all lags/rolling stats **after** `groupby("station_id")`, sorted by `timestamp_utc` — never across station boundaries.
- Use trailing windows only (`df.groupby('station_id')[col].shift(1).rolling(w).mean()`); never `center=True`.
- Drop `era5_temperature_k` / `era5_dewpoint_k` (redundant with Celsius) — plan already does this correctly.
- Confirm `NOx_ground` is in ppb while co-located precursors are in µg/m³ — do not mix units silently in any derived ratio feature (e.g. HCHO/NO2 regime ratio uses `sat_HCHO`/`sat_NO2`, both mol/m², which is fine — but audit every other engineered ratio for unit consistency).
- Cyclical encodings (`hour_sin/cos`, `doy_sin/cos`) — correct approach, keep.
- One-hot `geo_dominant_landuse_1km` — fine; alternatively pass as a native categorical to LightGBM/CatBoost instead of one-hot, which trees handle more efficiently.
- Add binary satellite-availability flags (`sat_NO2_available`, `sat_CO_available`) as already planned — these matter more during monsoon months (Jul–Sep) when missingness spikes.

---

## 3. Recommended build sequence (risk-managed, not all-at-once)

Building LightGBM + TFT + BiLSTM+Attention + stacking + SHAP in parallel is a lot of engineering surface for a hackathon-paced phase. Sequence it so there is always a complete, evaluated deliverable:

1. **Stage A — Baseline (must-have):** Persistence baseline + LightGBM, one model per horizon, both pollutants, all 10 stations. Full eval report (RMSE/MAE/R²/sMAPE/Willmott's d) vs. persistence. This alone is a defensible, demoable Phase 3 result.
2. **Stage B — Diagnostics:** Blocked walk-forward CV (with scaled purge gap, §1.2) to confirm fold stability (std of R² < 0.03) before investing in deep models.
3. **Stage C — Stretch models (only if time remains):** TFT, then BiLSTM+Attention. Both are optional upgrades, not blockers for a working submission.
4. **Stage D — Stacking:** Ridge/NNLS meta-learner over Stage A + C out-of-fold predictions, only once at least two base models exist.
5. **Stage E — Interpretability:** SHAP attribution + forecast visualizations, generated from whichever model is the final champion.

If time runs out, Stage A + B alone is a complete, scientifically sound, defensible submission. Don't let C/D block that.

---

## 4. Evaluation reporting template

For every (pollutant, horizon, station) combination, report:

| Horizon | Pollutant | Model R² | Persistence R² | ΔR² | RMSE | MAE | sMAPE | Willmott d |
|---|---|---|---|---|---|---|---|---|

Plus:
- CV fold stability: mean ± std of R² across the 5 walk-forward folds.
- Breakdown by season / episodic window (Diwali, stubble-burning Oct 15–Nov 20) since the plan itself flags these as high-uncertainty periods — show them, don't hide them.
- Train vs. test R² gap per model (overfitting check, Scenario D in the original plan).

---

## 5. Summary checklist before training starts

- [ ] Fix row-count arithmetic in both docs (§1.1)
- [ ] Make purge gap a function of max lag window, not a hardcoded 24h (§1.2)
- [ ] Add lag/rolling-feature causality test to the leakage suite (§1.3)
- [ ] Write down the missing-value policy for lag features explicitly (§1.4)
- [ ] Confirm training scripts use masked embeddings, not zero-fill (§1.5)
- [ ] Implement stacker as constrained NNLS, not plain Ridge (§1.6)
- [ ] Add persistence-baseline column to every results table (§1.7)
- [ ] Build in the Stage A→E order (§3) so there's always a working deliverable
