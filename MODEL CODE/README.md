# 🤖 AIRO2 — Machine Learning & Deep Learning Model Codebase
> **SIH 2026 — Problem Statement ID: SIH 25178**  
> **Architecture:** 2-Tier Multi-Horizon Stacking Ensemble (LightGBM + PyTorch BiLSTM with Multi-Head Temporal Attention + NNLS Simplex Stacker)  
> **Pollutants:** Nitrogen Dioxide ($\text{NO}_2$) and Ground-Level Ozone ($\text{O}_3$)  
> *(Note: This directory contains strictly model code, neural network definitions, production bundles, and model documentation — zero results).*

---

## 📂 Model Code Organization by Model Type

```
MODEL CODE/
├── 📄 README.md                                                 # [YOU ARE HERE] Master Guide to Model Types & Code
│
├── 🌲 01_MACHINE_LEARNING_MODELS/                               # Tree-Based Machine Learning Models
│   ├── train_lightgbm.py                                        # LightGBM GBDT (2,500 trees, L1 Huber loss, monotonic constraints)
│   └── feature_engineering.py                                   # 58-feature extraction & cyclical sine/cos encodings
│
├── 🧠 02_DEEP_LEARNING_MODELS/                                  # Neural Network & Deep Learning Architectures
│   └── train_bilstm_attention.py                                # PyTorch BiLSTM + Multi-Head Temporal Attention + AdamW
│
├── 🔗 03_ENSEMBLE_AND_META_STACKING/                            # Ensemble Blending & Meta-Learner Code
│   └── nnls_simplex_stacking.py                                 # Non-Negative Least Squares (NNLS) simplex stacker (w_i >= 0, sum w_i = 1)
│
├── 📈 04_DIURNAL_CALIBRATION_MODEL/                             # 24-Hour Empirical Physics Calibration
│   ├── fit_diurnal_weights.py                                   # CLI fitting tool computing hour-of-day empirical transfer weights
│   └── diurnal_calibration.py                                   # Standalone diurnal calibration engine w(hour)
│
├── 🔄 05_TRAINING_PIPELINE_AND_CV/                              # Full End-to-End Orchestrator & Cross-Validation
│   ├── run_master_pipeline.py                                   # 1-Click Master Training Orchestrator across all models
│   ├── temporal_cross_validation.py                             # Blocked temporal 5-fold CV splitter (zero lookahead leakage)
│   ├── eda_analysis.py                                          # Exploratory data distribution & collinearity checks
│   ├── evaluation_metrics.py                                    # Multi-horizon metric computation (Willmott d, RMSE, MAE, R²)
│   └── shap_attribution.py                                      # TreeSHAP feature importance & driver extractor
│
├── ⚙️ 06_PRODUCTION_INFERENCE_SERVICES/                          # Production Inference Engines & Services
│   ├── model_service.py                                         # Singleton loader, 58-feature schema ordering, expm1 inverse mapping
│   ├── feature_builder.py                                       # Feature vector assembler & static station geometries
│   └── aqi_calculator.py                                        # Official CPCB National AQI sub-index calculator
│
├── 📦 07_PRODUCTION_MODEL_BUNDLES/                              # Frozen Production Models & Schemas (Without Results)
│   ├── NO2/
│   │   ├── feature_schema.json                                  # Canonical 58-feature schema & data types
│   │   ├── metadata.json                                        # Training metadata & horizons [1, 3, 6, 12, 24, 48]
│   │   └── model.pkl                                            # Phase 3 frozen ensemble production model
│   └── O3/
│       ├── feature_schema.json                                  # Canonical 58-feature schema & data types
│       ├── metadata.json                                        # Training metadata & horizons [1, 3, 6, 12, 24, 48]
│       └── model.pkl                                            # Phase 3 frozen ensemble production model
│
└── 📚 08_MODEL_DOCUMENTATION/                                   # Technical Documentation & Architecture Blueprints
    ├── MODEL_ARCHITECTURE.md                                    # Deep Stacking Ensemble Architectural Blueprint
    ├── MODEL_CONTRACT.md                                        # Strict 58-Feature Production Input/Output Contract
    ├── PHASE_3_MODEL_DEVELOPER_SPECIFICATION.md                 # Full Engineering Specification & Equations
    ├── PHASE_3_COMPLETE_MASTER_HANDOUT.md                       # Comprehensive Technical Reference Handout
    ├── PHASE_3_SUDHITH_IMPLEMENTATION_PLAN.md                   # Training Roadmap & Hyperparameter Configuration
    ├── PHASE_3_TO_PHASE_4_HANDOFF_REQUIREMENTS.md               # 54-Section Production Model Handoff Standards
    └── PHASE_3_PIPELINE_GUIDE.md                                # Step-by-Step Training & Inference Guide
```

