# SIH 25178 — Phase 2 Spatiotemporal Fusion Methodology
## Scientific Design Decisions, Evidence & Parameter Freeze

> **Project:** SIH 25178 — Short-term forecasting of ground-level O₃ and NO₂ using satellite and reanalysis data  
> **Phase:** 2 — Data Cleaning, Spatiotemporal Fusion & Quality Control  
> **Status:** APPROVED & FROZEN  
> **Target Horizon:** 2023-01-01 to 2025-12-31 (10 Delhi CPCB Stations)  

---

## 1. Executive Summary of Scientific Decisions

| Decision # | Decision Area | Approved Method | Scientific Justification | Frozen Configuration |
|---|---|---|---|---|
| **D1** | **CPCB Temporal Aggregation** | 1-Hour Mean ($\ge 75\%$ completeness rule) | World Meteorological Organization (WMO) standard: requires $\ge 3$ of 4 fifteen-minute readings per hour. | `aggregation: "mean"`, `min_readings: 3` |
| **D2** | **Sentinel-5P Spatial Matching** | Station-Box AOI ($\pm 0.02^\circ$ Bounding Box) | $\approx 4.4 \times 2.2\text{ km}$ spatial footprint matches TROPOMI nadir pixel resolution ($3.5 \times 5.5\text{ km}$) directly over sensor. | `satellite_buffer_degrees: 0.02` |
| **D3** | **Sentinel-5P Quality Filtering** | Product-specific QA threshold | Official ESA/Copernicus validation protocol: `NO2 >= 75` (cloud radiance $< 0.5$, no snow/ice), `CO >= 50`, `HCHO >= 50`. | `min_qa_no2: 75`, `min_qa_co: 50`, `min_qa_hcho: 50` |
| **D4** | **Sentinel-5P Temporal Association** | Contemporaneous & Subsequent forward association (Zero backward leakage) | Satellite overpass at $\approx 13:30\text{ UTC}$ is linked to hour $t \ge 14:00\text{ UTC}$. Never linked to $t < 13:30\text{ UTC}$. | `leakage_guard: true`, `max_observation_age_hours: 24` |
| **D5** | **ERA5 Spatial Extraction** | Nearest Grid Cell ($\approx 0.25^\circ \times 0.25^\circ$) | Preserves numerical consistency of ERA5 physics without introducing artificial spatial interpolation smoothing. | `era5_extraction_method: "nearest"` |
| **D6** | **Missing Predictor Representation** | Explicit `NaN` Preservation (No zero-filling) | Zero is a physical concentration ($0\ \mu\text{g/m}^3$), not absence. Imputation is deferred to Phase 3 ML pipeline. | `preserve_nans: true`, `fill_zeros: false` |
| **D7** | **Target Variables Integrity** | CPCB `OZONE_ground` & `NO2_ground` | Pure ground observations. Target variables are NEVER filled or modified. | `target_variables: ["OZONE_ground", "NO2_ground"]` |
| **D8** | **Time Standard** | Hourly UTC (`YYYY-MM-DD HH:00:00`) | Universal standard avoiding daylight savings and multi-source timezone offsets. | `timezone: "UTC"`, `grid_freq: "1h"` |

---

## 2. Detailed Decision Analysis

### Decision 1: CPCB Ground Station Temporal Aggregation
- **Problem:** CPCB raw data provides 15-minute average concentrations. The forecasting horizon is hourly.
- **Candidate Methods:**
  - *Method A:* Nearest 15-min observation to top-of-hour. (High variance, sensitive to instrument spikes).
  - *Method B:* Hourly median. (Robust to outliers, but biased for continuous pollutant dispersion).
  - *Method C (Selected):* Hourly arithmetic mean requiring $\ge 3$ valid 15-minute readings ($\ge 75\%$ data capture).
- **Literature & Guidance:** WMO Guidelines on Air Quality Monitoring (WMO-No. 1184) and CPCB CAAQMS guidelines.
- **Decision:** Method C with `observation_count` preserved as auxiliary feature.

