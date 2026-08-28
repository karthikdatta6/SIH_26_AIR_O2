# AIRO2 — PHASE 1 MASTER TECHNICAL DOSSIER (PART 1)
# CPCB Ground Station Air Quality Network & ECMWF ERA5 Meteorological Reanalysis
### Smart India Hackathon (SIH) — Problem Statement ID: SIH 25178
**Ministry of Environment, Forest and Climate Change (MoEFCC) / Indian Space Research Organisation (ISRO)**

---

## 🏛️ EXECUTIVE METADATA & SYSTEM SPECIFICATION

| Specification Attribute | Operational Definition |
|---|---|
| **Document Identity** | Master Technical Dossier: CPCB CAAQMS & ECMWF ERA5 Reanalysis (Phase 1) |
| **System Architecture** | AIRO2 (Atmospheric Intelligence & Real-Time Observation Operator) |
| **Statutory Mandate** | Problem Statement ID: SIH 25178 — AI/ML Multi-Source Fusion for Ground-Level $\text{O}_3$ and $\text{NO}_2$ Forecasting |
| **Instituting Bodies** | Ministry of Environment, Forest and Climate Change (MoEFCC) & ISRO |
| **Target Geographic Domain** | Delhi National Capital Region (NCR) — 10 Canonical CAAQMS Monitoring Stations |
| **Temporal Coverage** | **CPCB Ground Truth:** 2023-01-01 00:00 UTC to 2025-12-31 23:00 UTC (3 Continuous Calendar Years) <br> **ERA5 Meteorology:** 2022-01-01 00:00 UTC to 2025-12-31 23:00 UTC (4 Full Years / 16 Quarters) |
| **Primary Target Pollutants** | Nitrogen Dioxide ($\text{NO}_2$) & Ground-Level Tropospheric Ozone ($\text{O}_3$ / `OZONE`) |
| **Chemical Precursors Harvested** | Nitric Oxide ($\text{NO}$), Nitrogen Oxides ($\text{NO}_x$), Carbon Monoxide ($\text{CO}$), Sulphur Dioxide ($\text{SO}_2$), Ammonia ($\text{NH}_3$), Fine Particulates ($\text{PM}_{2.5}$), Coarse Particulates ($\text{PM}_{10}$) |
| **Meteorological Suite** | 2m Temperature ($T_{2m}$), 2m Dewpoint ($T_{d2m}$), 10m Zonal Wind ($U_{10}$), 10m Meridional Wind ($V_{10}$), Scalar Wind Speed ($WS$), Meteorological Wind Direction ($WD$), Surface Pressure ($SP$), Boundary Layer Height ($BLH$), Surface Solar Radiation Downwards ($SSRD$), Total Precipitation ($TP$), Relative Humidity ($RH$) |
| **Phase 1 Responsible Teams** | Team A (Sudhith / Deva) — CPCB CAAQMS Ingestion <br> Team C (Revathi) — ECMWF ERA5 Meteorological Pipeline |
| **Standardization Baseline** | WMO $\ge 75\%$ Hourly Completeness Protocol, ISO 8601 UTC Standardization, EPSG:4326 to WGS84 Coords |

---

# 📑 MASTER TABLE OF CONTENTS

