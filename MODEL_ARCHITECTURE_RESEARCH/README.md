# 🧠 Pre-Modeling Research & Analysis Archive
> **SIH 2026 — Problem Statement ID: SIH 25178**  
> This directory contains all exploratory analyses, mathematical formulations, comparative benchmarks, and research studies conducted **prior to building and training the final AI models**.

---

## 📑 Included Analysis Documents

| File | Core Pre-Modeling Analysis Content |
|---|---|
| 📄 **`COMPARATIVE_ANALYSIS_LIVE_DATA_INGESTION_METHODS.md`** | **13,035-Pair CAMS vs CPCB Benchmark Analysis:** Empirical analysis showing midday ozone overestimation (+69 µg/m³), proof of scalar invariance ($r$ invariance), and diurnal ratio variation ($0.18 \to 0.65$). |
| 📄 **`SUDHITH_EXTRA_FEATURES_ANALYSIS.md`** | **Atmospheric Physics & Feature Engineering Analysis:** Analysis of Planetary Boundary Layer ventilation coefficients ($\text{BLH} \times \text{wind}$), solar photolysis indices, and cyclical sine/cosine temporal projections. |
| 📄 **`MODEL_BUILD_RECOMMENDATIONS_ANALYSIS.md`** | **Pre-Modeling Strategy & Constraints:** Analysis of log-space target stabilization ($\log(1+y)$), non-negative constraints, and direct multi-horizon forecasting vs recursive compounding. |
| 📄 **`MODEL_ARCHITECTURE_RESEARCH.md`** | **Ensemble Design & Loss Formulation:** Mathematical analysis of 2-tier stacking (LightGBM with Huber L1 loss + BiLSTM with Temporal Attention + NNLS Simplex Meta-Learner). |
| 📄 **`ML_RESEARCHER_THEORETICAL_ANALYSIS.md`** | **Theoretical Multi-Horizon Modeling Handout:** Analysis of the 6 discrete forecast horizons (+1h, +3h, +6h, +12h, +24h, +48h) and error propagation bounds. |
| 📄 **`DIURNAL_CALIBRATION_ANALYSIS.md`** | **24-Hour Diurnal Transfer Model Analysis:** Mathematical derivation of hour-of-day empirical weights $w(h) = \mathbb{E}[\text{CPCB}\mid h] / \mathbb{E}[\text{CAMS}\mid h]$. |
| 📄 **`PROPOSAL_HYBRID_SATELLITE_VS_CPCB.md`** | **Hybrid Ingestion Research Proposal:** Initial theoretical proposal combining spaceborne telemetry with ground-truth sensor baselines. |
