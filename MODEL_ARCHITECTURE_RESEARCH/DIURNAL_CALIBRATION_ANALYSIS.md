# Live Data Ingestion — Diurnal Calibration Changes

**Date:** 2026-08-28
**Scope:** `LIVE_DATA/` ozone calibration logic, plus one unresolved blocker in backend integration.
**Requested by:** Arbitration of Option A (Sudhith — satellite assimilation) vs. Option B (Hemanth —
diurnal calibration) vs. Option C (unified synthesis), per
`SUDHITH METHOD/CONFLICT OF INTEREST/COMPARATIVE_ANALYSIS_LIVE_DATA_INGESTION_METHODS.md`.

---

## 1. Decision

**Option C — satellite/NWP ingestion (Sudhith) calibrated with an hour-of-day transfer function
(Hemanth) — is correct**, and is what the code changes below implement. Two independent reasons:

1. **Mandate compliance.** SIH 25178 requires satellite data assimilation. Direct CPCB scraping
   (the alternative to satellite ingestion) fails this outright, and is separately unviable in
   production: CPCB's public API returns AQI sub-indices, not raw concentrations; the CCR portal
   is CAPTCHA-gated; only ~400 stations exist nationally; and ground sensors carry zero forward
   information, which is fatal for a system that must forecast to +48h.
2. **Mathematical necessity of hour-of-day calibration, not a scalar.** A constant multiplier
   `α` cannot change Pearson correlation:
   `r(αX + β, Y) = sgn(α) · r(X, Y)`.
   Since the CPCB/CAMS ozone ratio swings from ~0.18 at midday to ~0.65 at night, no single
   scalar can track that swing — only a function of hour-of-day can.

This part of the arbitration dossier's reasoning is sound and is not in question. What needed
fixing was that **the code did not actually implement it.**

---

## 2. What was actually wrong before this change

Before these edits, `LIVE_DATA/live_weather_service.py` (lines ~190–193) computed the ozone
correction as:

```python
o3_titration_factor = 0.38 if raw_o3 > 40.0 else 0.75
corr_o3 = round(raw_o3 * o3_titration_factor, 2)
```

This has two problems, independent of whether `0.38`/`0.75` are good numbers:

- **It is not a function of hour-of-day at all.** It's a two-bucket threshold gated on the raw
  CAMS reading itself. The dossier's own math (§1 above) is the argument *against* exactly this
  kind of scalar/near-scalar correction — a threshold on the value doesn't restore the diurnal
  phase relationship any more than a single scalar does, because photochemical ozone can cross
  the 40 µg/m³ threshold at different times of day under different conditions.
