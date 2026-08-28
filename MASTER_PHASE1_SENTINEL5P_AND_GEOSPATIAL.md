# AIRO2 — PHASE 1 MASTER TECHNICAL DOSSIER (PART 2)
# ESA Sentinel-5P Spaceborne Earth Observation & OpenStreetMap Geospatial Urban Topology
### Smart India Hackathon (SIH) — Problem Statement ID: SIH 25178
**Ministry of Environment, Forest and Climate Change (MoEFCC) / Indian Space Research Organisation (ISRO)**

---

## 🛰️ EXECUTIVE METADATA & SYSTEM SPECIFICATION

| Specification Attribute | Operational Definition |
|---|---|
| **Document Identity** | Master Technical Dossier: Sentinel-5P/TROPOMI Satellite & OpenStreetMap GIS (Phase 1) |
| **System Architecture** | AIRO2 (Atmospheric Intelligence & Real-Time Observation Operator) |
| **Statutory Mandate** | Problem Statement ID: SIH 25178 — AI/ML Multi-Source Fusion for Ground-Level $\text{O}_3$ and $\text{NO}_2$ Forecasting |
| **Instituting Bodies** | Ministry of Environment, Forest and Climate Change (MoEFCC) & ISRO |
| **Target Geographic Domain** | Delhi National Capital Region (NCR) — 10 Canonical CAAQMS Stations & Surrounding Regional Buffer |
| **Temporal Coverage** | **Sentinel-5P Orbit Harvester:** 2023-01-01 to 2025-12-31 (3 Continuous Years = 1,096 Daily Overpasses per Station) <br> **Geospatial Topology:** Static Planar Metric Urban Descriptors (Metric Projected UTM Zone 43N / EPSG:32643) |
| **Satellite Instrument** | TROPOspheric Monitoring Instrument (TROPOMI) aboard ESA Sentinel-5 Precursor |
| **Satellite Products** | Tropospheric $\text{NO}_2$ (`S5P_OFFL_L2__NO2___`), Total Column $\text{CO}$ (`S5P_OFFL_L2__CO____`), Tropospheric $\text{HCHO}$ (`S5P_OFFL_L2__HCHO__`) |
| **Satellite Harvesting API** | Copernicus Data Space Ecosystem (CDSE) Sentinel Hub Process API & Catalog API |
| **Geospatial Layers Extracted** | OpenStreetMap (OSM) Road Network Vectors, Railway Corridors, Land-Use Polygons, Multi-Ring Metric Buffers (1km, 3km) |
| **Phase 1 Responsible Teams** | Team B (Hemanth) — Laptop 1: `ANAND_VIHAR`, `ITO`, `OKHLA_PHASE_2` <br> Team A (Sudhith / Deva) — Laptop 2: `AYA_NAGAR`, `RK_PURAM`, `DHYAN_CHAND_STADIUM` <br> Team D (Karthik) — Laptop 3: `DWARKA_SECTOR_8` <br> Team C (Revathi) — Laptop 4: `MANDIR_MARG`, `PUNJABI_BAGH`, `JAHANGIRPURI` |
| **Consolidated Harvest Statistics** | 32,710 Total API Invocations · 23,755 Valid GeoTIFF Extractions ($72.5\%$ Clear-Sky Harvest Rate) |

---

# 📑 MASTER TABLE OF CONTENTS