---

## 🔬 Deep Dive: The Models We Used

### 1. 🌲 Machine Learning Models (`01_MACHINE_LEARNING_MODELS/`)
* **Algorithm:** LightGBM (Light Gradient Boosting Machine)
* **Code:** [`01_MACHINE_LEARNING_MODELS/train_lightgbm.py`](file:///c:/Users/saisu/OneDrive/Desktop/SIH%202026/PROJECT-AIRO2/MODEL%20CODE/01_MACHINE_LEARNING_MODELS/train_lightgbm.py)
* **Key Mechanisms:**
  * 2,500 gradient-boosted trees per horizon model.
  * Huber L1 Loss for robustness against extreme winter smog outliers.
  * Feature subsampling ($0.8$) and column subsampling by tree ($0.8$).
  * Monotonic constraints enforced on Planetary Boundary Layer Height and Ventilation Coefficient.

### 2. 🧠 Deep Learning Models (`02_DEEP_LEARNING_MODELS/`)
* **Algorithm:** Bidirectional LSTM with Multi-Head Temporal Attention (PyTorch)
* **Code:** [`02_DEEP_LEARNING_MODELS/train_bilstm_attention.py`](file:///c:/Users/saisu/OneDrive/Desktop/SIH%202026/PROJECT-AIRO2/MODEL%20CODE/02_DEEP_LEARNING_MODELS/train_bilstm_attention.py)
* **Key Mechanisms:**
  * Multi-layer BiLSTM processing 24-hour trailing sequential input windows.
  * Custom `TemporalAttention` module attending dynamically to peak photolysis (12:00–15:00) and nocturnal inversion hours (02:00–06:00).
  * Trained with AdamW optimizer and Cosine Annealing learning rate schedule.

### 3. 🔗 Ensemble & Meta-Stacking (`03_ENSEMBLE_AND_META_STACKING/`)
* **Algorithm:** Non-Negative Least Squares (NNLS) Simplex Meta-Learner
* **Code:** [`03_ENSEMBLE_AND_META_STACKING/nnls_simplex_stacking.py`](file:///c:/Users/saisu/OneDrive/Desktop/SIH%202026/PROJECT-AIRO2/MODEL%20CODE/03_ENSEMBLE_AND_META_STACKING/nnls_simplex_stacking.py)
* **Key Mechanisms:**
  * Blends out-of-fold predictions from LightGBM and Deep BiLSTM.
  * Enforces convex probability simplex constraints ($\sum w_i = 1, w_i \ge 0$) to guarantee physical plausibility and prevent overconfidence.

### 4. 📈 Diurnal Calibration Model (`04_DIURNAL_CALIBRATION_MODEL/`)
* **Algorithm:** 24-Hour Empirical Ratio Transfer Model
* **Code:** [`04_DIURNAL_CALIBRATION_MODEL/diurnal_calibration.py`](file:///c:/Users/saisu/OneDrive/Desktop/SIH%202026/PROJECT-AIRO2/MODEL%20CODE/04_DIURNAL_CALIBRATION_MODEL/diurnal_calibration.py)
* **Key Mechanisms:**
  * Calibrates spaceborne CAMS satellite inputs into ground-truth CPCB equivalents using hour-of-day transfer function $w(h) = \mathbb{E}[\text{CPCB}\mid h] / \mathbb{E}[\text{CAMS}\mid h]$.
