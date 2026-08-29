"""
config.py - Path configuration for the AIRO2 FastAPI backend.
Resolves all model artifact paths relative to the project root.
"""
import os

# Project root is 2 levels above this file: backend/app/config.py -> backend/app -> backend -> root
_HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))

# Production model artifact paths (canonical location per handoff doc Section 7)
MODEL_NO2_PATH          = os.path.join(PROJECT_ROOT, "models", "NO2", "model.pkl")
MODEL_O3_PATH           = os.path.join(PROJECT_ROOT, "models", "O3",  "model.pkl")
MODEL_NO2_SCHEMA_PATH   = os.path.join(PROJECT_ROOT, "models", "NO2", "feature_schema.json")
MODEL_O3_SCHEMA_PATH    = os.path.join(PROJECT_ROOT, "models", "O3",  "feature_schema.json")
MODEL_NO2_METADATA_PATH = os.path.join(PROJECT_ROOT, "models", "NO2", "metadata.json")
MODEL_O3_METADATA_PATH  = os.path.join(PROJECT_ROOT, "models", "O3",  "metadata.json")

# SHAP attribution files
SHAP_NO2_CSV = os.path.join(PROJECT_ROOT, "results", "figures", "shap_top10_NO2.csv")
SHAP_O3_CSV  = os.path.join(PROJECT_ROOT, "results", "figures", "shap_top10_O3.csv")

# Golden reference paths
GOLDEN_001_INPUT  = os.path.join(PROJECT_ROOT, "integration_test", "GOLDEN_001", "input.json")
GOLDEN_001_OUTPUT = os.path.join(PROJECT_ROOT, "integration_test", "GOLDEN_001", "expected_output.json")

API_VERSION   = "v1"
MODEL_VERSION = "1.0.0"

# Forecast horizons (direct multi-step — per handoff doc Section 4)
FORECAST_HORIZONS = [1, 3, 6, 12, 24, 48]

# Supported pollutants
POLLUTANTS = ["NO2", "O3"]

# Station canonical encoding for BiLSTM station embeddings (handoff doc Section 20)
STATION_ENCODING = {
    "ANAND_VIHAR":         0,
    "ITO":                 1,
    "OKHLA_PHASE_2":       2,
    "AYA_NAGAR":           3,
    "RK_PURAM":            4,
    "DHYAN_CHAND_STADIUM": 5,
    "MANDIR_MARG":         6,
    "PUNJABI_BAGH":        7,
    "JAHANGIRPURI":        8,
    "DWARKA_SECTOR_8":     9,
}
