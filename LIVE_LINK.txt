========================================================================================
             AIRO2 — GROUND-LEVEL OZONE (O3) & NITROGEN DIOXIDE (NO2) FORECASTING
                                SMART INDIA HACKATHON (SIH 25178)
========================================================================================

🔗 LIVE PROJECT LINKS:
----------------------------------------------------------------------------------------
🌐 Interactive Web Dashboard (Frontend) : https://sih26airo2fe-seven.vercel.app
⚡ Live REST API & Swagger Documentation : https://sih-26-air-o2-backend.onrender.com/docs
🩺 Live Health / Liveness Probe         : https://sih-26-air-o2-backend.onrender.com/healthz
📊 Built-in Control Center Web UI       : https://sih-26-air-o2-backend.onrender.com/static/index.html
💻 GitHub Source Code Repository        : https://github.com/Sudhith/SIH_26_AIR_O2

========================================================================================


1. WHAT IS THE PROBLEM? (WHY AIR POLLUTION IS DANGEROUS)
----------------------------------------------------------------------------------------
Air pollution is not just haze in the sky — it is a serious, silent public health crisis.
In rapidly growing metropolitan regions like Delhi NCR, millions of people breathe toxic air
every single day. Prolonged exposure causes chronic asthma, lung damage, respiratory failure,
heart diseases, and reduces the average human life expectancy by several years. Children and
elderly citizens are the most vulnerable.

Most existing air quality apps only report what is happening RIGHT NOW. By the time a citizen
or city official sees that the air is "Severe", the toxic air has already been inhaled. We need
a system that tells us what is going to happen 1 to 48 hours BEFORE it happens so people and
authorities can take preventive action.


2. WHY FOCUS ON NO2 AND O3? (THE DANGEROUS CHEMICAL TWINS)
----------------------------------------------------------------------------------------
While most public attention goes to dust particles (PM2.5 and PM10), gaseous pollutants like
Nitrogen Dioxide (NO2) and Ground-Level Ozone (O3) are equally lethal and much trickier to predict:

• NITROGEN DIOXIDE (NO2):
  - Where it comes from: Vehicle exhausts, diesel engines, thermal power plants, and industrial boilers.
  - Health Impact: It inflames the lining of the lungs, reduces immunity to lung infections,
    triggers severe wheezing, and acts as the primary ingredient for toxic winter smog.

• GROUND-LEVEL OZONE (O3):
  - Where it comes from: Unlike other pollutants, Ozone is NOT emitted directly by any chimney or tailpipe.
    Instead, it is "cooked" in the atmosphere when sunlight and heat trigger complex photochemical
    reactions between vehicle fumes (NOx) and volatile organic gases.
  - Health Impact: Breathing ozone is like getting a sunburn inside your lungs. It causes chest pain,
    coughing, throat irritation, and permanently scars lung tissue.

• THE COMPLEX DANCE:
  During the daytime, blazing sunlight breaks NO2 down to form dangerous Ozone spikes. At night, fresh
  vehicle emissions eat up Ozone in a reaction called NO-titration. Because this process is highly
  non-linear and changes with every degree of temperature and breeze of wind, traditional physics
  simulations take hours to calculate. We need instant Artificial Intelligence to solve this.


3. WHAT IS OUR SOLUTION? (AIRO2)
----------------------------------------------------------------------------------------
We built AIRO2 — an ultra-fast, intelligent, multi-horizon AI/ML atmospheric chemistry forecaster.

Instead of just telling you past or current pollution, AIRO2 predicts exact ground-level NO2 and O3
concentrations (in ug/m3) and official CPCB AQI categories across 6 DISCRETE FUTURE TIME HORIZONS:
  👉 +1 Hour  (Immediate commute planning)
  👉 +3 Hours (Outdoor exercise & school morning warnings)
  👉 +6 Hours (Afternoon peak photochemical ozone warning)
  👉 +12 Hours (Evening rush hour smog accumulation)
  👉 +24 Hours (Next-day public health advisory)
  👉 +48 Hours (Strategic industrial and traffic curtailment planning)


4. HOW WE DID IT (STEP-BY-STEP ARCHITECTURE)
----------------------------------------------------------------------------------------
1. MULTI-MODAL DATA HARMONIZATION:
   We combined 4 distinct data streams across 10 major CPCB monitoring stations in Delhi NCR
   (Anand Vihar, ITO, Okhla, Aya Nagar, R.K. Puram, etc.):
   - Ground In-Situ Sensors (CPCB): Real-time air quality telemetry.
   - Spaceborne Satellites (ESA Sentinel-5P TROPOMI): Earth observation satellite columns for NO2 & O3.
   - Weather NWP (ECMWF ERA5 & Open-Meteo): Temperature, wind speed, humidity, solar radiation, boundary layer height.
   - Static Geospatial GIS: Distance to major roads, railway junctions, and urban land-use densities.

2. STATE-OF-THE-ART MACHINE LEARNING ENSEMBLE:
   - LightGBM: Highly optimized gradient-boosted decision trees to capture non-linear weather thresholds.
   - PyTorch BiLSTM + Self-Attention: Deep learning sequential model that understands past temporal memory.
   - NNLS Convex Simplex Meta-Stacking: Mathematically combines predictions with zero negative bias.
   - Diurnal Photochemical Calibration: Corrects for sun angles and peak afternoon solar radiation.

3. GUARANTEED ZERO DATA LEAKAGE:
   Built with strict temporal expanding-window cross-validation, ensuring the model never cheats
   by peeking into future data.


5. HOW WE DEPLOYED IT (TECH STACK & INFRASTRUCTURE)
----------------------------------------------------------------------------------------
• FRONTEND COMMAND CENTER (Deployed on Vercel):
  - Stack: React 18, TypeScript, Vite, TailwindCSS.
  - Visuals: Interactive real-time Delhi NCR Leaflet GIS map with color-coded station pins, radar scanlines,
    and a 3D rotating atmospheric Earth globe powered by D3-Geo.
  - Live Link: https://sih26airo2fe-seven.vercel.app

• PRODUCTION BACKEND API (Deployed on Render - Singapore / Southeast Asia Region):
  - Stack: Python 3.11, FastAPI, Uvicorn, SQLite, LightGBM, Scikit-Learn.
  - Speed: Sub-10 millisecond inference response time per forecast call.
  - Endpoints: Multi-station forecasts, SHAP feature importance explainability, what-if policy simulators,
    and automated early warning alerts.
  - Live API Docs: https://sih-26-air-o2-backend.onrender.com/docs

========================================================================================
Submitted for Smart India Hackathon (SIH 2026) | Problem Statement 25178 | Team Zephr
========================================================================================
