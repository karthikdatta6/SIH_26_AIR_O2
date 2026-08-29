# 🛡️ Model Output Invariants & Physical Plausibility Checklist
> **SIH 25178 — AIRO2 Quality Assurance Standard**

Every model prediction emitted by the AIRO2 inference pipeline must satisfy the following 7 non-negotiable physical rules:

---

### ✅ Checklist of Physical Invariants:

1. **[PASSED] Strict Non-Negativity:**  
   Pollutant concentrations must never be negative ($\forall t, h: \hat{y}_{p}(t+h) \ge 0\,\mu\text{g/m}^3$).  
   *Implementation:* Inverse projection applies `expm1(np.clip(pred, 0, None))`.

2. **[PASSED] Finite Bounds & Outlier Suppression:**  
   Predictions must be finite (no `Inf` or unhandled `NaN` in predictions).  
   *Implementation:* ModelService validates finite bounds; out-of-distribution values are constrained.

3. **[PASSED] Direct Horizon Independence (No Compounding Error):**  
   Predictions are computed from 6 discrete independent models ($h \in \{1, 3, 6, 12, 24, 48\}$).  
   *Implementation:* Model output at $+3\text{h}$ is never fed recursively as input into $+6\text{h}$.

4. **[PASSED] Native Statutory Units ($\mu\text{g/m}^3$):**  
   All concentrations are in native $\mu\text{g/m}^3$ units matching CPCB CAAQM standards (no conversion to ppm/ppb).

5. **[PASSED] Exact 12-Prediction Matrix per Station:**  
   Every station forecast produces exactly 12 predictions ($2\text{ pollutants} \times 6\text{ horizons}$).

6. **[PASSED] CPCB Standard AQI Sub-Index Calculation:**  
   AQI values and categories are derived strictly from official CPCB breakpoints (linear piecewise sub-index).

7. **[PASSED] Deterministic Station Encoding:**  
   Station identity uses exact canonical IDs ($0\text{--}9$) matching trained station geometries.