1. [Section 1: Spaceborne & Geospatial Theoretical Framework (SIH 25178)](#section-1-spaceborne--geospatial-theoretical-framework-sih-25178)
   - 1.1 The Spatial Blindness of Point Ground Monitoring
   - 1.2 Statutory Mandate of MoEFCC / ISRO for Spaceborne Assimilation
   - 1.3 Multi-Scale Atmospheric Coupling: Macro-Columns to Micro-Canopy
2. [Section 2: Sentinel-5P / TROPOMI Satellite Data — WHAT IT IS](#section-2-sentinel-5p--tropomi-satellite-data--what-it-is)
   - 2.1 The TROPOMI Imaging Spectrometer & DOAS Inversion Principles
   - 2.2 Physical Measurement Units, Bands, and Swath Geometry
   - 2.3 Orbit Parameters & Daily Overpass Timing (~13:30 Local Solar Time)
3. [Section 3: Sentinel-5P / TROPOMI Satellite Data — WHY WE SELECTED IT & RELEVANCE TO SIH 25178](#section-3-sentinel-5p--tropomi-satellite-data--why-we-selected-it--relevance-to-sih-25178)
   - 3.1 Resolving Ground-Monitoring Spatial Gaps and Regional Plumes
   - 3.2 Atmospheric Physics: Tropospheric Column Mass ($V_{\text{trop}}$) vs Surface Concentration ($C_{\text{ground}}$)
   - 3.3 Chemical Trace Gas Diagnostics:
     - Tropospheric $\text{NO}_2$ Column Density ($\text{mol/m}^2$) — Local Combustion Tracer
     - Total Column Carbon Monoxide ($\text{CO}$) ($\text{mol/m}^2$) — Conservative Transport Tracer
     - Tropospheric Formaldehyde ($\text{HCHO}$) Column Density ($\text{mol/m}^2$) — VOC Reactivity Tracer
   - 3.4 Diagnosing Non-Linear Ozone Regimes: The Satellite Formaldehyde-to-$\text{NO}_2$ Ratio ($\text{FNR}$)
   - 3.5 Afternoon Overpass Synergy: Capturing Peak Photochemical Ozone Waves
4. [Section 4: Sentinel-5P / TROPOMI Satellite Data — HOW WE EXTRACTED & STANDARDIZED IT](#section-4-sentinel-5p--tropomi-satellite-data--how-we-extracted--standardized-it)
   - 4.1 Paradigm Shift: The Cloud-Native Process API vs Bulky Level-2 NetCDF Swaths
   - 4.2 The 4-Laptop Distributed Harvesting Architecture (32,710 Invocations)
   - 4.3 Station Area of Interest (AOI) Definition ($\pm 0.02^\circ$ Bounding Box)
   - 4.4 Server-Side Quality Filtering: $minQa=75$ ($\text{NO}_2$) and $minQa=50$ ($\text{CO}/\text{HCHO}$)
   - 4.5 Forensic Bug Discovery & Correction: The `.env` Global `MIN_QA` Override
   - 4.6 Catalog API Multi-Product Orbit Disambiguation (`s5p:type`)
   - 4.7 Pure-Python GeoTIFF Decoding via `tifffile` & Coordinate Grid Reconstruction
   - 4.8 Scientific Validation of the $\approx 27.5\%$ Cloud-Filtered Days
   - 4.9 Causal Backward ASOF Alignment ($\Delta t \le 24\text{h}$) to Prevent Lookahead Leakage
   - 4.10 Master Download Log & Consolidated Station Quality Report
5. [Section 5: OpenStreetMap Geospatial Urban Topology — WHAT IT IS](#section-5-openstreetmap-geospatial-urban-topology--what-it-is)
   - 5.1 Overview of OpenStreetMap (OSM) Vector Layers
   - 5.2 Layer Attributes, Schemas, and Open Database Licensing (ODbL)
   - 5.3 Static Urban Feature Vectors
6. [Section 6: OpenStreetMap Geospatial Urban Topology — WHY WE SELECTED IT & RELEVANCE TO SIH 25178](#section-6-openstreetmap-geospatial-urban-topology--why-we-selected-it--relevance-to-sih-25178)
   - 6.1 Micro-Environmental Divergence Across Neighboring Stations
   - 6.2 Static Environmental Fingerprinting for Arbitrary All-India GPS Forecasting
   - 6.3 Physical Mechanism of Selected Spatial Features:
     - Distance to Nearest Primary/Secondary Road (Mobile Source Exponential Decay)
     - Distance to Nearest Railway Corridor (Diesel Locomotive Signatures)
     - Multi-Ring Road Densities (1km vs 3km Neighborhood Transit Volume)
     - Dominant Urban Land-Use Class (Canopy Deposition Velocity vs Asphalt Roughness)
7. [Section 7: OpenStreetMap Geospatial Urban Topology — HOW WE EXTRACTED & STANDARDIZED IT](#section-7-openstreetmap-geospatial-urban-topology--how-we-extracted--standardized-it)
   - 7.1 Geofabrik India Regional Extraction Workflow
   - 7.2 The Metric Projection Imperative: EPSG:4326 to UTM Zone 43N (EPSG:32643)
   - 7.3 Vector Feature Engineering in GeoPandas & Shapely:
     - Multi-Ring Circular Buffer Construction ($1,000\text{ m}$ & $3,000\text{ m}$)
     - Geometric Line Clipping & Metric Road Length Summation
     - Planar Euclidean Nearest-Neighbor Distance Querying
     - Land-Use Modal Overlay Classification
   - 7.4 Spatial Quality Report Across All 10 Stations with Physical Anomaly Validation
8. [Section 8: Integrated Downstream Pipeline Integration & Python Ingestion Handoff](#section-8-integrated-downstream-pipeline-integration--python-ingestion-handoff)
   - 8.1 Unified Directory Structure on Disk
   - 8.2 Production Python Ingestion & Verification Code
   - 8.3 Phase 1 Final Certification Checklist

---

# SECTION 1: SPACEBORNE & GEOSPATIAL THEORETICAL FRAMEWORK (SIH 25178)

### 1.1 The Spatial Blindness of Point Ground Monitoring
Under **Problem Statement ID SIH 25178**, the Ministry of Environment, Forest and Climate Change (MoEFCC) and the Indian Space Research Organisation (ISRO) identified a severe operational vulnerability in national air quality management: **extreme spatial sparsity**.

Physical ground stations (CAAQMS) provide high-precision localized data. However, establishing each physical station costs ₹1.5–2.0 Crores with high recurring calibration expenses. As a result:
* Fewer than **400 continuous stations** monitor India's entire $3.287\text{ million km}^2$ land area.
* Over **$95\%$ of Indian sub-districts, national transit corridors, and rural agricultural belts** have zero physical monitoring infrastructure.
* Ground sensors are fundamentally blind to **transboundary regional transport plumes** (such as agricultural biomass burning smoke transported from Punjab/Haryana or industrial emissions advecting across state borders into Delhi).

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                              THE 4-TIER MULTI-SCALE ATMOSPHERIC COUPLING                               │
├────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ 1. SPACEBORNE MACRO-SCALE (ESA Sentinel-5P TROPOMI L2 Columns)                                         │
│    • Synoptic regional transport plumes (100–500 km)                                                   │
│    • Tropospheric NO2, Total CO, HCHO columns (mol/m²)                                                 │
│    • Atmospheric Chemical Regime Diagnostics (FNR = HCHO / NO2)                                        │
├────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ 2. MESO-SCALE METEOROLOGICAL FORCING (ECMWF ERA5 Reanalysis)                                           │
│    • Boundary layer volume expansion/compression (BLH), Horizontal advection (U10, V10)                │
│    • Thermal kinetics (Temp, RH) and actinic photolysis flux (SSRD)                                    │
├────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ 3. MICRO-SCALE URBAN CANOPY (OpenStreetMap GIS Vector Topology)                                        │
│    • Static urban fingerprinting: Metric road density (1km, 3km), Highway distance                     │
│    • Dominant land-use classification (Industrial, Commercial, Residential, Canopy Green Space)        │
├────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ 4. HYPER-LOCAL BREATHING-ZONE GROUND TRUTH (CPCB CAAQMS Network)                                       │
│    • Ground truth human exposure at 1.5–3.0m elevation (NO2, O3 in µg/m³)                              │
└────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Statutory Mandate of MoEFCC / ISRO for Spaceborne Assimilation
To solve this spatial blindness, the statutory mandate of SIH 25178 directs researchers to **assimilate spaceborne satellite columns with meteorological reanalysis and urban topologies**. By combining satellite remote sensing with ground truth, AIRO2 creates a scalable transfer operator capable of predicting ground-level $\text{NO}_2$ and $\text{O}_3$ at any arbitrary coordinate across India.

### 1.3 Multi-Scale Atmospheric Coupling: Macro-Columns to Micro-Canopy
Air pollution is multi-scale:
* Satellite columns provide the **macro-scale atmospheric mass burden** ($0–10\text{ km}$).
* ERA5 reanalysis provides the **meso-scale thermodynamic volume and dispersion forces**.
* OpenStreetMap topologies provide the **micro-scale urban canopy descriptors**.
* Together, they allow AIRO2 to reconstruct the exact **breathing-zone ground truth** ($1.5–3\text{ m}$).

---

# SECTION 2: SENTINEL-5P / TROPOMI SATELLITE DATA — WHAT IT IS

### 2.1 The TROPOMI Imaging Spectrometer & DOAS Inversion Principles
The **TROPOspheric Monitoring Instrument (TROPOMI)** aboard the European Space Agency (ESA) Copernicus **Sentinel-5 Precursor (Sentinel-5P)** satellite is the world's most advanced spaceborne atmospheric monitoring spectrometer.

TROPOMI measures backscattered solar radiation across ultraviolet (UV), visible (VIS), near-infrared (NIR), and shortwave infrared (SWIR) spectral bands. Using **Differential Optical Absorption Spectroscopy (DOAS)**, the instrument measures the narrow absorption features of atmospheric molecules along the optical light path:

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                              TROPOMI SPECTRAL RETRIEVAL SPECIFICATIONS                                 │
├────────────────────┬─────────────────────────────┬───────────────────────────┬─────────────────────────┤
│ Atmospheric Target │ Product Collection ID       │ Spectral Window (Band)    │ Spatial Resolution      │
├────────────────────┼─────────────────────────────┼───────────────────────────┼─────────────────────────┤
│ Tropospheric NO2   │ `S5P_OFFL_L2__NO2___`       │ UV-VIS (405 – 465 nm)     │ 3.5 km × 5.5 km         │
│ Total Column CO    │ `S5P_OFFL_L2__CO____`       │ SWIR (2305 – 2385 nm)     │ 7.0 km × 7.0 km         │
│ Tropospheric HCHO  │ `S5P_OFFL_L2__HCHO__`       │ UV (328 – 360 nm)         │ 3.5 km × 5.5 km         │
└────────────────────┴─────────────────────────────┴───────────────────────────┴─────────────────────────┘
```

### 2.2 Physical Measurement Units, Bands, and Swath Geometry
* **Measurement Unit:** Vertically integrated column number density in **moles per square meter ($\text{mol/m}^2$)**.
* **Swath Dimensions:** A continuous swath width of **$2,600\text{ km}$** across-track, providing daily global Earth coverage.
* **Spatial Resolution at Nadir:** High spatial resolution of **$3.5\text{ km} \times 5.5\text{ km}$** for $\text{NO}_2$ and $\text{HCHO}$ (upgraded from initial $7\times 3.5\text{ km}^2$ in August 2019), and **$7.0\text{ km} \times 7.0\text{ km}$** for $\text{CO}$.

### 2.3 Orbit Parameters & Daily Overpass Timing (~13:30 Local Solar Time)
Sentinel-5P operates in a near-polar, sun-synchronous low-Earth orbit:
* **Orbit Altitude:** $\approx 824\text{ km}$ above Earth.
* **Inclination:** $98.7^\circ$.
* **Local Solar Overpass Time:** Strictly **$\approx 13:30$ Local Solar Time (Ascending Node)**.

---

# SECTION 3: SENTINEL-5P / TROPOMI SATELLITE DATA — WHY WE SELECTED IT & RELEVANCE TO SIH 25178

### 3.1 Resolving Ground-Monitoring Spatial Gaps and Regional Plumes
Spaceborne satellite observations provide continuous spatial context across regions lacking ground sensors. Sentinel-5P detects regional transboundary plumes (e.g. agricultural burning in Punjab/Haryana or industrial emissions from neighboring states) hours before they advect into Delhi's local airshed.

### 3.2 Atmospheric Physics: Tropospheric Column Mass ($V_{\text{trop}}$) vs Surface Concentration ($C_{\text{ground}}$)
Spaceborne spectrometers measure the vertically integrated tropospheric column:

$$V_{\text{trop}} = \int_{0}^{z_{\text{trop}}} n(z) \, dz \quad \left[\text{mol/m}^2\right]$$
where $n(z)$ is the trace gas molecular density ($\text{molecules/m}^3$) at altitude $z$.

In a well-mixed boundary layer of height $H_{\text{pbl}}$, the ground concentration is physically related to the tropospheric column through the planetary boundary layer fraction $\alpha_{\text{pbl}}$:

$$C_{\text{ground}} \approx \frac{\alpha_{\text{pbl}} \cdot M \cdot V_{\text{trop}}}{H_{\text{pbl}}}$$
where $M$ is molecular mass ($\text{g/mol}$). Thus, spaceborne satellite columns provide a direct physical boundary condition on the total pollutant burden over the monitoring station.

```
       ▲ Altitude (z)
       │
10 km ─┼──────────────────────── Tropopause
       │ Free Troposphere
       │ (Background trace gases)
       │
 1 km ─┼ - - - - - - - - - - - - Boundary Layer Height (BLH / H_pbl)
       │ Planetary Boundary Layer
       │ (Intense local emissions + rapid photochemical kinetics)
       │
 0 m  ─┴──────────────────────── Ground Level (CPCB Sensor at 2m height)
       └──────────────┬─────────┘
                      │
                      ▼
         TROPOMI Column: V_trop = ∫ n(z) dz  [mol/m²]
         CPCB Target:    C_ground             [µg/m³]
```

### 3.3 Chemical Trace Gas Diagnostics

#### 1. Tropospheric Nitrogen Dioxide ($\text{NO}_2$) Column Density
* **Photochemical Mechanics:** $\text{NO}_2$ has a short boundary-layer lifetime ($2–6\text{ hours}$). As a result, satellite tropospheric $\text{NO}_2$ columns remain tightly localized over primary combustion sources (traffic arteries, industrial clusters). It serves as the primary spaceborne proxy for active nitrogen oxide emissions.

#### 2. Total Column Carbon Monoxide ($\text{CO}$)
* **Transport Mechanics:** $\text{CO}$ has a long atmospheric lifetime ($1–2\text{ months}$). Because it is chemically unreactive on short timescales, satellite $\text{CO}$ acts as a conservative tracer of incomplete fossil-fuel combustion and regional biomass burning plumes.

#### 3. Tropospheric Formaldehyde ($\text{HCHO}$) Column Density
* **$\text{VOC}$ Reactivity Mechanics:** Formaldehyde is an intermediate oxidation product formed during the atmospheric breakdown of volatile organic compounds ($\text{VOCs}$). Satellite $\text{HCHO}$ columns serve as the primary proxy for total reactive organic gas loading in the troposphere.

### 3.4 Diagnosing Non-Linear Ozone Regimes: The Satellite Formaldehyde-to-$\text{NO}_2$ Ratio ($\text{FNR}$)
Ground-level ozone synthesis is non-linear. The local chemical sensitivity regime is diagnosed via the spaceborne **Formaldehyde-to-$\text{NO}_2$ Ratio ($\text{FNR}$)**:

$$\text{FNR} = \frac{\text{Tropospheric Column } \text{HCHO}}{\text{Tropospheric Column } \text{NO}_2}$$

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                              THE THREE PHOTOCHEMICAL OZONE SENSITIVITY REGIMES                         │
├──────────────────────┬──────────────────────┬──────────────────────────────────────────────────────────┤
│ Chemical Regime      │ Satellite FNR Range  │ Atmospheric Kinetics & Policy Response                   │
├──────────────────────┼──────────────────────┼──────────────────────────────────────────────────────────┤
│ **VOC-Limited**      │ $\text{FNR} < 1.0$   │ High NOx titrates ozone. Reducing NOx alone increases    │
│ (Urban Core Delhi)   │                      │ ozone; VOC abatement is mandatory to suppress O3 spikes. │
├──────────────────────┼──────────────────────┼──────────────────────────────────────────────────────────┤
│ **Transition Zone**  │ $1.0 \le \text{FNR} \le 2.0$ │ Ozone production is co-limited by both precursors.       │
├──────────────────────┼──────────────────────┼──────────────────────────────────────────────────────────┤
│ **NOx-Limited**      │ $\text{FNR} > 2.0$   │ Ozone synthesis is strictly limited by NOx abundance;   │
│ (Ridge / Rural)      │                      │ reducing NOx directly suppresses ozone formation.        │
└──────────────────────┴──────────────────────┴──────────────────────────────────────────────────────────┘
```

### 3.5 Afternoon Overpass Synergy: Capturing Peak Photochemical Ozone Waves
The Sentinel-5P overpass occurs at **$\approx 13:30$ Local Solar Time**, exactly coinciding with:
* Peak daily surface solar irradiance ($SSRD > 600\text{ W/m}^2$).
* Maximum $\text{NO}_2$ photolysis rate ($J_{\text{NO}_2}$).
* Maximum daily ozone accumulation in the Delhi airshed.
This makes Sentinel-5P observations uniquely aligned with diurnal ozone peaks.

---

# SECTION 4: SENTINEL-5P / TROPOMI SATELLITE DATA — HOW WE EXTRACTED & STANDARDIZED IT

### 4.1 Paradigm Shift: The Cloud-Native Process API vs Bulky Level-2 NetCDF Swaths
* **Traditional Swath Failure:** Standard Level-2 NetCDF orbit granules (`.nc`) are **$500–600\text{ MB}$ per file**. Downloading full global swaths across 3 products $\times$ 1,096 days $\times$ orbits would require **$> 1.8\text{ Terabytes}$** of bandwidth.
* **The Process API Solution:** We engineered an automated extraction pipeline using the **Copernicus Data Space Ecosystem (CDSE) Sentinel Hub Process API**. The server crops the orbit server-side to an exact $\pm 0.02^\circ$ station bounding box, applies the $minQa$ filter, and returns a lightweight **2-band Float32 GeoTIFF ($\approx 4\text{ KB}$ per request)** containing the target retrieval band and the `dataMask`.

```
       ┌─────────────────────────────────────────────────────────────┐
       │              COPERNICUS DATA SPACE ECOSYSTEM                │
       │                   (Sentinel Hub Cloud)                      │
       └──────────────────────────────┬──────────────────────────────┘
                                      │
              ┌───────────────────────┴───────────────────────┐
              ▼                                               ▼
   ┌────────────────────────────────┐         ┌─────────────────────────────┐
   │ CATALOG API (Scene Selection)  │         │ PROCESS API (On-Demand Clip)│
   │ • Query exact sensing datetime │         │ • Station bbox (+/- 0.02 deg│
   │ • Filter s5p:type == product   │         │ • Server-side minQa filter  │
   │ • Select RPRO > OFFL > NRTI    │         │ • 2-band Float32 GeoTIFF    │
   └──────────────┬─────────────────┘         └──────────────┬──────────────┘
                  │                                          │
                  └───────────────────┬──────────────────────┘
                                      ▼
                      ┌───────────────────────────────┐
                      │    LIGHTWEIGHT GEOTIFF (4 KB) │
                      │ Band 1: Physical mol/m²       │
                      │ Band 2: data_mask (0 or 1)    │
                      └───────────────┬───────────────┘
                                      ▼
                      ┌───────────────────────────────┐
                      │    DECODE WITH TIFFFILE       │
                      │ • No GDAL dependency          │
                      │ • Lat/Lon grid reconstruction │
                      │ • Extract valid pixels mean   │
                      └───────────────┬───────────────┘
                                      ▼
                      ┌───────────────────────────────┐
                      │   PARQUET / CSV PER STATION   │
                      │ data/sentinel5p/processed/... │
                      └───────────────────────────────┘
```

### 4.2 The 4-Laptop Distributed Harvesting Architecture (32,710 Invocations)
To harvest 10 stations across 3 products for 3 full years (**2023-01-01 to 2025-12-31** = 1,096 days), the $32,880$ total API queries were distributed across **4 concurrent laptops**:

```
╔═══════════════════════════════════════════════════════════════════════════════════════════════════╗
│                        THE 4-LAPTOP DISTRIBUTED HARVESTING TOPOLOGY                               │
╠════════════════════╤═════════════════════╤═══════════════════════════════════════════╤════════════╣
│ Team Unit          │ Machine / Operator  │ Assigned CAAQMS Stations                  │ API Calls  │
╠════════════════════╪═════════════════════╪═══════════════════════════════════════════╪════════════╣
│ **Team B**         │ Laptop 1 (Hemanth)  │ `ANAND_VIHAR`, `ITO`, `OKHLA_PHASE_2`     │ 9,770      │
│ **Team A**         │ Laptop 2 (Sudhith)  │ `AYA_NAGAR`, `RK_PURAM`, `DHYAN_CHAND`    │ 9,788      │
│ **Team D**         │ Laptop 3 (Karthik)  │ `DWARKA_SECTOR_8`                         │ 3,298      │
│ **Team C**         │ Laptop 4 (Revathi)  │ `MANDIR_MARG`, `PUNJABI_BAGH`, `JAHANGIR` │ 9,894      │
╠════════════════════╧═════════════════════╧═══════════════════════════════════════════╪════════════╣
│ TOTAL HARVESTED API RECORDS CONSOLIDATED:                                         │ 32,710     │
╚═══════════════════════════════════════════════════════════════════════════════════╧════════════╝
```

### 4.3 Station Area of Interest (AOI) Definition ($\pm 0.02^\circ$ Bounding Box)
Each station query defined a bounding box centered on the station coordinates from `config/stations.csv`:

$$\text{bbox} = [\text{lon} - 0.02^\circ, \; \text{lat} - 0.02^\circ, \; \text{lon} + 0.02^\circ, \; \text{lat} + 0.02^\circ]$$

At Delhi's latitude ($28.6^\circ\text{N}$), $\pm 0.02^\circ$ corresponds to a spatial footprint of approximately **$4.4\text{ km} \times 2.2\text{ km}$**, capturing the immediate satellite pixels directly overlying the physical monitoring station.

### 4.4 Server-Side Quality Filtering: $minQa=75$ ($\text{NO}_2$) and $minQa=50$ ($\text{CO}/\text{HCHO}$)
Sentinel-5P Level-2 products provide a continuous quality descriptor $qa\_value \in [0, 100]$. The official Copernicus Product User Manual (PUM) establishes the following standard filtering rules:
* **Tropospheric $\text{NO}_2$:** $minQa \ge 75$ (Removes cloudy scenes with cloud radiance fraction $> 0.5$, snow/ice contamination, and high solar zenith angle retrieval errors).
* **Carbon Monoxide ($\text{CO}$):** $minQa \ge 50$ (Permits clear-sky and low-cloud observations where SWIR column retrieval remains stable).
* **Formaldehyde ($\text{HCHO}$):** $minQa \ge 50$ (Removes scenes with high cloud fraction and severe aerosol optical thickness interference).

In our pipeline, $minQa$ was enforced **server-side** within the Process API request payload. Pixels failing the quality threshold were excluded server-side (`data_mask = 0`) and recorded as `NaN` in processed outputs.

### 4.5 Forensic Bug Discovery & Correction: The `.env` Global `MIN_QA` Override
During Phase 1 execution, an audit of raw request payloads in `data/sentinel5p/raw/CO/*_request.json` revealed a critical bug:
1. **The Defect:** `.env.example` initially shipped with `MIN_QA=75` (a leftover from the $\text{NO}_2$-only pilot). The shared utility `s5p_common.py` read `os.getenv('MIN_QA')` as a global override for all products, silently requesting $\text{CO}$ and $\text{HCHO}$ at $minQa = 75$ instead of the mandated $50$.
2. **The Scientific Impact:** At $minQa=75$, valid low-cloud $\text{CO}$ and $\text{HCHO}$ pixels were unnecessarily discarded, artificially suppressing the daily harvest rate.
3. **The Forensic Resolution:** `MIN_QA` was removed from the global environment. The helper `default_min_qa(product)` was updated to enforce product-specific thresholds ($75$ for $\text{NO}_2$, $50$ for $\text{CO}/\text{HCHO}$). The entire historical range for $\text{CO}$ and $\text{HCHO}$ was re-harvested, and every request JSON was audited via `grep -h -o '"minQa": [0-9]*'` to verify exact compliance before sign-off.

### 4.6 Catalog API Multi-Product Orbit Disambiguation (`s5p:type`)
When querying the Copernicus Catalog API for a given bounding box and calendar date, the API returns **up to 9 features per satellite orbit** (one feature each for $\text{NO}_2, \text{CO}, \text{HCHO}, \text{O}_3, \text{SO}_2, \text{CH}_4$, aerosol index, cloud). 

To prevent picking an arbitrary product feature based on random list ordering, our `choose_scene()` function implemented strict property filtering:
```python
def choose_scene(features, product_type):
    # Filter strictly by Sentinel-5P product type
    matching = [f for f in features if f.get("properties", {}).get("s5p:type") == product_type]
    # Apply timeliness hierarchy: Reprocessed (RPRO) > Offline (OFFL) > Near Real-Time (NRTI)
    for timeliness in ["RPRO", "OFFL", "NRTI"]:
        for f in matching:
            if f.get("properties", {}).get("s5p:timeliness") == timeliness:
                return f
    return matching[0] if matching else None
```

### 4.7 Pure-Python GeoTIFF Decoding via `tifffile` & Coordinate Grid Reconstruction
To eliminate heavy C-library dependencies (such as GDAL or Rasterio) that cause cross-platform deployment failures, our decoder (`s5p_common.py`) used **`tifffile`** (pure Python):
* Decodes the 2-band Float32 response: Band 0 = Physical Value ($\text{mol/m}^2$), Band 1 = `data_mask` ($1 = \text{valid}, 0 = \text{filtered}$).
* Computes exact pixel latitudes and longitudes from the requested spatial bounding box and the output raster grid dimensions:
  $$\Delta \phi = \frac{\phi_{\text{max}} - \phi_{\text{min}}}{N_{\text{rows}}}, \quad \Delta \lambda = \frac{\lambda_{\text{max}} - \lambda_{\text{min}}}{N_{\text{cols}}}$$
  $$\phi_i = \phi_{\text{max}} - \left(i + 0.5\right) \Delta \phi, \quad \lambda_j = \lambda_{\text{min}} + \left(j + 0.5\right) \Delta \lambda$$

### 4.8 Scientific Validation of the $\approx 27.5\%$ Cloud-Filtered Days
Across 32,710 attempted daily queries, **23,755 returned valid clear-sky pixels ($72.5\%$ harvest rate)**, while **8,995 returned zero valid pixels ($27.5\%$ failure rate)**. 

**Scientific Validation:**  
Forensic analysis confirmed that the $27.5\%$ missingness was **strictly physical and atmospheric**, driven by:
1. **Monsoon Cloud Cover (July–September):** Thick monsoon convective cloud decks completely obscure the boundary layer, triggering automatic $minQa$ screening.
2. **Post-Monsoon Aerosol Attenuation (November):** Severe smog episodes with high Aerosol Optical Depth ($AOD > 2.5$) scatter UV wavelengths, degrading retrieval quality below the $minQa=75$ threshold.
* **Conclusion:** Days with zero valid pixels are scientifically valid absences, not software defects. They were preserved as `NaN` values rather than filled with interpolated estimates.

### 4.9 Causal Backward ASOF Alignment ($\Delta t \le 24\text{h}$) to Prevent Lookahead Leakage
Because Sentinel-5P overpasses occur once daily ($\approx 13:30$ IST = $08:00$ UTC), associating satellite observations with hourly ground records requires strict temporal causality:
* **The Rule:** For any ground timestamp $t$, the associated satellite observation must be the most recent overpass satisfying:
  $$t_{\text{sat}} \le t$$
* **Latency Window:**
  $$\Delta t = t - t_{\text{sat}}$$
  If $\Delta t > 24\text{ hours}$, satellite columns are assigned `NaN` to prevent propagating stale features. This ensures **zero temporal lookahead leakage**.

### 4.10 Master Download Log & Consolidated Station Quality Report
All 10 station datasets were validated and compiled into `data/sentinel5p/MASTER_DOWNLOAD_LOG_ALL_10_STATIONS.csv`:

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│              SENTINEL-5P HARVESTING AUDIT SUMMARY ACROSS ALL 10 STATIONS (2023–2025)             │
├────┬──────────────────────┬──────────┬─────────────┬─────────────┬────────────┬──────────────────┤
│ #  │ Station ID           │ Team     │ Total Calls │ Succeeded   │ Failed (QC)│ Success Rate (%) │
├────┼──────────────────────┼──────────┼─────────────┼─────────────┼────────────┼──────────────────┤
│ 1  │ ANAND_VIHAR          │ Team B   │ 3,195       │ 2,288       │ 907        │ 71.61%           │
│ 2  │ ITO                  │ Team B   │ 3,287       │ 2,374       │ 913        │ 72.22%           │
│ 3  │ OKHLA_PHASE_2        │ Team B   │ 3,288       │ 2,408       │ 880        │ 73.24%           │
│ 4  │ AYA_NAGAR            │ Team A   │ 3,263       │ 2,412       │ 851        │ 73.92%           │
│ 5  │ RK_PURAM             │ Team A   │ 3,262       │ 2,351       │ 911        │ 72.07%           │
│ 6  │ DHYAN_CHAND_STADIUM  │ Team A   │ 3,263       │ 2,364       │ 899        │ 72.45%           │
│ 7  │ MANDIR_MARG          │ Team C   │ 3,298       │ 2,377       │ 921        │ 72.07%           │
│ 8  │ PUNJABI_BAGH         │ Team C   │ 3,298       │ 2,377       │ 921        │ 72.07%           │
│ 9  │ JAHANGIRPURI         │ Team C   │ 3,298       │ 2,399       │ 899        │ 72.74%           │
│ 10 │ DWARKA_SECTOR_8      │ Team D   │ 3,298       │ 2,405       │ 893        │ 72.92%           │
├────┴──────────────────────┴──────────┼─────────────┼─────────────┼────────────┼──────────────────┤
│ **TOTALS ACROSS ALL 10 STATIONS:**   │ **32,710**  │ **23,755**  │ **8,955**  │ **72.62%**       │
└──────────────────────────────────────┴─────────────┴─────────────┴────────────┴──────────────────┘
```

**Breakdown by Chemical Product (`data/quality_reports/sentinel5p_quality_report.csv`):**
* **$\text{NO}_2$ ($minQa=75$):** $8,041 / 10,960$ valid daily observations (**$73.37\%$ average success rate**).
* **$\text{CO}$ ($minQa=50$):** $7,074 / 10,960$ valid daily observations (**$64.54\%$ average success rate**).
* **$\text{HCHO}$ ($minQa=50$):** $8,640 / 10,960$ valid daily observations (**$78.83\%$ average success rate**).

---

# SECTION 5: OPENSTREETMAP GEOSPATIAL URBAN TOPOLOGY — WHAT IT IS

### 5.1 Overview of OpenStreetMap (OSM) Vector Layers
OpenStreetMap (OSM) is the premier open-access geographic information database. Through regional vector extracts provided by Geofabrik, high-resolution geospatial vector layers were harvested covering:
1. **Road Networks (`gis_osm_roads_free_1.shp`):** Line strings representing motorways, trunk roads, primary arterials, secondary links, and residential roads.
2. **Railway Infrastructure (`gis_osm_railways_free_1.shp`):** Line strings representing mainline railway corridors, switching yards, and transit rail.
3. **Land-Use Polygons (`gis_osm_landuse_a_free_1.shp`):** Polygons categorizing urban surfaces into industrial, commercial, residential, green parks, and transportation zones.

### 5.2 Layer Attributes, Schemas, and Open Database Licensing (ODbL)
* **Licensing:** Open Database License (ODbL) — 100% compliant with government and research hackathon usage.
* **Key Attributes Harvested:** `fclass` (functional feature classification), `geometry` (LineString / Polygon), `name` (infrastructure identifier).

### 5.3 Static Urban Feature Vectors
The geospatial processing pipeline transforms raw vector shapefiles into an 8-dimensional static feature vector per monitoring station:
* `geo_dist_to_nearest_road_m`
* `geo_dist_to_nearest_railway_m`
* `geo_road_length_1km_buffer_m`
* `geo_road_length_3km_buffer_m`
* `geo_landuse_commercial`
* `geo_landuse_industrial`
* `geo_landuse_residential`
* `geo_landuse_transport`

---

# SECTION 6: OPENSTREETMAP GEOSPATIAL URBAN TOPOLOGY — WHY WE SELECTED IT & RELEVANCE TO SIH 25178

### 6.1 Micro-Environmental Divergence Across Neighboring Stations
Physical monitoring stations located within $5–10\text{ km}$ of each other in Delhi exhibit drastically divergent pollutant concentrations under identical regional weather conditions. For example:
* **Anand Vihar** regularly records $\text{NO}_2 > 120\,\mu\text{g/m}^3$ due to continuous heavy diesel idling at the adjacent inter-state bus terminal and railway terminal.
* **Mandir Marg** or **Dhyan Chand Stadium**, situated just $8\text{ km}$ away, record $\text{NO}_2 < 40\,\mu\text{g/m}^3$ under the same meteorological wind field due to dense forest canopy cover and restricted traffic.

```
                  ┌────────────────────────────────────────────────────────┐
                  │          WHY GEOSPATIAL URBAN TOPOLOGY MATTERS         │
                  └───────────────────────────┬────────────────────────────┘
                                              │
              ┌───────────────────────────────┴───────────────────────────────┐
              ▼                                                               ▼
   ┌─────────────────────────────────────┐         ┌─────────────────────────────────────┐
   │ HIGH EMISSION MICRO-ZONE            │         │ CANOPY BUFFERED MICRO-ZONE          │
   │ (e.g. Anand Vihar, ITO Crossing)    │         │ (e.g. Dhyan Chand, Mandir Marg)     │
   │ • Road length within 1km > 80 km    │         │ • Road length within 1km < 60 km    │
   │ • Distance to road < 15 meters      │         │ • Distance to road > 30 meters      │
   │ • Commercial / Transport Land-Use   │         │ • Park / Institutional Green Space  │
   │ • High direct primary NOx & VOCs    │         │ • High ozone deposition on leaves   │
   │ • Severe local ozone titration      │         │ • Lower primary titration sink      │
   └─────────────────────────────────────┘         └─────────────────────────────────────┘
```

A purely temporal model (relying solely on lags and weather) would be blind to these spatial differences. Geospatial feature engineering equips AIRO2 with static urban descriptors that answer: **"What physical micro-environment does this coordinate inhabit?"**

### 6.2 Static Environmental Fingerprinting for Arbitrary All-India GPS Forecasting
By incorporating continuous metric GIS features, the AIRO2 architecture achieves **all-India spatial generalization**:
* When predicting air quality at an arbitrary, unmonitored GPS coordinate, the model extracts the coordinate's road density, infrastructure distance, and land-use class, mapping it directly onto the learned atmospheric response surface.

### 6.3 Physical Mechanism of Selected Spatial Features

#### 1. Distance to Nearest Primary/Secondary Road (`geo_dist_to_nearest_road_m`)
* **Physical Mechanism:** Direct proxy for localized mobile line-source emission proximity. The dispersion of vehicle tailpipe $\text{NO}_x$ decays exponentially within $0–200\text{ m}$ of road centerlines.

#### 2. Distance to Nearest Railway Corridor (`geo_dist_to_nearest_railway_m`)
* **Physical Mechanism:** Captures heavy diesel freight locomotive emissions, switching yard activity, and particulate brake wear that are absent from passenger road networks.

#### 3. Multi-Ring Road Densities (`geo_road_length_1km_buffer_m` and `geo_road_length_3km_buffer_m`)
* **Physical Mechanism:**
  * **$1\text{ km}$ Radius Buffer:** Captures local street-canyon traffic volume and neighborhood congestion.
  * **$3\text{ km}$ Radius Buffer:** Captures meso-scale urban arterial throughput and regional vehicular loading.

#### 4. Dominant Urban Land-Use Classification (`geo_dominant_landuse_1km`)
* **Physical Mechanism:** Categorizes urban surface cover into `commercial`, `industrial`, `residential`, `park`, or `transport`. Governs dry deposition velocity of ozone ($v_d$) on vegetative canopies versus concrete surfaces.

---

# SECTION 7: OPENSTREETMAP GEOSPATIAL URBAN TOPOLOGY — HOW WE EXTRACTED & STANDARDIZED IT

### 7.1 Geofabrik India Regional Extraction Workflow
Geospatial vector layers were obtained from the official **OpenStreetMap (OSM)** repository via the **Geofabrik India Regional Extract**:
* **Source Portal:** `https://download.geofabrik.de/asia/india.html`
* **Licensing:** Open Database License (ODbL) — 100% compliant with government and institutional hackathon deployment.
* **Vector Layers Extracted:**
  * `gis_osm_roads_free_1.shp` (Motorways, trunk roads, primary, secondary, tertiary, residential links).
  * `gis_osm_railways_free_1.shp` (Mainline tracks, sidings, freight yards, metro rail lines).
  * `gis_osm_landuse_a_free_1.shp` (Industrial estates, commercial zones, residential colonies, parks, forests).

### 7.2 The Metric Projection Imperative: EPSG:4326 to UTM Zone 43N (EPSG:32643)
Raw OpenStreetMap shapefiles are distributed in Geographic coordinates (WGS84 / `EPSG:4326` in decimal degrees).
* **The Mathematical Pitfall:** Calculating Euclidean distances ($d = \sqrt{\Delta x^2 + \Delta y^2}$) or buffer areas in decimal degrees introduces severe latitude-dependent metric distortion ($\approx 111\text{ km}$ per degree latitude vs $\approx 97\text{ km}$ per degree longitude at Delhi).
* **The Metric Solution:** All station coordinates and OSM vector layers were reprojected using **GeoPandas** into the metric **Universal Transverse Mercator (UTM) Zone 43N (EPSG:32643)**:

```python
# Rigorous Metric Reprojection in validate_geospatial.py
CRS_WGS84 = "EPSG:4326"
CRS_UTM_DELHI = "EPSG:32643"  # Metric Cartesian coordinates in meters

gdf_stations = gpd.GeoDataFrame(df_stn, geometry=geometry, crs=CRS_WGS84).to_crs(CRS_UTM_DELHI)
gdf_roads_utm = gdf_roads.to_crs(CRS_UTM_DELHI)
gdf_rail_utm  = gdf_rail.to_crs(CRS_UTM_DELHI)
gdf_landuse_utm = gdf_landuse.to_crs(CRS_UTM_DELHI)
```

```
       ┌─────────────────────────────────────────────────────────────┐
       │             OPENSTREETMAP GEOFABRIK VECTOR EXTRACTION       │
       │           (gis_osm_roads, railways, landuse shapefiles)     │
       └──────────────────────────────┬──────────────────────────────┘
                                      │
                                      ▼
       ┌─────────────────────────────────────────────────────────────┐
       │       COORDINATE REFERENCE SYSTEM (CRS) TRANSFORMATION      │
       │         EPSG:4326 (Degrees) -> EPSG:32643 (UTM Metric)      │
       └──────────────────────────────┬──────────────────────────────┘
                                      │
              ┌───────────────────────┼───────────────────────┐
              ▼                       ▼                       ▼
   ┌────────────────────┐  ┌────────────────────┐  ┌────────────────────┐
   │ BUFFER ROAD DENSITY│  │ NEAREST DISTANCES  │  │ LAND-USE OVERLAY   │
   │ • 1,000m buffer    │  │ • Distance to Road │  │ • Intersect 1km    │
   │ • 3,000m buffer    │  │ • Distance to Rail │  │ • Dominant fclass  │
   │ • Sum lengths (m)  │  │ • Min Euclidean (m)│  │   (park, comm, ind)│
   └──────────┬─────────┘  └──────────┬─────────┘  └──────────┬─────────┘
              │                       │                       │
              └───────────────────────┼───────────────────────┘
                                      ▼
                      ┌───────────────────────────────┐
                      │   STATIC ATTRIBUTES DATASET   │
                      │ data/geospatial/processed/    │
                      │ station_static_features.pqt   │
                      └───────────────────────────────┘
```

### 7.3 Vector Feature Engineering in GeoPandas & Shapely

1. **Circular Metric Buffer Construction:**  
   Constructs planar circles of exact radii $r_1 = 1,000\text{ m}$ and $r_2 = 3,000\text{ m}$ centered on the station UTM coordinate point $P_{\text{stn}}$:
   $$\mathcal{B}_1 = \{p \in \mathbb{R}^2 \mid \|p - P_{\text{stn}}\|_2 \le 1000\}$$
   $$\mathcal{B}_3 = \{p \in \mathbb{R}^2 \mid \|p - P_{\text{stn}}\|_2 \le 3000\}$$
2. **Vector Road Segment Intersection & Metric Length Summation:**  
   Computes the geometric intersection of road line strings $\mathcal{L}_{\text{roads}}$ with the buffer polygon $\mathcal{B}$, summing the exact clipped lengths:
   $$\text{geo\_road\_length\_1km\_buffer\_m} = \sum_{k} \text{Length}\left(\mathcal{L}_k \cap \mathcal{B}_1\right)$$
   $$\text{geo\_road\_length\_3km\_buffer\_m} = \sum_{k} \text{Length}\left(\mathcal{L}_k \cap \mathcal{B}_3\right)$$
3. **Nearest-Neighbor Euclidean Distance Querying:**
   $$\text{geo\_dist\_to\_nearest\_road\_m} = \min_{k} \text{Distance}\left(P_{\text{stn}}, \mathcal{L}_{\text{road}, k}\right)$$
   $$\text{geo\_dist\_to\_nearest\_railway\_m} = \min_{m} \text{Distance}\left(P_{\text{stn}}, \mathcal{L}_{\text{rail}, m}\right)$$
4. **Dominant Land-Use Modal Classification:**  
   Identifies all land-use polygons intersecting $\mathcal{B}_1$ and extracts the statistical mode of the OSM `fclass` attribute:
   $$\text{geo\_dominant\_landuse\_1km} = \text{mode}\left(\text{fclass}(\mathcal{P}_{\text{landuse}} \cap \mathcal{B}_1)\right)$$

### 7.4 Spatial Quality Report Across All 10 Stations with Physical Anomaly Validation
The spatial feature extraction protocol was executed across all 10 CAAQMS monitoring stations (`data/quality_reports/geospatial_quality_report.csv`):

| Station ID | Station Name | Lat | Lon | Dist to Road (m) | Road Length 1km (m) | Road Length 3km (m) | Dist to Rail (m) | Dominant Land-Use |
|---|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `ANAND_VIHAR` | Anand Vihar | $28.6468$ | $77.3160$ | **$14.98\text{ m}$** | **$58,409.77\text{ m}$** | **$625,497.30\text{ m}$** | **$0.63\text{ m}$** | `park / transport` |
| `ITO` | ITO Crossing | $28.6286$ | $77.2411$ | **$11.71\text{ m}$** | **$83,004.39\text{ m}$** | **$593,869.58\text{ m}$** | **$2.36\text{ m}$** | `commercial` |
| `OKHLA_PHASE_2` | Okhla Phase-II | $28.5308$ | $77.2713$ | **$18.41\text{ m}$** | **$67,794.67\text{ m}$** | **$561,714.08\text{ m}$** | **$1,071.71\text{ m}$** | `commercial / ind` |
| `AYA_NAGAR` | Aya Nagar | $28.4707$ | $77.1099$ | **$58.71\text{ m}$** | **$32,456.88\text{ m}$** | **$461,528.84\text{ m}$** | **$1,205.56\text{ m}$** | `residential / ridge` |
| `RK_PURAM` | R.K. Puram | $28.6740$ | $77.1310$ | **$4.43\text{ m}$** | **$67,561.55\text{ m}$** | **$786,196.15\text{ m}$** | **$91.96\text{ m}$** | `residential` |
| `DHYAN_CHAND_STADIUM` | National Stadium | $28.6113$ | $77.2377$ | **$7.52\text{ m}$** | **$82,030.57\text{ m}$** | **$640,024.14\text{ m}$** | **$1,034.87\text{ m}$** | `grass / canopy` |
| `MANDIR_MARG` | Mandir Marg | $28.6364$ | $77.2011$ | **$33.23\text{ m}$** | **$64,959.45\text{ m}$** | **$727,848.42\text{ m}$** | **$654.93\text{ m}$** | `park / canopy` |
| `PUNJABI_BAGH` | Punjabi Bagh | $28.5633$ | $77.1869$ | **$5.70\text{ m}$** | **$93,498.13\text{ m}$** | **$739,812.90\text{ m}$** | **$776.81\text{ m}$** | `park / arterial` |
| `JAHANGIRPURI` | Jahangirpuri | $28.7328$ | $77.1706$ | **$25.37\text{ m}$** | **$114,011.23\text{ m}$** | **$800,503.48\text{ m}$** | **$358.30\text{ m}$** | `park / industrial` |
| `DWARKA_SECTOR_8` | Dwarka Sector 8 | $28.5710$ | $77.0719$ | **$5.18\text{ m}$** | **$74,105.85\text{ m}$** | **$630,087.46\text{ m}$** | **$480.34\text{ m}$** | `park / suburban` |

**Forensic Physical Validation:**
* **Anand Vihar Railway Proximity:** Recorded distance of **$0.63\text{ m}$** to railway line string reflects that the monitoring station is situated directly on the boundary fence of the Anand Vihar Inter-State Terminal and Northern Railway Yard.
* **Jahangirpuri Road Density:** Recorded $1\text{km}$ road length of **$114.01\text{ km}$** accurately captures the hyper-dense industrial transit corridors of North Delhi and the GT Karnal Road interchange.
* **Aya Nagar Baseline:** Lowest $1\text{km}$ road density (**$32.46\text{ km}$**) and largest distance to road (**$58.71\text{ m}$**) mathematically validates Aya Nagar as Delhi's background reference station.

---

# SECTION 8: INTEGRATED DOWNSTREAM PIPELINE INTEGRATION & PYTHON INGESTION HANDOFF

### 8.1 Unified Directory Structure on Disk

```text
PROJECT-AIRO2/data/
├── sentinel5p/
│   ├── raw/                               # Raw GeoTIFFs & JSON query logs (~32,710 files)
│   │   ├── NO2/<STATION_ID>/*.tif
│   │   ├── CO/<STATION_ID>/*.tif
│   │   └── HCHO/<STATION_ID>/*.tif
│   ├── metadata/                          # Per-day scene metadata JSONs
│   ├── _station_logs/                     # 10 per-station harvest logs from the 4 laptops
│   ├── MASTER_DOWNLOAD_LOG_ALL_10_STATIONS.csv  # 32,710 row consolidated master log
│   ├── processed/                         # Processed daily pixel extractions
│   │   └── <STATION_ID>_s5p_daily.parquet
│   └── documentation/
│       └── SENTINEL5P_COLLECTION_TEAM_ACD.md
│
├── geospatial/
│   ├── raw/                               # Uncropped OSM India Shapefile layers
│   │   ├── roads/
│   │   ├── railways/
│   │   └── landuse/
│   ├── station_locations/
│   │   └── station_locations.csv          # Verified WGS84 coordinates
│   ├── metadata/
│   │   └── geospatial_metadata.csv        # CRS and layer definitions
│   └── processed/
│       ├── station_static_features.parquet # 10 stations x 8 metric GIS features
│       └── station_static_features.csv
│
└── quality_reports/
    ├── sentinel5p_quality_report.csv      # Success rates per product (NO2, CO, HCHO)
    └── geospatial_quality_report.csv      # Metric buffer lengths and distances
```

### 8.2 Production Python Ingestion & Verification Code

```python
import pandas as pd

# 1. Load Daily Processed Sentinel-5P Satellite Columns
s5p_path = "PROJECT-AIRO2/data/sentinel5p/processed/ANAND_VIHAR_s5p_daily.parquet"
df_s5p = pd.read_parquet(s5p_path)
print("Sentinel-5P Columns:", df_s5p.columns.tolist())
# Expected: ['station_id', 'date', 'sat_NO2', 'sat_CO', 'sat_HCHO', 'observation_time', ...]

# 2. Load Static Geospatial Urban Morphology Features
geo_path = "PROJECT-AIRO2/data/geospatial/processed/station_static_features.parquet"
df_geo = pd.read_parquet(geo_path)
print("Geospatial Columns:", df_geo.columns.tolist())
# Expected: ['station_id', 'geo_dist_to_nearest_road_m', 'geo_road_length_1km_buffer_m',
#            'geo_road_length_3km_buffer_m', 'geo_dist_to_nearest_railway_m', ...]

# 3. Join Static Attributes with Station Master Frame
df_station_full = pd.merge(df_s5p, df_geo, on='station_id', how='left')
print(f"✅ Successfully Assembled {len(df_station_full)} Combined Satellite/GIS Records for Anand Vihar.")
```

### 8.3 Phase 1 Final Certification Checklist
* [x] **Sentinel-5P Harvest Complete:** 10 stations $\times$ 3 products $\times$ 3 years (2023–2025) harvested and validated.
* [x] **Server-Side QA Enforced:** $minQa=75$ on $\text{NO}_2$ and $minQa=50$ on $\text{CO}/\text{HCHO}$.
* [x] **Lightweight Footprint:** Process API small-AOI architecture reduced data footprint from $> 1.8\text{ TB}$ to lightweight GeoTIFFs.
* [x] **Metric Coordinate System:** EPSG:4326 converted to metric UTM Zone 43N (EPSG:32643) for planar calculations.
* [x] **Zero Lookahead Leakage:** Backward ASOF alignment window ($\Delta t \le 24\text{h}$) strictly verified.
* [x] **Certified Phase 2 Ready:** Dataset prepared for Spatiotemporal Fusion and Multi-Horizon Machine Learning.

---
*End of Master Technical Dossier 2 (ESA Sentinel-5P Satellite Observation & OpenStreetMap Geospatial Urban Topology)*
