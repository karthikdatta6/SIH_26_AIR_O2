🔗 LIVE WEB APP (MAIN LINK):
https://sih26airo2fe-seven.vercel.app

========================================================================================
             AIRO2 — GROUND-LEVEL OZONE (O3) & NITROGEN DIOXIDE (NO2) FORECASTING
                                SMART INDIA HACKATHON (SIH 25178)
========================================================================================


1. THE PROBLEM (HOW DANGEROUS AIR POLLUTION IS):
Air pollution in metropolitan cities like Delhi NCR is a silent public health emergency that shortens human lifespans and causes chronic asthma, severe lung damage, and heart disease. The fundamental failure of existing monitoring tools is that they only report pollution after people have already inhaled toxic air. To protect vulnerable citizens, schools, and hospitals, we urgently need an early-warning system that predicts hazardous air quality hours before it actually strikes.


2. WHY NO2 AND O3 ARE DANGEROUS:
Nitrogen Dioxide (NO2) and Ground-Level Ozone (O3) are toxic gaseous pollutants that severely inflame human respiratory airways. While NO2 is pumped directly from vehicle exhausts and thermal plants, ground-level ozone is an invisible chemical hazard "cooked" when intense sunlight heats up urban fumes, causing severe lung irritation similar to a sunburn inside your chest. Because daytime sunlight rapidly creates ozone while nighttime traffic fumes destroy it, predicting their complex, non-linear atmospheric dance requires advanced Artificial Intelligence.


3. OUR SOLUTION (AIRO2):
AIRO2 is an intelligent atmospheric forecasting system that predicts exact ground-level NO2 and O3 concentrations (in ug/m3) and official CPCB AQI categories up to 48 hours in advance across 6 discrete checkpoints (+1h, +3h, +6h, +12h, +24h, and +48h). Instead of slow recursive calculations, it delivers instant, non-recursive predictions that empower citizens to plan safe outdoor travel and help municipal authorities enforce targeted industrial and traffic curtailments ahead of severe smog episodes.


4. HOW WE DID IT (MACHINE LEARNING & FUSION):
We harmonized 4 multimodal data streams across 10 Delhi NCR CPCB stations—combining ground-level sensors, European Space Agency Sentinel-5P satellite columns, ECMWF ERA5 meteorological weather forecasts, and urban GIS road-density data. We then trained a high-performance stacked ensemble pairing LightGBM decision trees with PyTorch BiLSTM neural networks with self-attention, meta-stacked through Non-Negative Least Squares (NNLS) and calibrated with solar diurnal photochemical curves, guaranteeing sub-10ms inference with zero future data leakage.


5. HOW WE DEPLOYED IT:
Our frontend is built with React 18, TypeScript, Vite, TailwindCSS, interactive Leaflet GIS maps, and a 3D rotating Earth globe deployed globally on Vercel for instantaneous loading. The backend is an asynchronous FastAPI microservice running in Singapore on Render, serving real-time predictions, SHAP feature explainability, and automated early-warning alert webhooks.


========================================================================================
🔗 ALL PROJECT & TECHNICAL LINKS:
• Interactive Web Dashboard (Frontend) : https://sih26airo2fe-seven.vercel.app
• Live REST API & Swagger Documentation : https://sih-26-air-o2-backend.onrender.com/docs
• Health & Liveness Probe              : https://sih-26-air-o2-backend.onrender.com/healthz
• Built-in Control Center Web UI        : https://sih-26-air-o2-backend.onrender.com/static/index.html
• GitHub Source Code Repository         : https://github.com/Sudhith/SIH_26_AIR_O2
========================================================================================
