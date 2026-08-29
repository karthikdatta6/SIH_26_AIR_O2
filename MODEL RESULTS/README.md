# 📊 AIRO2 — Model Results & Certified Evaluation Benchmark
> **SIH 2026 — Problem Statement ID: SIH 25178**  
> **Model Evaluation:** Direct Multi-Horizon Stacking Ensemble (LightGBM + BiLSTM-Attention + NNLS Simplex Stacking)  
> **Certified Test Period:** Held-Out Temporal Test Slices across 10 Delhi CAAQMS Stations (2023–2025)

---

## 📂 Directory Structure

```
MODEL RESULTS/
├── 📄 README.md                                                 # [YOU ARE HERE] Master Evaluation & Benchmark Summary
│
├── 📊 01_BENCHMARK_AND_METRICS_CSVS/                            # Certified Numerical Evaluation CSVs
│   ├── ensemble_evaluation_summary.csv                          # Multi-horizon ensemble RMSE, MAE, R², Willmott d
│   ├── lightgbm_evaluation_summary.csv                          # LightGBM base learner horizon performance
│   ├── bilstm_evaluation_summary.csv                            # Deep BiLSTM-Attention base learner performance
│   ├── station_evaluation_summary.csv                           # Per-station accuracy breakdown across 10 Delhi stations
│   ├── phase3_evaluation_summary.csv                            # Overall Phase 3 milestone evaluation summary
│   └── cv_fold_boundaries.csv                                   # Blocked temporal 5-fold cross-validation date ranges
│
├── 🖼️ 02_VISUALIZATIONS_AND_SHAP/                              # High-Resolution Interpretability & Trajectory Plots
│   ├── shap_summary_NO2.png                                     # TreeSHAP top feature attribution for NO2
│   ├── shap_summary_O3.png                                      # TreeSHAP top feature attribution for O3
│   ├── shap_top10_NO2.csv                                       # Top-10 SHAP feature importance table for NO2
│   ├── shap_top10_O3.csv                                        # Top-10 SHAP feature importance table for O3
│   ├── forecast_vs_actual_NO2_ITO.png                           # Observed vs Predicted trajectory plot (NO2 at ITO)
│   ├── forecast_vs_actual_O3_ITO.png                            # Observed vs Predicted trajectory plot (O3 at ITO)
│   ├── horizon_degradation_NO2.png                              # Error degradation curve across +1h to +48h (NO2)
│   └── horizon_degradation_O3.png                               # Error degradation curve across +1h to +48h (O3)
│
└── 📑 03_EVALUATION_AND_ACCURACY_REPORTS/                       # Detailed Scientific Audit & Evaluation Reports
    ├── ULTRA_DETAILED_EVALUATION_METRICS_AND_RESEARCH_AUDIT.md  # Certified 28KB In-Depth Evaluation & Audit Report
    ├── PHASE_3_EVALUATION_REPORT.md                             # Phase 3 Certified Performance Benchmark Report
    ├── PHASE_3_INTEGRITY_AND_ACCURACY_REPORT.md                 # Physical Plausibility, Invariant Checks & Proofs
    └── FINAL_EXECUTION_REPORT.md                                # Phase 3 Final Training Execution Report
```

---

## 🏆 Certified Multi-Horizon Ensemble Accuracy

### 1. Nitrogen Dioxide ($\text{NO}_2$) Performance Benchmark:
| Horizon | RMSE ($\mu\text{g/m}^3$) | MAE ($\mu\text{g/m}^3$) | $R^2$ Score | Willmott Index ($d$) | Relative Error |
|:---:|:---:|:---:|:---:|:---:|:---:|
| **+1h**  | **$10.64$** | **$7.42$** | **$0.919$** | **$0.9785$** | $14.2\%$ |
| **+3h**  | **$13.21$** | **$9.15$** | **$0.875$** | **$0.9662$** | $17.5\%$ |
| **+6h**  | **$15.84$** | **$11.02$** | **$0.821$** | **$0.9510$** | $21.1\%$ |
| **+12h** | **$17.92$** | **$12.65$** | **$0.771$** | **$0.9364$** | $24.2\%$ |
| **+24h** | **$18.65$** | **$13.18$** | **$0.752$** | **$0.9312$** | $25.2\%$ |
| **+48h** | **$20.08$** | **$14.41$** | **$0.712$** | **$0.9189$** | $27.6\%$ |

---

### 2. Ground-Level Ozone ($\text{O}_3$) Performance Benchmark:
| Horizon | RMSE ($\mu\text{g/m}^3$) | MAE ($\mu\text{g/m}^3$) | $R^2$ Score | Willmott Index ($d$) | Relative Error |
|:---:|:---:|:---:|:---:|:---:|:---:|
| **+1h**  | **$13.01$** | **$8.82$** | **$0.892$** | **$0.9712$** | $18.1\%$ |
| **+3h**  | **$15.42$** | **$10.54$** | **$0.849$** | **$0.9584$** | $21.6\%$ |
| **+6h**  | **$17.15$** | **$11.89$** | **$0.812$** | **$0.9470$** | $24.4\%$ |
| **+12h** | **$18.52$** | **$12.94$** | **$0.781$** | **$0.9381$** | $26.5\%$ |
| **+24h** | **$19.14$** | **$13.41$** | **$0.767$** | **$0.9340$** | $27.5\%$ |
| **+48h** | **$20.15$** | **$14.28$** | **$0.742$** | **$0.9265$** | $29.3\%$ |

---

## 🔍 Top Model Drivers (TreeSHAP Interpretability)

### Top $\text{NO}_2$ Drivers:
1. `NO2_ground_lag_1h` (Immediate trailing concentration & local momentum)
2. `era5_boundary_layer_height` (Planetary boundary layer inversion trapping)
3. `ventilation_coeff` ($\text{BLH} \times \text{wind speed}$ atmospheric dispersion rate)
4. `geo_road_length_1km_buffer_m` (Vehicular traffic precursor density)
5. `era5_temperature_c` (Atmospheric boundary layer thermal structure)

### Top $\text{O}_3$ Drivers:
1. `era5_solar_radiation_w_m2` (Downwelling solar UV flux driving photolysis)
2. `photo_index` ($\text{SSRD}/1024$ photolysis rate indicator)
3. `era5_temperature_c` (Thermal kinetics of volatile organic reactions)
4. `OZONE_ground_lag_1h` (Trailing baseline concentration)
5. `hour_sin` / `hour_cos` (Diurnal solar zenith angle cycle)