---

### Decision 2: Sentinel-5P Spatial Matching & Aggregation
- **Problem:** Sentinel-5P Level-2 products have native resolution of $3.5 \times 5.5\text{ km}$ for NO₂/HCHO and $7 \times 7\text{ km}$ for CO. Ground stations are point locations.
- **Candidate Methods:**
  - *Method A:* Single nearest pixel centroid. (Subject to edge noise and sub-pixel cloud filtering).
  - *Method B (Selected):* Station-centered $\pm 0.02^\circ$ bounding box ($\approx 20 \times 20\text{ grid}$).
- **Literature:** Lorente et al. (2019), *Atmospheric Measurement Techniques* (TROPOMI NO₂ operational validation).
- **Decision:** Station-box spatial mean with `valid_pixel_count` tracked.

---

### Decision 3: Satellite Quality Filtering Thresholds
- **Problem:** Cloud cover and low sun-elevation angle distort satellite column retrieval.
- **Thresholds Applied:**
  - **Tropospheric NO₂ (`S5P_OFFL_L2__NO2___`):** `qa_value >= 0.75` (filters out cloud fraction $> 0.2$, snow, and bad retrievals).
  - **Carbon Monoxide (`S5P_OFFL_L2__CO____`):** `qa_value >= 0.50` (recommended by SRON validation team).
  - **Formaldehyde (`S5P_OFFL_L2__HCHO__`):** `qa_value >= 0.50` (recommended by BIRA-IASB team).
- **Decision:** Filter raw GeoTIFFs strictly at retrieval time; discard pixels below threshold.

---

### Decision 4: Temporal Alignment & Leakage Prevention
- **Problem:** Satellite observes Delhi once daily ($\approx 13:30\text{ UTC} / 19:00\text{ IST}$). A model forecasting at $10:00\text{ UTC}$ must not see the $13:30\text{ UTC}$ overpass.
- **Rules:**
  1. For hour $t$, available satellite observation is from the most recent overpass $t_{\text{sat}} \le t$.
  2. The observation age $\Delta t = t - t_{\text{sat}}$ is recorded as `satellite_age_hours`.
  3. If $\Delta t > 24\text{ hours}$, satellite features are set to `NaN` (stale observation).
- **Decision:** Forward association only. Strict zero backward leakage enforced.

---

### Decision 5: ERA5 Meteorological Spatial Mapping
- **Problem:** ERA5 is provided on a $0.25^\circ \times 0.25^\circ$ regular latitude-longitude grid ($\approx 27\text{ km}$ spacing).
- **Candidate Methods:**
  - *Method A (Selected):* Nearest grid cell center. (Preserves thermodynamic balance between $T$, $P$, $u$, $v$, and $q$).
  - *Method B:* Bilinear spatial interpolation. (Introduces artificial smoothing across microclimate gradients).
- **Decision:** Method A with exact distance in km recorded in `spatial_matching_report.csv`.

---

## 3. Parameter Freeze Table (`configs/phase2.yaml`)

```yaml
phase: 2
status: FROZEN
date_range:
  start: "2023-01-01 00:00:00"
  end: "2025-12-31 23:00:00"
  frequency: "1h"
  timezone: "UTC"

cpcb:
  temporal_aggregation: "mean"
  min_valid_samples_per_hour: 3
  pollutants:
    - OZONE
    - NO2
    - PM2.5
    - PM10
    - CO
    - NO
    - NOx
    - NH3
    - SO2

sentinel5p:
  spatial_buffer_degrees: 0.02
  max_observation_age_hours: 24
  qa_thresholds:
    NO2: 75
    CO: 50
    HCHO: 50

era5:
  spatial_extraction: "nearest"
  variables:
    - t2m
    - d2m
    - u10
    - v10
    - sp
    - blh
    - ssrd
    - tp

leakage_guard:
  strict_causality: true
  max_forward_lookahead_hours: 0
```
