"""
forecast.py - Pydantic schemas for the forecast API response.

Per handoff doc:
  - Section 5:  exactly 6 horizons: 1, 3, 6, 12, 24, 48
  - Section 6:  NOT 48 hourly points — exactly 6 checkpoints
  - Section 17: unit is always 'ug/m3'
  - Section 34: ForecastResponse shape
  - Section 36: every prediction must include forecast_generated_at + target_timestamp
  - Section 54: one station = 12 predictions (2 pollutants x 6 horizons)
"""

from pydantic import BaseModel, Field
from typing import Optional


class ModelInfo(BaseModel):
    name:                  str
    version:               str
    feature_schema_version: str
    feature_count:         int = Field(58, description="Always 58 production features")
    native_unit:           str = Field("ug/m3", description="Model native output unit")
    architecture:          list[str] = Field(
        default=["LightGBM", "BiLSTM+Attention", "NNLS"],
        description="Phase 3 ensemble components"
    )


class HorizonPrediction(BaseModel):
    horizon_hours:    int
    target_timestamp: str
    prediction:       Optional[float] = Field(
        None, description="Forecast value in ug/m3. None if inference failed."
    )
    unit:             str = "ug/m3"
    aqi:              Optional[int]   = None
    aqi_category:     Optional[str]   = None
    aqi_color:        Optional[str]   = None


class ForecastResponse(BaseModel):
    """
    Complete forecast response for one station.
    Contains 12 predictions: 2 pollutants x 6 horizons.
    Per handoff doc Section 34 and Section 54.
    """
    station_id:         str
    generated_at:       str
    model:              ModelInfo
    forecasts:          dict[str, list[HorizonPrediction]]
    data_mode:          str = "historical"
    is_live:            bool = False
    ground_chem_source: str = "HISTORICAL_FUSED"
    note:               str = (
        "Six discrete forecast checkpoints: +1h, +3h, +6h, +12h, +24h, +48h. "
        "Predictions are model outputs, not observational data. "
        "48h predictions have lower accuracy than 1h predictions."
    )


class HealthResponse(BaseModel):
    status:   str
    database: str = "n/a"
    models:   dict[str, str]


class ModelInfoFull(BaseModel):
    model_name:       str
    pollutants:       list[str]
    horizons_hours:   list[int]
    feature_count:    int
    native_unit:      str
    architecture:     list[str]
    model_version:    str
    training_period:  str
    validation_period: str
    test_period:      str
    performance_NO2:  Optional[dict] = None
    performance_O3:   Optional[dict] = None
