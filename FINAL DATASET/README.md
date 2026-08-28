# 📦 AIRO2: Master Production Datasets (2023–2025)
## SIH 25178 — Spatiotemporally Fused & Engineered Feature Tables

This directory contains the certified, production-grade master datasets for the **AIRO2 Atmospheric AI Forecasting Platform (SIH 25178)**. All tables cover 3 full unbroken calendar years (**January 1, 2023 00:00 UTC to December 31, 2025 23:00 UTC**) across the 10 canonical Delhi CAAQMS monitoring stations.

---

## 🗂️ Directory Contents & File Matrix

```
FINAL DATASET/
├── README.md                              # [YOU ARE HERE] Master Dataset Documentation
│
├── 📊 CORE PARQUET DATASETS:
│   ├── station_hourly_fused.parquet       # ⭐ Master Fused Matrix (263,040 rows × 45 columns, 14.73 MB)
│   ├── features_engineered.parquet        # 🚀 58-Feature Engineered Matrix (263,040 rows × 62 columns, 26.96 MB)
│   ├── station_static_features.parquet    # 📍 Static OSM GIS metric buffers & land-use for 10 stations
│   └── anand_vihar_pilot.parquet          # 🧪 Pilot dataset (Anand Vihar, Jan 2023: 744 rows)
│
├── 📑 metadata/
│   ├── data_dictionary.csv                # 45-column data dictionary (units, roles, descriptions)
│   ├── station_locations.csv              # Canonical station GPS coordinates & typologies
│   └── station_metadata.csv               # CPCB station operating metadata
│
└── 🛡️ quality_reports/                    # 10 Certified Forensic Quality & Zero-Leakage CSVs
    ├── independent_dataset_audit.csv      # 5-point dataset certification audit
    ├── leakage_report.csv                 # 5-check zero-leakage automated audit
    ├── fusion_quality_report.csv          # Station-level completeness summary
    ├── missingness_report.csv             # 140-variable missingness & gap analysis
    ├── phase2_input_inventory.csv         # Raw harvest catalog across all 4 streams
    ├── station_coverage_report.csv        # Hourly grid continuity check
    ├── cpcb_quality_report.csv            # Ground sensor QC summary
    ├── sentinel5p_quality_report.csv      # Satellite QA filtering summary
    ├── era5_quality_report.csv            # Meteorology validation summary
    ├── spatial_matching_report.csv        # Spatial nearest-neighbor grid distance
    └── temporal_matching_report.csv       # Satellite backward ASOF join audit
```

---

## 🔬 Dataset Profiles & Dimensions

### 1. `station_hourly_fused.parquet` (Master Fused Dataset)
* **Row Count:** **263,040 rows** ($10\text{ stations} \times 26,304\text{ hours}$).
* **Column Count:** **45 columns**.
* **File Size:** `14.73 MB` (Snappy-compressed columnar Apache Parquet).
* **Contents:** Fuses raw CPCB ground observations ($\text{NO}_2, \text{O}_3, \text{PM}_{2.5}, \text{PM}_{10}, \text{CO}, \text{SO}_2, \text{NH}_3, \text{NO}, \text{NO}_x$), Sentinel-5P daily column densities (`sat_NO2`, `sat_CO`, `sat_HCHO`), ERA5 meteorology (13 thermodynamic/wind variables), and static GIS spatial features with zero temporal lookahead.

### 2. `features_engineered.parquet` (Model Training Matrix)
* **Row Count:** **263,040 rows**.
* **Column Count:** **62 columns** (58 engineered model features + timestamps + identifiers).
* **File Size:** `26.96 MB`.
* **Contents:** Contains all 58 features used by LightGBM and PyTorch BiLSTM models:
  * Trigonometric time cycles (`hour_sin/cos`, `doy_sin/cos`, `wind_sin/cos`)
  * Atmospheric physics (`ventilation_coeff` = BLH $\times$ Wind Speed, `photo_index` = SSRD / 1024)
  * Autoregressive trailing lags (1h, 3h, 6h, 12h, 24h lags + 6h/24h rolling means and std deviations)
  * Satellite availability flags (`sat_NO2_available`, `sat_CO_available`)
  * One-hot land-use fractions and station encodings.

---

## ⚡ How to Load and Inspect in Python

```python
import pandas as pd

# Load the Master Fused Dataset
df_fused = pd.read_parquet("station_hourly_fused.parquet")
print(f"Fused Dataset Shape: {df_fused.shape}")
print(df_fused.head())

# Load the 58-Feature Engineered Matrix
df_features = pd.read_parquet("features_engineered.parquet")
print(f"Feature Matrix Shape: {df_features.shape}")

# Load the Data Dictionary
df_dict = pd.read_csv("metadata/data_dictionary.csv")
print(df_dict[["column_name", "unit", "data_source", "role"]])
```