1. [Section 1: The Statutory Context & Scientific Mandate (SIH 25178)](#section-1-the-statutory-context--scientific-mandate-sih-25178)
   - 1.1 The Operational Breakdown of Reactive Air Quality Governance
   - 1.2 Statutory Mandate of MoEFCC / ISRO Under SIH 25178
   - 1.3 Photochemical Dynamics: The Leighton Relationship & Dual Inversion Cycle
2. [Section 2: CPCB Ground Station Data — WHAT IT IS](#section-2-cpcb-ground-station-data--what-it-is)
   - 2.1 The CAAQMS Network Architecture & Reference Instrumentation
   - 2.2 Physical Measurement Units & Raw Export Structures
   - 2.3 Comprehensive Station Registry (10 Canonical Delhi Stations)
3. [Section 3: CPCB Ground Station Data — WHY WE SELECTED IT & RELEVANCE TO SIH 25178](#section-3-cpcb-ground-station-data--why-we-selected-it--relevance-to-sih-25178)
   - 3.1 The Breathing-Zone Ground-Truth Imperative (NAAQS Regulatory Compliance)
   - 3.2 Capturing Non-Linear Precursor Chemistry ($\text{VOC}$- vs $\text{NO}_x$-Limited Regimes)
   - 3.3 Micro-Environmental Differentiation Across Urban Typologies
   - 3.4 Rejection of Lodhi Road & Strategic Selection of R.K. Puram
4. [Section 4: CPCB Ground Station Data — HOW WE EXTRACTED & STANDARDIZED IT](#section-4-cpcb-ground-station-data--how-we-extracted--standardized-it)
   - 4.1 Official Portals & Query Parameters
   - 4.2 The Pilot-First Protocol (Anand Vihar Baseline)
   - 4.3 Raw Workbook Anatomy & The 11-Row Metadata Header Offset
   - 4.4 Strict Raw Data Preservation Protocol (`data/cpcb/raw/`)
   - 4.5 Quality Control (QC) Bounds & Physical Anomaly Purification
   - 4.6 IST to UTC ISO 8601 Temporal Conversion & WMO $\ge 75\%$ Hourly Aggregation
   - 4.7 Critical Field Resolution: The `OZONE` vs `O3` Schema Trap
   - 4.8 Forensic Audit, Incident Resolution (Mandir Marg 2024) & Full Missingness Matrix
5. [Section 5: ECMWF ERA5 Meteorological Reanalysis — WHAT IT IS](#section-5-ecmwf-era5-meteorological-reanalysis--what-it-is)
   - 5.1 Overview of the Fifth-Generation ECMWF Atmospheric Reanalysis
   - 5.2 Atmospheric Parameters, Dimensions, and Spatiotemporal Resolution
   - 5.3 Ingestion Architecture (16 Consecutive Calendar Quarters)
6. [Section 6: ECMWF ERA5 Meteorological Reanalysis — WHY WE SELECTED IT & RELEVANCE TO SIH 25178](#section-6-ecmwf-era5-meteorological-reanalysis--why-we-selected-it--relevance-to-sih-25178)
   - 6.1 Thermodynamic and Dynamic Forcing of Urban Air Pollution
   - 6.2 Overcoming Physical Ground Weather Sensor Deficiencies
   - 6.3 Parameter-by-Parameter Atmospheric Rationale:
     - 2m Temperature ($T_{2m}$) & Dewpoint ($T_{d2m}$) (Arrhenius Kinetics & Humidity)
     - Boundary Layer Height ($BLH$) & Thermal Inversion Trapping
     - 10m Vector Winds ($U_{10}, V_{10}$) & Transboundary Stubble/Smog Advection
     - Surface Solar Radiation Downwards ($SSRD$) & Normalized Photolysis Index
     - Surface Pressure ($SP$) & Total Precipitation ($TP$) (Wet Scavenging)
7. [Section 7: ECMWF ERA5 Meteorological Reanalysis — HOW WE EXTRACTED & STANDARDIZED IT](#section-7-ecmwf-era5-meteorological-reanalysis--how-we-extracted--standardized-it)
   - 7.1 Copernicus Climate Data Store (CDS API) Extraction Pipeline
   - 7.2 Synchronization of Instantaneous and Accumulated NetCDF Streams
   - 7.3 Haversine Spatial Nearest-Neighbor Station Matching
   - 7.4 Physics-Informed Thermodynamic Conversions & Derived Variables:
     - Kelvin to Celsius Transformation
     - Scalar Wind Speed & Circular Meteorological Direction
     - Magnus-Tetens Equation for Relative Humidity ($RH$)
     - Solar Flux Conversion ($\text{J/m}^2 \to \text{W/m}^2$)
     - Precipitation Conversion ($\text{m} \to \text{mm}$)
   - 7.5 Spatial Distance Mapping Matrix & Climatological Quality Audit
8. [Section 8: Fused Inter-Dataset Synergy & Downstream Pipeline Integration](#section-8-fused-inter-dataset-synergy--downstream-pipeline-integration)
   - 8.1 Filesystem Organization & Authoritative Directory Structure
   - 8.2 Production Python Ingestion & Verification Code
   - 8.3 Phase 1 Sign-Off & Phase 2 Entry Gate Certification

---

# SECTION 1: THE STATUTORY CONTEXT & SCIENTIFIC MANDATE (SIH 25178)

### 1.1 The Operational Breakdown of Reactive Air Quality Governance
Urban air pollution across the Indo-Gangetic Plain (IGP), centered on the Delhi National Capital Region (NCR), constitutes a premier environmental health emergency. While public attention focuses heavily on particulate matter ($\text{PM}_{2.5}$ and $\text{PM}_{10}$), secondary gaseous pollutants—specifically **Nitrogen Dioxide ($\text{NO}_2$)** and **Tropospheric Ground-Level Ozone ($\text{O}_3$)**—induce acute respiratory morbidity, irreversible pediatric lung function loss, and severe asthmatic hospitalizations.

The primary operational failure of existing government management systems is **purely reactive intervention**:
1. Statutory monitoring networks record air quality **after the fact** (measuring pollution inhaled 2 to 24 hours prior).
2. Emergency protocols under the Commission for Air Quality Management (CAQM)—such as Graded Response Action Plan (GRAP Stages I, II, III, IV)—are enforced **only after statutory thresholds are breached**.
3. Consequently, millions of citizens sustain toxic acute exposure before industrial shutdowns, commercial vehicle bans, or school closures take effect.

```
       TRADITIONAL REACTIVE MONITORING (FAILED PARADIGM):
       [Toxic Smog Spike Occurs] ──► [Ground Sensor Measures Peak] ──► [CAQM Declares Emergency GRAP] ──► [Exposure Already Occurred]
       
       AIRO2 PROACTIVE 48-HOUR FORECASTING (SIH 25178 PARADIGM):
       [Multi-Modal Data Fusion] ──► [Physics-Informed ML Models]  ──► [Accurate Forecast at +48h]     ──► [Preemptive Policy Action]
```

### 1.2 Statutory Mandate of MoEFCC / ISRO Under SIH 25178
To solve this national crisis, **Problem Statement SIH 25178** was formulated:
> *"Develop an operational artificial intelligence and machine learning framework for short-term forward forecasting of ground-level Ozone ($\text{O}_3$) and Nitrogen Dioxide ($\text{NO}_2$) concentrations by assimilating spaceborne satellite observations and meteorological reanalysis with continuous ambient ground monitoring networks."*

**AIRO2** fulfills this statutory mandate by creating a multi-modal predictive framework capable of direct, non-recursive forward forecasting across 6 horizons: **$+1\text{h}$, $+3\text{h}$, $+6\text{h}$, $+12\text{h}$, $+24\text{h}$, and $+48\text{h}$**.

### 1.3 Photochemical Dynamics: The Leighton Relationship & Dual Inversion Cycle
Unlike primary pollutants, ground-level ozone is **not emitted directly by anthropogenic sources**. It is a secondary photochemical oxidant synthesized in the lower troposphere through non-linear reactions governed by solar radiation, nitrogen oxides ($\text{NO}_x = \text{NO} + \text{NO}_2$), and volatile organic compounds ($\text{VOCs}$/$\text{HCHO}$).

#### The Photostationary State (Daytime Sunlight):
1. **Photodissociation of Nitrogen Dioxide:**
   $$\text{NO}_2 + h\nu \;(\lambda < 420\text{ nm}) \xrightarrow{J_{\text{NO}_2}} \text{NO} + \text{O}(^3\text{P})$$
2. **Rapid Synthesis of Ground-Level Ozone:**
   $$\text{O}(^3\text{P}) + \text{O}_2 + \text{M} \xrightarrow{k_2} \text{O}_3 + \text{M} \quad (\text{where M is a stabilizing third body, } \text{N}_2 \text{ or } \text{O}_2)$$
3. **Ozone Titration by Fresh Nitric Oxide:**
   $$\text{NO} + \text{O}_3 \xrightarrow{k_3} \text{NO}_2 + \text{O}_2$$

Under steady-state daytime conditions, these reactions establish the **Leighton Relationship**:
$$\frac{[\text{O}_3][\text{NO}]}{[\text{NO}_2]} = \frac{J_{\text{NO}_2}}{k_3}$$
where $J_{\text{NO}_2}$ is the photolysis rate constant directly dependent on downwelling surface solar radiation ($SSRD$), and $k_3$ is the temperature-dependent titration reaction rate constant.

#### The Nocturnal Inversion Titration Cycle:
* **Midday Peak ($12:00–16:00$ IST):** Intense solar flux ($SSRD > 600\text{ W/m}^2$) drives $J_{\text{NO}_2}$ to its maximum. $\text{NO}_2$ is rapidly photolyzed into $\text{O}(^3\text{P})$, causing ground $\text{O}_3$ concentrations to surge to peak daytime levels ($> 100–200\,\mu\text{g/m}^3$).
* **Nighttime Collapse ($20:00–06:00$ IST):** Solar flux drops to zero ($J_{\text{NO}_2} = 0$), halting ozone synthesis. Simultaneously, nocturnal heavy commercial diesel trucks enter Delhi, emitting massive volumes of fresh $\text{NO}$. In the shallow nocturnal boundary layer ($BLH < 100\text{ m}$), fresh $\text{NO}$ completely titrates available $\text{O}_3$ into $\text{NO}_2$, causing ground $\text{O}_3$ to collapse to near $0\,\mu\text{g/m}^3$ while $\text{NO}_2$ and $\text{NO}_x$ surge to extreme nocturnal peaks.

---

# SECTION 2: CPCB GROUND STATION DATA — WHAT IT IS

### 2.1 The CAAQMS Network Architecture & Reference Instrumentation
The Central Pollution Control Board (CPCB), in coordination with the Delhi Pollution Control Committee (DPCC), operates the Continuous Ambient Air Quality Monitoring Station (CAAQMS) network. Each monitoring station represents an enclosed, temperature-controlled physical shelter equipped with certified reference instruments meeting USEPA and MoEFCC regulatory standards:

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                               CAAQMS CONTINUOUS SENSOR SUITE & INSTRUMENTATION                         │
├────────────────────┬─────────────────────────────┬───────────────────────────┬─────────────────────────┤
│ Chemical Variable  │ Measurement Technology      │ Reference Standard        │ Operational Detection   │
├────────────────────┼─────────────────────────────┼───────────────────────────┼─────────────────────────┤
│ Nitrogen Dioxide   │ Chemiluminescence Analyzer  │ USEPA RFNA-1289-074       │ 0 – 1000 µg/m³          │
│ Ground-Level Ozone │ UV Photometric Analyzer     │ USEPA EQOA-0880-047       │ 0 – 1000 µg/m³ (254 nm) │
│ Nitric Oxide (NO)  │ Gas-Phase Chemiluminescence │ CPCB Standard Protocol    │ 0 – 1000 µg/m³          │
│ Carbon Monoxide    │ Non-Dispersive IR (NDIR)    │ USEPA RFCA-0981-054       │ 0 – 50 mg/m³            │
│ PM2.5 Particulate  │ Beta Attenuation Monitor    │ BAM-1020 Radiometric      │ 0 – 1000 µg/m³          │
│ PM10 Particulate   │ Beta Attenuation Monitor    │ BAM-1020 Radiometric      │ 0 – 1500 µg/m³          │
│ Sulphur Dioxide    │ Pulsed UV Fluorescence      │ USEPA EQSA-0486-060       │ 0 – 1000 µg/m³          │
│ Ammonia (NH3)      │ Catalytic Chemiluminescence │ CPCB Standard Protocol    │ 0 – 1000 µg/m³          │
└────────────────────┴─────────────────────────────┴───────────────────────────┴─────────────────────────┘
```

### 2.2 Physical Measurement Units & Raw Export Structures
* **Gaseous Pollutants ($\text{O}_3, \text{NO}_2, \text{NO}, \text{NO}_x, \text{SO}_2, \text{NH}_3$):** Measured in micrograms per cubic meter ($\mu\text{g/m}^3$).
* **Carbon Monoxide ($\text{CO}$):** Measured in milligrams per cubic meter ($\text{mg/m}^3$).
* **Particulate Matter ($\text{PM}_{2.5}, \text{PM}_{10}$):** Measured in micrograms per cubic meter ($\mu\text{g/m}^3$).
* **Sampling Frequency:** Exactly **15-minute intervals (`15M`)**, generating 96 discrete records per station per calendar day (35,040 to 35,136 rows per year).

### 2.3 Comprehensive Station Registry (10 Canonical Delhi Stations)
To ensure the AIRO2 framework captures the full spatial heterogeneity of the Delhi National Capital Region, 10 monitoring stations were audited, certified, and registered:

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                 THE 10 CANONICAL DELHI CAAQMS STATIONS                                 │
├────┬──────────────────────┬──────────────────────────────────┬───────────┬───────────┬─────────────────┤
│ #  │ Station ID           │ Station Name                     │ Latitude  │ Longitude │ Operating Body  │
├────┼──────────────────────┼──────────────────────────────────┼───────────┼───────────┼─────────────────┤
│ 1  │ `ANAND_VIHAR`        │ Anand Vihar, East Delhi          │ 28.646835 │ 77.316032 │ DPCC / CPCB     │
│ 2  │ `ITO`                │ ITO Crossing, Central Delhi      │ 28.628624 │ 77.241060 │ DPCC / CPCB     │
│ 3  │ `OKHLA_PHASE_2`      │ Okhla Phase-II, South-East Delhi │ 28.530785 │ 77.271255 │ DPCC / CPCB     │
│ 4  │ `AYA_NAGAR`          │ Aya Nagar, South Delhi           │ 28.470691 │ 77.109936 │ DPCC / CPCB     │
│ 5  │ `RK_PURAM`           │ R.K. Puram, South-West Delhi     │ 28.674045 │ 77.131023 │ DPCC / CPCB     │
│ 6  │ `DHYAN_CHAND_STADIUM`│ Major Dhyan Chand Nat. Stadium   │ 28.611281 │ 77.237738 │ DPCC / CPCB     │
│ 7  │ `MANDIR_MARG`        │ Mandir Marg, Central Delhi       │ 28.636429 │ 77.201067 │ DPCC / CPCB     │
│ 8  │ `PUNJABI_BAGH`       │ Punjabi Bagh, West Delhi         │ 28.563262 │ 77.186937 │ DPCC / CPCB     │
│ 9  │ `JAHANGIRPURI`       │ Jahangirpuri, North Delhi        │ 28.732820 │ 77.170633 │ DPCC / CPCB     │
│ 10 │ `DWARKA_SECTOR_8`    │ Dwarka Sector 8, South-West Delhi│ 28.571027 │ 77.071901 │ DPCC / CPCB     │
└────┴──────────────────────┴──────────────────────────────────┴───────────┴───────────┴─────────────────┘
```

---

# SECTION 3: CPCB GROUND STATION DATA — WHY WE SELECTED IT & RELEVANCE TO SIH 25178

### 3.1 The Breathing-Zone Ground-Truth Imperative (NAAQS Regulatory Compliance)
Spaceborne Earth observation satellites measure total atmospheric columns ($\text{mol/m}^2$) integrated vertically through the entire planetary troposphere ($0–10\text{ km}$). However:
1. Statutory public health limits established by the **National Ambient Air Quality Standards (NAAQS)** of India mandate permissible limits strictly at the **human breathing level** ($1.5–3.0\text{ m}$ elevation above ground).
2. The NAAQS 8-hour permissible standard for $\text{O}_3$ is **$100\,\mu\text{g/m}^3$** (and 1-hour standard is **$180\,\mu\text{g/m}^3$**); the 24-hour standard for $\text{NO}_2$ is **$80\,\mu\text{g/m}^3$**.
3. CPCB CAAQMS sensors provide the indisputable statutory ground truth against which AIRO2's forecasts must be validated.

### 3.2 Capturing Non-Linear Precursor Chemistry ($\text{VOC}$- vs $\text{NO}_x$-Limited Regimes)
Ground ozone formation is non-linear and sensitive to local chemical regimes:
* **$\text{VOC}$-Limited (Urban Core):** High $\text{NO}_x$ emissions suppress ozone formation via titration. Reductions in $\text{NO}_x$ alone cause ozone levels to increase unless volatile organic compounds ($\text{VOCs}$/$\text{HCHO}$) are curtailed.
* **$\text{NO}_x$-Limited (Fringes/Rural):** Ozone synthesis is directly proportional to $\text{NO}_x$ abundance.

By harvesting the complete suite of precursors ($\text{NO}, \text{NO}_x, \text{CO}, \text{PM}_{2.5}, \text{PM}_{10}, \text{SO}_2, \text{NH}_3$), AIRO2's machine learning models capture these chemical shift points rather than treating ozone as an isolated time series.

### 3.3 Micro-Environmental Differentiation Across Urban Typologies
Delhi does not have a single uniform atmosphere. To ensure model robustness across distinct urban topographies, the 10 stations were chosen across diverse functional environments:
* **`ANAND_VIHAR` (Inter-State Transport Hub):** Bordering the Anand Vihar Inter-State Bus Terminus (ISBT) and railway yard; extreme diesel locomotive and heavy bus freight emissions, representing the highest localized $\text{NO}_2$ and $\text{PM}$ corridor in India.
* **`ITO` (Arterial Commercial Hub):** Historic 12-lane central Delhi road intersection experiencing massive idling congestion during morning and evening rush hours.
* **`OKHLA_PHASE_2` (Heavy Industrial Estate):** Industrial boiler combustion, chemical plating, solvent release, and fabrication facilities.
* **`PUNJABI_BAGH` (Ring Road Mixed Commercial/Residential):** Intersection of major ring road freight transit with dense residential colonies.
* **`RK_PURAM` (Dense Multi-Story Residential):** High residential density, domestic cooking emissions, and local traffic networks.
* **`MANDIR_MARG` (Institutional & Forest Canopy):** Government institutional district characterized by mature tree canopies, high biogenic $\text{VOC}$ release, and low direct industrial combustion.
* **`DHYAN_CHAND_STADIUM` (Urban Park & Green Buffer):** Central Delhi park zone within India Gate grounds; minimal direct traffic, ideal for studying downwind photochemical transport.
* **`JAHANGIRPURI` (North Industrial & Landfill Zone):** Heavy industrial clusters and close proximity to the Bhalswa municipal solid waste landfill.
* **`DWARKA_SECTOR_8` (Open Suburban & Aviation Corridor):** Planned residential grid situated directly beneath the takeoff and approach flight path of Indira Gandhi International (IGI) Airport.
* **`AYA_NAGAR` (Semi-Rural & Southern Ridge Fringe):** Forested southern ridge border with Haryana; serves as Delhi's background baseline reference.

```
                  ┌────────────────────────────────────────────────────────┐
                  │            THE 10 MICRO-ENVIRONMENTAL REGIMES         │
                  └───────────────────────────┬────────────────────────────┘
                                              │
         ┌────────────────────────┬───────────┴────────────┬────────────────────────┐
         ▼                        ▼                        ▼                        ▼
  [TRANSPORT HUBS]        [INDUSTRIAL ZONES]       [RESIDENTIAL/CANOPY]      [BACKGROUND RIDGE]
  • Anand Vihar (ISBT)    • Okhla Phase-II         • R.K. Puram              • Aya Nagar
  • ITO (12-lane traffic) • Jahangirpuri (Landfill)• Mandir Marg (Forest)
  • Punjabi Bagh (Ring)                            • Dhyan Chand (Park)
                                                   • Dwarka Sec 8 (Aviation)
```

### 3.4 Rejection of Lodhi Road & Strategic Selection of R.K. Puram
During initial Phase 1 scoping, `LODHI_ROAD` was tentatively included. However, our preliminary temporal continuity audit revealed:
1. Severe, unrecoverable sensor hardware dropouts spanning multiple consecutive months across 2023 and 2024.
2. Inconsistent reporting of the primary target $\text{O}_3$.
3. Data completeness $< 50\%$.

To protect model integrity from artificial temporal distortions, **`LODHI_ROAD` was formally excluded** and replaced by **`RK_PURAM`** ($\text{Lat: } 28.674045, \text{Lon: } 77.131023$), which demonstrated continuous, verified $95\%+$ data availability across the target 3-year period (2023–2025).

---

# SECTION 4: CPCB GROUND STATION DATA — HOW WE EXTRACTED & STANDARDIZED IT

### 4.1 Official Portals & Query Parameters
Ground monitoring data was harvested through official government infrastructure:
* **Primary Query Portal:** CPCB Central Control Room for Air Quality Management (`https://airquality.cpcb.gov.in/ccr/`).
* **Supplementary Repository:** Open Government Data (OGD) Platform India (`https://www.data.gov.in/`).
* **Harvesting Procedure:**
  1. Select State: `Delhi` $\to$ City: `Delhi` $\to$ Station: `[Station ID]`.
  2. Select Parameters: All 9 criteria parameters (`PM2.5, PM10, NO, NO2, NOx, NH3, SO2, CO, Ozone`).
  3. Select Time Interval: **15-Minute Averages (`15M`)**.
  4. Select Calendar Range: `01-01-YYYY 00:00` to `31-12-YYYY 23:45` for years 2023, 2024, and 2025.
  5. Export Format: Microsoft Excel (`.xlsx`).

### 4.2 The Pilot-First Protocol (Anand Vihar Baseline)
Prior to scaling downloads to all 10 stations, Team A executed an isolated pilot on **Anand Vihar (2022–2025)**:
* Identified the standard 11-row header structure in CPCB exports.
* Uncovered the `OZONE` vs `O3` label mismatch.
* Confirmed that raw CPCB workbooks contained no valid meteorological fields, verifying the necessity of the ERA5 pipeline.

### 4.3 Raw Workbook Anatomy & The 11-Row Metadata Header Offset
Each downloaded workbook (`.xlsx`) contains a single worksheet named **`CPCB Ambient AQ`**. The first 10 rows consist of metadata text banners, with actual data headers beginning strictly on **Row 11**:

```text
Row 1  : "CENTRAL POLLUTION CONTROL BOARD"
Row 2  : "CONTINUOUS AMBIENT AIR QUALITY"
Row 3  : Download date and time timestamp
Row 4  : State = Delhi
Row 5  : City  = Delhi
Row 6  : Station = Anand Vihar, Delhi - DPCC
Row 7  : Parameter = "NO,PM10,PM2.5,NO2,SO2,CO,Ozone,NH3,NOx"
Row 8  : AvgPeriod = "15M"
Row 9  : From Date = 01-01-2023 00:00
Row 10 : To Date   = 31-12-2023 23:45
Row 11 : From Date | To Date | PM2.5 | PM10 | NO | NO2 | NOx | NH3 | SO2 | CO | Ozone
Row 12+: 01-01-2023 00:00 | 01-01-2023 00:15 | 142.0 | 280.0 | 45.2 | 68.4 | ...
```

### 4.4 Strict Raw Data Preservation Protocol (`data/cpcb/raw/`)
Under the Phase 1 architectural contract, **all 30 raw files in `data/cpcb/raw/` were preserved exactly as received**. No in-place editing, manual value replacement, column deletion, or lossy conversions were permitted.

**Inventory of the 30 Raw Workbooks on Disk (`data/cpcb/raw/`):**

| File Name | Station Name | Calendar Year | File Size | Status |
|---|---|:---:|:---:|:---:|
| `ANAND_VIHAR_2023_DATA.xlsx` | Anand Vihar | 2023 | 1,561.8 KB | Validated |
| `ANAND_VIHAR_2024_DATA.xlsx` | Anand Vihar | 2024 | 1,468.5 KB | Validated |
| `ANAND_VIHAR_2025_DATA.xlsx` | Anand Vihar | 2025 | 1,611.6 KB | Validated |
| `AYA_NAGAR_2023_DATA.xlsx` | Aya Nagar | 2023 | 1,660.7 KB | Validated |
| `AYA_NAGAR_2024_DATA.xlsx` | Aya Nagar | 2024 | 1,826.8 KB | Validated |
| `AYA_NAGAR_2025_DATA.xlsx` | Aya Nagar | 2025 | 1,694.0 KB | Validated |
| `DHYAN_CHAND_STADIUM_2023_DATA.xlsx` | Dhyan Chand Stadium | 2023 | 1,613.8 KB | Validated |
| `DHYAN_CHAND_STADIUM_2024_DATA.xlsx` | Dhyan Chand Stadium | 2024 | 1,638.8 KB | Validated |
| `DHYAN_CHAND_STADIUM_2025_DATA.xlsx` | Dhyan Chand Stadium | 2025 | 1,656.3 KB | Validated |
| `DWARKA_SECTOR_8_2023_DATA.xlsx` | Dwarka Sector 8 | 2023 | 1,614.9 KB | Validated |
| `DWARKA_SECTOR_8_2024_DATA.xlsx` | Dwarka Sector 8 | 2024 | 1,668.1 KB | Validated |
| `DWARKA_SECTOR_8_2025_DATA.xlsx` | Dwarka Sector 8 | 2025 | 1,671.2 KB | Validated |
| `ITO_2023_DATA.xlsx` | ITO | 2023 | 1,570.8 KB | Validated |
| `ITO_2024_DATA.xlsx` | ITO | 2024 | 1,659.6 KB | Validated |
| `ITO_2025_DATA.xlsx` | ITO | 2025 | 1,632.7 KB | Validated |
| `JAHANGIRPURI_2023_DATA.xlsx` | Jahangirpuri | 2023 | 1,603.5 KB | Validated |
| `JAHANGIRPURI_2024_DATA.xlsx` | Jahangirpuri | 2024 | 1,611.8 KB | Validated |
| `JAHANGIRPURI_2025_DATA.xlsx` | Jahangirpuri | 2025 | 1,620.6 KB | Validated |
| `MANDIR_MARG_2023_DATA.xlsx` | Mandir Marg | 2023 | 1,583.1 KB | Validated |
| `MANDIR_MARG_2024_DATA.xlsx` | Mandir Marg | 2024 | 1,615.2 KB | Re-downloaded & Validated |
| `MANDIR_MARG_2025_DATA.xlsx` | Mandir Marg | 2025 | 1,621.4 KB | Validated |
| `OKHLA_PHASE_2_2023_DATA.xlsx` | Okhla Phase II | 2023 | 1,628.4 KB | Validated |
| `OKHLA_PHASE_2_2024_DATA.xlsx` | Okhla Phase II | 2024 | 1,671.0 KB | Validated |
| `OKHLA_PHASE_2_2025_DATA.xlsx` | Okhla Phase II | 2025 | 1,653.6 KB | Validated |
| `PUNJABI_BAGH_2023_DATA.xlsx` | Punjabi Bagh | 2023 | 1,567.2 KB | Validated |
| `PUNJABI_BAGH_2024_DATA.xlsx` | Punjabi Bagh | 2024 | 1,635.8 KB | Validated |
| `PUNJABI_BAGH_2025_DATA.xlsx` | Punjabi Bagh | 2025 | 1,570.1 KB | Validated |
| `RK_PURAM_2023_DATA.xlsx` | R.K. Puram | 2023 | 1,607.3 KB | Validated |
| `RK_PURAM_2024_DATA.xlsx` | R.K. Puram | 2024 | 1,641.6 KB | Validated |
| `RK_PURAM_2025_DATA.xlsx` | R.K. Puram | 2025 | 1,655.5 KB | Validated |

### 4.5 Quality Control (QC) Bounds & Physical Anomaly Purification
CAAQMS sensors occasionally generate zero-drift artifacts, calibration spikes, or negative values during power disruptions. We established strict physical plausibility bounds:

```python
POLLUTANT_BOUNDS = {
    "PM2.5": (0.0, 1000.0),   # ug/m3
    "PM10":  (0.0, 1500.0),   # ug/m3
    "NO":    (0.0, 1000.0),   # ug/m3
    "NO2":   (0.0, 1000.0),   # ug/m3 (Target)
    "NOx":   (0.0, 1500.0),   # ug/m3
    "NH3":   (0.0, 1000.0),   # ug/m3
    "SO2":   (0.0, 1000.0),   # ug/m3
    "CO":    (0.0, 50.0),     # mg/m3
    "OZONE": (0.0, 1000.0),   # ug/m3 (Target)
}
```

**QC Cleaning Rule:**
$$\text{If } x < x_{\min} \text{ or } x > x_{\max} \implies x \leftarrow \text{NaN}$$
* **Crucial Rule:** Invalid observations were converted to `NaN`. They were **NEVER replaced with 0.0**, as an artificial zero introduces severe bias into non-linear photochemical gradients.

### 4.6 IST to UTC ISO 8601 Temporal Conversion & WMO $\ge 75\%$ Hourly Aggregation
1. **Timestamp Normalization:** Raw timestamps (`DD-MM-YYYY HH:MM` IST) were localized to `Asia/Kolkata` ($\text{UTC}+5:30$) and converted to UTC standard ISO 8601 (`datetime64[ns]`).
2. **Hourly Grid Flooring:** Timestamps were floored to nearest 1-hour UTC bins:
   $$t_{\text{hour}} = \lfloor t_{\text{utc}} \rfloor_{1\text{h}}$$
3. **World Meteorological Organization (WMO) $\ge 75\%$ Completeness Standard:**  
   Within any 1-hour interval, exactly 4 fifteen-minute readings exist ($:00, :15, :30, :45$). The hourly mean was computed **if and only if at least 3 of the 4 readings ($\ge 75\%$) were valid**:
   $$\bar{C}_{\text{hourly}} = \begin{cases} \frac{1}{N}\sum_{i=1}^{N} C_i & \text{if } N \ge 3 \\ \text{NaN} & \text{if } N < 3 \end{cases}$$
   The integer count $N \in \{0, 1, 2, 3, 4\}$ was retained as `<POLLUTANT>_obs_count`.

### 4.7 Critical Field Resolution: The `OZONE` vs `O3` Schema Trap
In raw CPCB exports, ground-level ozone is explicitly labelled **`OZONE`** (or `Ozone`), while standard atmospheric literature uses `O3`. Automated scripts searching for `df['O3']` fail silently. Our pipeline implements robust case-insensitive standardisation:
```python
col_mapping = {}
for col in df_clean.columns:
    clean_c = col.upper().replace(".", "").replace(" ", "").replace("_", "")
    if clean_c in ["OZONE", "O3"]:
        col_mapping[col] = "OZONE"
```

### 4.8 Forensic Audit, Incident Resolution (Mandir Marg 2024) & Full Missingness Matrix
* **Mandir Marg 2024 Resolution:** During initial harvesting, `MANDIR_MARG_2024_DATA.xlsx` was downloaded as an incomplete 8.8 KB stub due to a portal timeout. The Phase 1 audit flagged this anomaly; the file was purged, re-downloaded (1,615.2 KB), and verified complete across all 35,064 rows.
* **Overall Missingness Matrix (`data/quality_reports/cpcb_quality_report.csv`):**

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                        CPCB GROUND SENSOR QUALITY & MISSINGNESS AUDIT (2023–2025)                      │
├────────────────────┬──────────────────┬─────────────────┬───────────────────┬──────────────────────────┤
│ Chemical Variable  │ Raw Column Name  │ Missingness (%) │ Valid Records     │ Quality Assessment       │
├────────────────────┼──────────────────┼─────────────────┼───────────────────┼──────────────────────────┤
│ Nitrogen Dioxide   │ NO2              │ 4.27%           │ 973,228 / 1,016K  │ ✅ EXCELLENT             │
│ Ground Ozone (O3)  │ OZONE            │ 6.28%           │ 952,806 / 1,016K  │ ✅ GOOD                  │
│ PM10 Particulate   │ PM10             │ 4.25%           │ 973,444 / 1,016K  │ ✅ EXCELLENT             │
│ PM2.5 Particulate  │ PM2.5            │ 5.43%           │ 961,448 / 1,016K  │ ✅ GOOD                  │
│ Carbon Monoxide    │ CO               │ 7.61%           │ 939,285 / 1,016K  │ ✅ GOOD                  │
│ Nitric Oxide       │ NO               │ 8.12%           │ 934,100 / 1,016K  │ ✅ GOOD                  │
│ Nitrogen Oxides    │ NOx              │ 7.89%           │ 936,437 / 1,016K  │ ✅ GOOD                  │
│ Ammonia            │ NH3              │ 14.88%          │ 865,374 / 1,016K  │ ⚠️ ACCEPTABLE            │
│ Sulphur Dioxide    │ SO2              │ 19.04%          │ 823,081 / 1,016K  │ ⚠️ ACCEPTABLE            │
└────────────────────┴──────────────────┴─────────────────┴───────────────────┴──────────────────────────┘
```

---

# SECTION 5: ECMWF ERA5 METEOROLOGICAL REANALYSIS — WHAT IT IS

### 5.1 Overview of the Fifth-Generation ECMWF Atmospheric Reanalysis
The **ERA5 Reanalysis** dataset is produced by the European Centre for Medium-Range Weather Forecasts (ECMWF) under the Copernicus Climate Change Service (C3S). ERA5 combines advanced numerical weather prediction (NWP) models (IFS Cy41r2) with global observational data assimilation (4D-Var), providing a physically consistent, globally unbroken record of the planetary atmosphere.

### 5.2 Atmospheric Parameters, Dimensions, and Spatiotemporal Resolution
* **Spatial Resolution:** $0.25^\circ \times 0.25^\circ$ (~$27.75\text{ km} \times 27.75\text{ km}$ at equator, ~$24.5\text{ km}$ across Delhi NCR).
* **Temporal Resolution:** Hourly continuous timestamps ($00:00, 01:00, \dots, 23:00$ UTC).
* **Vertical Dimension:** Surface / Single-Level Atmospheric Grid.
* **Geographic Boundary:** Regional Delhi Bounding Box ($\text{North: } 29.0^\circ\text{N}, \text{West: } 76.8^\circ\text{E}, \text{South: } 28.3^\circ\text{N}, \text{East: } 77.5^\circ\text{E}$).

### 5.3 Ingestion Architecture (16 Consecutive Calendar Quarters)
To ensure reliable transfer over high-latency networks and avoid CDS queue timeouts, ERA5 data was partitioned into **16 consecutive quarterly bundles** spanning 4 full calendar years (**2022-01-01 to 2025-12-31** = 35,064 continuous hours per station):

```
data/era5/raw/
├── 2022_Q1/ (2022-01-01 to 2022-03-31)  ├── 2024_Q1/ (2024-01-01 to 2024-03-31)
├── 2022_Q2/ (2022-04-01 to 2022-06-30)  ├── 2024_Q2/ (2024-04-01 to 2024-06-30)
├── 2022_Q3/ (2022-07-01 to 2022-09-30)  ├── 2024_Q3/ (2024-07-01 to 2024-09-30)
├── 2022_Q4/ (2022-10-01 to 2022-12-31)  ├── 2024_Q4/ (2024-10-01 to 2024-12-31)
├── 2023_Q1/ (2023-01-01 to 2023-03-31)  ├── 2025_Q1/ (2025-01-01 to 2025-03-31)
├── 2023_Q2/ (2023-04-01 to 2023-06-30)  ├── 2025_Q2/ (2025-04-01 to 2025-06-30)
├── 2023_Q3/ (2023-07-01 to 2023-09-30)  ├── 2025_Q3/ (2025-07-01 to 2025-09-30)
└── 2023_Q4/ (2023-10-01 to 2023-12-31)  └── 2025_Q4/ (2025-10-01 to 2025-12-31)
```

---

# SECTION 6: ECMWF ERA5 METEOROLOGICAL REANALYSIS — WHY WE SELECTED IT & RELEVANCE TO SIH 25178

### 6.1 Thermodynamic and Dynamic Forcing of Urban Air Pollution
Ground pollution concentrations in Delhi are fundamentally dictated by atmospheric thermodynamics:
* **The Winter Smog Trapping Paradox:** In winter (Nov–Jan), total emissions remain roughly constant, but ground $\text{NO}_2$ surges by $400–600\%$ due to low nocturnal Boundary Layer Height ($BLH < 100\text{ m}$) and severe ground radiation inversions.
* **The Summer Photochemical Ozone Wave:** In summer (Apr–Jun), solar irradiance exceeds $800\text{ W/m}^2$ and temperatures exceed $40^\circ\text{C}$, accelerating photolysis reactions and driving massive midday $\text{O}_3$ spikes.

### 6.2 Overcoming Physical Ground Weather Sensor Deficiencies
While CPCB stations feature auxiliary weather masts, audits revealed:
1. Ground anemometers and thermometers frequently experience uncalibrated zero-drift or are omitted from exports.
2. Ground stations cannot measure upper-air dynamics such as **Boundary Layer Height ($BLH$)** or **Downwelling Surface Solar Radiation ($SSRD$)**.
3. Point-level ground wind measurements are heavily distorted by building wake turbulence (urban street canyon effects). ERA5 provides globally validated, physically consistent, 100% complete hourly meteorology.

### 6.3 Parameter-by-Parameter Atmospheric Rationale

#### 1. 2m Temperature ($T_{2m}$) & 2m Dewpoint ($T_{d2m}$)
* **Kinetics Mechanism:** Photochemical reaction rates $k(T)$ increase exponentially with temperature via the Arrhenius equation. Elevated temperatures also stimulate biogenic volatile organic compound (isoprene) emissions from vegetation.
* **Moisture Mechanism:** Dewpoint temperature enables precise calculation of **Relative Humidity ($RH$)**, governing aqueous-phase oxidation and secondary aerosol hygroscopic growth.

#### 2. Boundary Layer Height ($BLH$) & Thermal Inversion Trapping
* **Dispersion Volume:** The planetary boundary layer defines the physical volume into which surface emissions are diluted ($V = \text{Area} \times BLH$).
* **Ventilation Coefficient:**
  $$\text{Ventilation Coefficient } (V_c) = BLH \times \text{Wind Speed} \quad (\text{m}^2/\text{s})$$
  When $V_c < 2000\,\text{m}^2/\text{s}$, the atmosphere lacks the physical capacity to flush pollutants, triggering emergency air quality episodes.

#### 3. 10m Vector Winds ($U_{10}, V_{10}$) & Transboundary Advection
* **Zonal ($u$) & Meridional ($v$) Vectors:** Resolved horizontal wind vectors capture the synoptic transport of agricultural crop residue smoke from Punjab/Haryana (north-westerly winds) or industrial sulfur plumes from the Sonipat/Ghaziabad industrial corridors into Delhi.

#### 4. Surface Solar Radiation Downwards ($SSRD$) & Normalized Photolysis Index
* **Photolysis Forcing:** Direct solar irradiance flux ($J/\text{m}^2 \to \text{W/m}^2$) provides the direct energy input driving the rate constant $J_{\text{NO}_2}$ for $\text{NO}_2$ photolysis. In AIRO2, this forms the basis of our **Normalized Photolysis Index**:
  $$\text{photo\_index} = \frac{SSRD_{\text{W/m}^2}}{1024.0}$$

#### 5. Surface Pressure ($SP$) & Total Precipitation ($TP$)
* **Barometric Dynamics:** Surface barometric pressure ($SP$) dictates synoptic high-pressure anticyclonic stagnation (subsidence trapping) versus low-pressure convective venting.
* **Wet Scavenging:** Total precipitation ($TP$) governs the wet deposition and scavenging rate of soluble nitrogen dioxide ($\text{NO}_2 + \text{H}_2\text{O} \to \text{HNO}_3$) and atmospheric particulates.

---

# SECTION 7: ECMWF ERA5 METEOROLOGICAL REANALYSIS — HOW WE EXTRACTED & STANDARDIZED IT

### 7.1 Copernicus Climate Data Store (CDS API) Extraction Pipeline
ERA5 reanalysis grids were retrieved using the official `cdsapi` Python client:
```python
import cdsapi
c = cdsapi.Client()
c.retrieve(
    'reanalysis-era5-single-levels',
    {
        'product_type': 'reanalysis',
        'variable': [
            '2m_temperature', '2m_dewpoint_temperature', '10m_u_component_of_wind',
            '10m_v_component_of_wind', 'surface_pressure', 'boundary_layer_height',
            'surface_solar_radiation_downwards', 'total_precipitation'
        ],
        'year': ['2022', '2023', '2024', '2025'],
        'month': [f"{m:02d}" for m in range(1, 13)],
        'day': [f"{d:02d}" for d in range(1, 32)],
        'time': [f"{h:02d}:00" for h in range(24)],
        'area': [29.0, 76.8, 28.3, 77.5], # North, West, South, East (Delhi Bounding Box)
        'format': 'netcdf'
    },
    'era5_delhi_raw.nc'
)
```

### 7.2 Synchronization of Instantaneous and Accumulated NetCDF Streams
ECMWF partitions parameters into two distinct physical streams within each quarterly bundle:
1. **Instantaneous Stream (`data_stream-oper_stepType-instant.nc`):** Parameters valid at exact timestamp $t$ ($t_{2m}, d_{2m}, u_{10}, v_{10}, sp, blh$).
2. **Accumulated Stream (`data_stream-oper_stepType-accum.nc`):** Flux variables integrated over the preceding 1-hour forecast window ($ssrd, tp$).

In `validate_era5.py`, both streams were loaded via `xarray`, aligned along the `valid_time` dimension using `xr.merge([ds_instant, ds_accum], compat='override')`, and converted into unified station dataframes.

### 7.3 Haversine Spatial Nearest-Neighbor Station Matching
For each of the 10 CAAQMS stations, the nearest ERA5 grid coordinate was determined using the great-circle **Haversine Distance Formula**:

$$a = \sin^2\left(\frac{\Delta \phi}{2}\right) + \cos(\phi_1)\cos(\phi_2)\sin^2\left(\frac{\Delta \lambda}{2}\right)$$
$$d = 2 R \arctan2\left(\sqrt{a}, \sqrt{1-a}\right)$$
where $R = 6371.0\text{ km}$ is Earth's mean radius.

### 7.4 Physics-Informed Thermodynamic Conversions & Derived Variables

1. **Temperature & Dewpoint Conversion (Kelvin $\to$ Celsius):**
   $$T_{^\circ\text{C}} = T_{\text{K}} - 273.15, \quad T_{d,^\circ\text{C}} = T_{d,\text{K}} - 273.15$$
2. **Scalar Wind Speed ($WS$ in $\text{m/s}$):**
   $$\text{era5\_wind\_speed} = \sqrt{u_{10}^2 + v_{10}^2}$$
3. **Circular Meteorological Wind Direction ($WD$ in Degrees):**
   $$\text{era5\_wind\_direction} = \left(\text{degrees}\left(\text{atan2}(-u_{10}, -v_{10})\right)\right) \pmod{360}$$
4. **Relative Humidity via Magnus-Tetens Formulation ($RH$ in $\%$):**
   $$E_s = 6.112 \times \exp\left(\frac{17.67 \times T_{^\circ\text{C}}}{T_{^\circ\text{C}} + 243.5}\right)$$
   $$E = 6.112 \times \exp\left(\frac{17.67 \times T_{d,^\circ\text{C}}}{T_{d,^\circ\text{C}} + 243.5}\right)$$
   $$\text{era5\_relative\_humidity} = \text{clip}\left(100.0 \times \frac{E}{E_s}, \; 0.0, \; 100.0\right)$$
5. **Surface Pressure Conversion ($\text{Pa} \to \text{hPa}$):**
   $$\text{era5\_surface\_pressure\_hpa} = \frac{sp}{100.0}$$
6. **Solar Irradiance Flux Conversion ($\text{J/m}^2 \to \text{W/m}^2$):**
   $$\text{era5\_solar\_radiation\_w\_m2} = \max\left(0.0, \; \frac{ssrd}{3600.0}\right)$$
7. **Total Precipitation Conversion ($\text{m} \to \text{mm}$):**
   $$\text{era5\_total\_precipitation\_mm} = \max\left(0.0, \; tp \times 1000.0\right)$$

### 7.5 Spatial Distance Mapping Matrix & Climatological Quality Audit

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                        ERA5 SPATIAL MAPPING & DISTANCE AUDIT ACROSS 10 STATIONS                        │
├────┬──────────────────────┬─────────────┬─────────────┬──────────────┬──────────────┬──────────────────┤
│ #  │ Station ID           │ Station Lat │ Station Lon │ ERA5 Grid Lat│ ERA5 Grid Lon│ Haversine Dist   │
├────┼──────────────────────┼─────────────┼─────────────┼──────────────┼──────────────┼──────────────────┤
│ 1  │ ANAND_VIHAR          │ 28.646835   │ 77.316032   │ 28.7500      │ 77.2500      │ 13.156 km        │
│ 2  │ ITO                  │ 28.628624   │ 77.241060   │ 28.7500      │ 77.2500      │ 13.525 km        │
│ 3  │ OKHLA_PHASE_2        │ 28.530785   │ 77.271255   │ 28.5000      │ 77.2500      │ 4.004 km         │
│ 4  │ AYA_NAGAR            │ 28.470691   │ 77.109936   │ 28.5000      │ 77.0000      │ 11.228 km        │
│ 5  │ RK_PURAM             │ 28.674045   │ 77.131023   │ 28.7500      │ 77.2500      │ 14.351 km        │
│ 6  │ DHYAN_CHAND_STADIUM  │ 28.611281   │ 77.237738   │ 28.5000      │ 77.2500      │ 12.432 km        │
│ 7  │ MANDIR_MARG          │ 28.636429   │ 77.201067   │ 28.7500      │ 77.2500      │ 13.500 km        │
│ 8  │ PUNJABI_BAGH         │ 28.563262   │ 77.186937   │ 28.5000      │ 77.2500      │ 9.351 km         │
│ 9  │ JAHANGIRPURI         │ 28.732820   │ 77.170633   │ 28.7500      │ 77.2500      │ 7.970 km         │
│ 10 │ DWARKA_SECTOR_8      │ 28.571027   │ 77.071901   │ 28.5000      │ 77.0000      │ 10.569 km        │
└────┴──────────────────────┴─────────────┴─────────────┴──────────────┴──────────────┴──────────────────┘
```

**Quality Audit Verification (`data/quality_reports/era5_quality_report.csv`):**
* **Total Hourly Timestamps per Station:** Exactly **35,064 records** (100.0% unbroken continuous temporal grid).
* **Missingness across all 13 atmospheric variables:** **0.00% (Zero missing values)**.
* **Climatological Means across Delhi Grid:**
  * Mean 2m Temperature: $24.75^\circ\text{C}$ to $25.26^\circ\text{C}$
  * Mean Relative Humidity: $65.96\%$ to $69.80\%$
  * Mean Wind Speed: $2.43\text{ m/s}$ to $2.46\text{ m/s}$
  * Mean Surface Pressure: $982.19\text{ hPa}$ to $983.03\text{ hPa}$

---

# SECTION 8: FUSED INTER-DATASET SYNERGY & DOWNSTREAM PIPELINE INTEGRATION

### 8.1 Filesystem Organization & Authoritative Directory Structure

```text
PROJECT-AIRO2/data/
├── cpcb/
│   ├── raw/                               # 30 untouched master Excel workbooks (~47.8 MB)
│   │   ├── ANAND_VIHAR_2023_DATA.xlsx ... RK_PURAM_2025_DATA.xlsx
│   ├── metadata/
│   │   └── station_metadata.csv           # 10 stations with coordinates & DPCC agency
│   ├── download_log.csv                   # 30-entry audit log
│   ├── processed/                         # Processed hourly parquet files per station
│   │   └── <STATION_ID>_cpcb_hourly.parquet
│   └── documentation/
│       ├── CPCB_collection_notes.md
│       └── CPCB_quality_report.md
│
├── era5/
│   ├── raw/                               # 16 quarterly NetCDF bundle folders (2022–2025)
│   │   ├── 2022_Q1/ ... 2025_Q4/
│   │   └── data_stream-oper_stepType-*.nc
│   ├── metadata/                          # Variable definitions & units schema
│   ├── download_log.csv                   # 16 quarterly download entries
│   └── processed/                         # Standardized hourly parquet files per station
│       └── <STATION_ID>_era5_hourly.parquet
│
└── quality_reports/
    ├── cpcb_quality_report.csv            # Missingness & bound audit per pollutant
    ├── era5_quality_report.csv            # Climatological consistency audit
    └── spatial_matching_report.csv         # Haversine distance from station to ERA5 node
```

### 8.2 Production Python Ingestion & Verification Code

```python
import pandas as pd

# Load Anand Vihar Processed CPCB Ground Truth
df_cpcb = pd.read_parquet("PROJECT-AIRO2/data/cpcb/processed/ANAND_VIHAR_cpcb_hourly.parquet")
print(f"CPCB Columns ({df_cpcb.shape[1]}): {df_cpcb.columns.tolist()[:5]}...")

# Load Anand Vihar Processed ERA5 Reanalysis Weather
df_era5 = pd.read_parquet("PROJECT-AIRO2/data/era5/processed/ANAND_VIHAR_era5_hourly.parquet")
print(f"ERA5 Columns ({df_era5.shape[1]}): {df_era5.columns.tolist()[:5]}...")

# Exact 1-to-1 UTC Join
df_fused = pd.merge(df_cpcb, df_era5, on=['timestamp_utc', 'station_id'], how='inner')
print(f"✅ Successfully Harmonized {len(df_fused):,} Continuous Hourly Records for Anand Vihar.")
```

### 8.3 Phase 1 Sign-Off & Phase 2 Entry Gate Certification
* [x] **Temporal Continuity:** 26,304 unbroken 1-hour UTC timestamps per station (2023–2025).
* [x] **Ground Truth Certification:** CPCB chemical criteria readings audited under WMO $\ge 75\%$ standards.
* [x] **Meteorological Integrity:** 100% complete, non-gap thermodynamic forcing parameters mapped to all 10 stations.
* [x] **Phase 2 Ready:** Dataset certified for Spatiotemporal Fusion and Lag Feature Engineering.

---
*End of Master Technical Dossier 1 (CPCB Ground Station Network & ECMWF ERA5 Meteorological Reanalysis)*
