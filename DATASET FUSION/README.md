# 🌐 AIRO2: Spatiotemporal Dataset Fusion Pipeline
## SIH 25178 — Forecasting Ground-Level $\text{O}_3$ and $\text{NO}_2$ Using Satellite & Meteorological Data Assimilation

This self-contained package contains the **complete end-to-end data fusion and harmonization pipeline (Phase 2)** that combines 4 heterogeneous atmospheric data streams into a single, model-ready, zero-leakage hourly dataset (**263,040 rows $\times$ 45 columns**, 2023–2025 across 10 Delhi CAAQMS stations).

---

## 📁 Repository & Folder Structure

```
DATASET FUSION/
├── README.md                              # [YOU ARE HERE] Master Guide & Instructions
├── requirements.txt                       # Python dependencies
│
├── ⚙️ config/
│   ├── phase2.yaml                        # Master parameters, QA limits, date bounds
│   └── stations.csv                       # Canonical 10 Delhi CAAQMS station GPS list
│
├── 🐍 scripts/                            # Complete ETL & Fusion Python Scripts
│   ├── run_phase2_pipeline.py             # 🚀 Master Orchestrator (runs steps 1 to 9)
│   ├── validate_inputs.py                 # Step 1: Input inventory & coverage check
│   ├── validate_cpcb.py                   # Step 2: CPCB QC & WMO ≥75% hourly averaging
│   ├── validate_sentinel5p.py             # Step 3: Satellite QC & ±0.02° AOI extraction
│   ├── validate_era5.py                   # Step 4: ERA5 NetCDF loader & thermodynamic converter
│   ├── validate_geospatial.py             # Step 5: OSM metric buffers (EPSG:32643)
│   ├── missingness_analysis.py            # Step 6: 140-variable missingness & gap analysis
│   ├── build_fused_dataset.py             # Step 7: ⭐ MASTER SPATIOTEMPORAL FUSION ENGINE
│   ├── leakage_check.py                   # Step 8: Automated 5-check zero-leakage test
│   └── independent_audit.py               # Step 9: 5-point dataset certification audit
│
├── 📊 metadata/
│   ├── data_dictionary.csv                # 45-column data dictionary (units, sources, roles)
│   ├── station_locations.csv              # Station coordinates & administrative metadata
│   └── station_metadata.csv               # CPCB sensor metadata
│
└── 📘 docs/
    ├── PHASE_2_COMPLETE_DOCUMENTATION.md  # Comprehensive Phase 2 Technical Report
    └── PHASE_2_FUSION_METHODOLOGY.md      # Detailed Step-by-Step Fusion Methodology
```

---

## 🔬 The 4 Ingested Data Streams

```
  ┌────────────────────────┐  ┌────────────────────────┐  ┌────────────────────────┐  ┌────────────────────────┐
  │   CPCB Ground (IST)    │  │ Sentinel-5P (TROPOMI)  │  │    ERA5 Meteorology    │  │     OSM Geospatial     │
  │   30 XLSX / 1.01M Rows │  │  32,710 Daily Products │  │ 16 Quarters (2022-25)  │  │  Roads, Landuse, Rail  │
  └───────────┬────────────┘  └───────────┬────────────┘  └───────────┬────────────┘  └───────────┬────────────┘
              │                           │                           │                           │
              ▼                           ▼                           ▼                           ▼
  ┌────────────────────────┐  ┌────────────────────────┐  ┌────────────────────────┐  ┌────────────────────────┐
  │    validate_cpcb.py    │  │ validate_sentinel5p.py │  │    validate_era5.py    │  │ validate_geospatial.py │
  │ • IST -> UTC conversion│  │ • QA filter (75/50)    │  │ • NetCDF xarray load   │  │ • EPSG:32643 metric CRS│
  │ • 15m -> 1h (WMO >=75%)│  │ • Daily mean extraction│  │ • T, P, Wind, RH, BLH  │  │ • Road buffer lengths  │
  └───────────┬────────────┘  └───────────┬────────────┘  └───────────┬────────────┘  └───────────┬────────────┘
              │                           │                           │                           │
              └───────────────────────────┼───────────────────────────┴───────────────────────────┘
                                          │
                                          ▼
                              ┌────────────────────────┐
                              │ missingness_analysis.py│ <--- 140-Variable Temporal Gap Analysis
                              └───────────┬────────────┘
                                          │
                                          ▼
                              ┌────────────────────────┐
                              │ build_fused_dataset.py │ <--- Master 1-Hour UTC Spatiotemporal Grid
                              └───────────┬────────────┘
                                          │
                                          ▼
                              ┌────────────────────────┐
                              │   leakage_check.py     │ <--- Automated Zero-Leakage Audit (5 Checks)
                              └───────────┬────────────┘
                                          │
                                          ▼
                      ┌────────────────────────────────────────┐
                      │ data/fused/station_hourly_fused.parquet│
                      │  (263,040 rows x 45 columns | 5.33 MB) │
                      └────────────────────────────────────────┘
```

---

## ⚡ How to Run the Pipeline

### 1. Install Dependencies:
```bash
pip install -r requirements.txt
```

### 2. Run the Full Fusion Pipeline (All 9 Steps):
```bash
python scripts/run_phase2_pipeline.py
```

### 3. Run Individual Steps:
```bash
# Step 1: Validate input coverage
python scripts/validate_inputs.py

# Step 2: Clean CPCB ground data
python scripts/validate_cpcb.py

# Step 3: Filter Sentinel-5P satellite granules
python scripts/validate_sentinel5p.py

# Step 4: Extract ERA5 meteorology
python scripts/validate_era5.py

# Step 5: Extract OSM geospatial buffers
python scripts/validate_geospatial.py

# Step 6: Run gap analysis
python scripts/missingness_analysis.py

# Step 7: Build master fused Parquet dataset
python scripts/build_fused_dataset.py

# Step 8: Run zero-leakage audit
python scripts/leakage_check.py

# Step 9: Run final independent audit
python scripts/independent_audit.py
```

---

## 🚀 How to Push This Folder to a New GitHub Repository

Run these exact commands in your terminal:

```bash
# 1. Navigate into this folder
cd "/Users/kadalirevathi/SIH 2026 AIRO2/DATASET FUSION"

# 2. Initialize Git
git init
git branch -M main

# 3. Stage all files
git add .

# 4. Commit
git commit -m "Initial commit: Complete AIRO2 Dataset Fusion Pipeline (SIH 25178)"

# 5. Add your new GitHub repository remote URL
# (Replace with your actual GitHub username and repository name)
git remote add origin https://github.com/<YOUR_GITHUB_USERNAME>/<YOUR_NEW_REPO>.git

# 6. Push to GitHub
git push -u origin main
```