- **It corrects on the value being corrected.** Selecting the multiplier based on `raw_o3`
  (the same quantity you're about to scale) is a fragile pattern — the correction boundary moves
  around depending on what CAMS happened to report that hour, rather than depending on what hour
  it actually is.

Additionally, the 24-hour rolling mean (`mean_24h_O3`, used as a lag/rolling feature) applied
**one blanket factor to all 24 hourly readings**, even though the entire premise of a diurnal
model is that the correction factor is different for each of those 24 hours.

Separately: the dossier presents a specific 24-value weight table and a resulting
`r: 0.346 → 0.782` improvement, attributed to a fit against "13,035 matched CAMS/CPCB pairs."
**No such matched-pairs dataset, and no script that could have produced that exact table, exists
anywhere in this repository.** `HEMANTH TEST FOLDER/CAMS_ACCURACY_EVALUATION.md` contains the
aggregate RMSE/bias table (which is well-documented) but no hour-by-hour breakdown. This doesn't
mean the table is wrong — it means it isn't currently *reproducible* from what's checked in, and
was carried into the code as a placeholder rather than a verified constant.

---

## 3. Files changed

### 3.1 `LIVE_DATA/diurnal_calibration.py` (new file)

Extracted the calibration math into its own module rather than inlining it in the HTTP-fetch
function, so it can be:
- unit-tested independently of the network call,
- re-fit and swapped out without touching `live_weather_service.py`,
- reused identically by both the instantaneous reading and the 24h rolling mean (previously the
  24h mean used a *different, blanket* correction than the instantaneous reading — now both use
  the same per-hour function, so they can't silently diverge).

Contents:
- `DIURNAL_O3_WEIGHTS_UTC`: the 24-value `w(h)` table, carried over from the dossier and
  **explicitly commented as an unverified placeholder** — see §5 below for what must happen
  before this is trusted in production.
- `NO2_MEAN_BIAS_CORRECTION = 0.96`: kept as a flat scalar, deliberately **not** given an
  hour-of-day table. Reason: Hemanth's benchmark shows NO2 has a *small mean bias* (+1.48 µg/m³)
  but *weak hour-to-hour correlation* (r = 0.206) against CPCB. Fitting a 24-value diurnal table
  to data that only weakly correlates in the first place would be fitting noise, not signal —
  there isn't a demonstrated diurnal relationship for NO2 the way there is for O3's photolysis
  cycle. A flat mean-bias correction is the defensible amount of correction given the evidence
  actually in the repo.
- `calibrate_o3()`, `calibrate_no2()`, `calibrate_cams_chemistry()`: the callable functions.

### 3.2 `LIVE_DATA/live_weather_service.py`

- `fetch_live_air_chemistry()` gained a `target_hour_utc: Optional[int] = None` parameter,
  defaulting to `datetime.datetime.utcnow().hour` when the caller doesn't know/care about a
  specific target hour (e.g. a "what's the AQI right now" summary call). This is what makes the
  hour-of-day calibration possible — the previous signature had no way to know which hour's
  weight to apply.
- Replaced the `0.38 if raw_o3 > 40.0 else 0.75` threshold with `calibrate_o3(raw_o3,
  target_hour_utc)`, and added the missing NO2 correction (`calibrate_no2(raw_no2)`) — previously
  `NO2_ground` was returned completely uncalibrated even though the benchmark documents a
  measurable mean bias for it.
- Fixed the 24h rolling mean to calibrate **each hourly sample with its own hour-of-day weight**
  instead of one blanket factor:
  ```python
  o3_h_calibrated = [
      calibrate_o3(x, (target_hour_utc - (len(o3_h_raw) - 1 - j)) % 24)
      for j, x in enumerate(o3_h_raw)
  ]
  ```
  The index arithmetic exists because the Open-Meteo response returns the last 24 hourly values
  ending at "now" (via `past_days=1&forecast_days=1`, sliced `[-24:]`), not labeled with explicit
  hour-of-day — so each array position's UTC hour is derived by counting backward from
  `target_hour_utc`.
- Added an explicit `raw_no2` variable (previously inlined) so the corrected value could be
  computed and returned instead of the raw passthrough that existed before.

### 3.3 `LIVE_DATA/live_feature_assembler.py`

- Reordered `build_live_58_features()` so `target_dt` is resolved **before** the chemistry fetch,
  not after. Previously the code called `fetch_live_air_chemistry(...)` first and computed
  `target_dt` afterward — meaning even if the calibration function had existed, this call site
  had no target hour available to give it.
- Passes `target_hour_utc=target_dt.hour` into `fetch_live_air_chemistry()`, so a forecast
  requested for a specific future/past hour gets ozone calibrated for *that* hour, not whatever
  hour the server happens to be running the request at.
- No other logic in this file was touched — the existing IST/UTC handling, cyclical time
  features, and lag/rolling feature construction were left as-is.

### 3.4 `scripts/fit_diurnal_weights.py` (new file)

A fitting script, not a code-path change — this is the tool needed to turn
`DIURNAL_O3_WEIGHTS_UTC` from a placeholder into a verified constant. It:
- reads a CSV of matched `(timestamp_utc, cams_o3, cpcb_o3)` rows,
- computes `w(h) = mean(cpcb_o3 | hour=h) / mean(cams_o3 | hour=h)` for each of the 24 hours,
- prints the sample count per hour and flags any hour with `n < 30`, since a weight fit from a
  handful of samples for a given hour would be no more trustworthy than the current placeholder.

This script was **not run** as part of this change, because the underlying matched-pairs dataset
referenced in the dossier (13,035 rows) does not exist anywhere in this repository — it was
presumably generated on whichever machine produced `CAMS_ACCURACY_EVALUATION.md` and never
checked in. Locating or regenerating that dataset and running this script is a prerequisite for
treating the O3 calibration as production-verified rather than a documented best guess.

---

## 4. What was *not* changed

- **The backend package-naming mismatch was left unresolved, by design.** Every file under
  `SUDHITH METHOD/SITE BACKEND/app/` imports `from backend.app...`, but no directory literally
  named `backend` exists in this repository — only `SUDHITH METHOD/SITE BACKEND` (with a space,
  which can't be imported as a Python package under that name regardless). This means the backend
  cannot currently start at all, independent of anything to do with calibration. The dossier's
  claim that two backend architectures (`backend/` and `SITE BACKEND/`) are "fully operational"
  does not match what's on disk — there is one backend, and it doesn't import cleanly as checked
  out.
  This was **not auto-fixed** because it's a structural rename (`git mv "SUDHITH METHOD/SITE
  BACKEND" backend`) that could affect other in-progress work or documentation references outside
  the scope of "fix the calibration pipeline" — it's flagged for a deliberate decision rather than
  applied silently.
- **PM2.5/PM10 geo-bias correction** (`_get_bias_factors`) was left untouched — it wasn't in
  scope and nothing in the dossier or benchmark data questioned it.
- **The weather/meteorology fetch path** (`fetch_live_weather`) was not touched.

---

## 5. Before this is trusted in production

1. Locate or regenerate the 13,035-pair matched CAMS/CPCB dataset referenced in the dossier.
2. Run `scripts/fit_diurnal_weights.py` against it and inspect the per-hour sample-size warnings.
3. Replace `DIURNAL_O3_WEIGHTS_UTC` in `LIVE_DATA/diurnal_calibration.py` with the script's output.
4. Re-validate on a held-out slice of the matched data (not the same rows used to fit `w(h)`) to
   confirm the claimed `r > 0.78` / RMSE ≈ 14.20 µg/m³ figures actually hold — those numbers in
   the dossier were not independently reproducible from anything in this repo and should not be
   quoted as verified until this step is done.
5. Resolve the `backend/` vs `SITE BACKEND/` naming mismatch (§4) — nothing in `LIVE_DATA/` will
   run end-to-end through the FastAPI server until that import path exists.
