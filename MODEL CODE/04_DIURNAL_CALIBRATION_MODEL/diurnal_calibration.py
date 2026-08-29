"""
diurnal_calibration.py - Empirical 24-Hour Diurnal Transfer Calibration Module.

Resolves Copernicus CAMS midday Ozone photolysis overshoot (+69 ug/m3) and NO2 mean bias
against CPCB ground monitors across the 24-hour solar cycle.
Reference: docs/LIVE_DATA_DIURNAL_CALIBRATION_CHANGES.md (Claude Code Architectural Decision).
"""

from typing import Optional, Tuple
import datetime

# 24-Hour Empirical Weight Vector w(h) = E[CPCB | hour=h] / E[CAMS | hour=h] in UTC
# Hours 00 to 23 UTC (Indian Standard Time = UTC + 5:30)
# 00:00 to 07:00 UTC (05:30 to 12:30 IST): Morning buildup to midday photolysis peak
# 08:00 to 15:00 UTC (13:30 to 20:30 IST): Afternoon photochemical decay
# 16:00 to 23:00 UTC (21:30 to 04:30 IST): Nocturnal atmospheric boundary layer phase
DIURNAL_O3_WEIGHTS_UTC = [
    0.61, 0.64, 0.66, 0.58, 0.42, 0.29, 0.21, 0.18,  # 00:00 - 07:00 UTC (Midday titration dip ~0.18 at 07:00 UTC)
    0.19, 0.24, 0.32, 0.41, 0.49, 0.53, 0.56, 0.59,  # 08:00 - 15:00 UTC (Afternoon recovery)
    0.60, 0.62, 0.63, 0.64, 0.65, 0.63, 0.62, 0.61   # 16:00 - 23:00 UTC (Nighttime baseline)
]

# NO2 flat mean bias correction factor (CAMS mean 44.3 vs CPCB mean 42.8 -> 42.8 / 44.3 ~= 0.96)
# Kept as scalar because NO2 correlation r=0.206 is weakly diurnal, avoiding fitting noise.
NO2_MEAN_BIAS_CORRECTION = 0.96


def calibrate_o3(raw_cams_o3: float, target_hour_utc: Optional[int] = None) -> float:
    """
    Calibrates instantaneous CAMS Ozone using the 24-hour diurnal transfer function.
    
    Args:
        raw_cams_o3: Raw ground Ozone concentration from CAMS (ug/m3).
        target_hour_utc: Target UTC hour (0-23). If None, defaults to current UTC hour.
        
    Returns:
        Calibrated ground Ozone concentration (ug/m3).
    """
    if raw_cams_o3 is None:
        return 28.0
    
    if target_hour_utc is None:
        target_hour_utc = datetime.datetime.now(datetime.timezone.utc).hour
    
    hour_idx = int(target_hour_utc) % 24
    weight = DIURNAL_O3_WEIGHTS_UTC[hour_idx]
    
    # Apply diurnal weight and ensure non-negative physical bound
    calibrated = round(max(0.0, float(raw_cams_o3) * weight), 2)
    return calibrated


def calibrate_no2(raw_cams_no2: float) -> float:
    """
    Calibrates instantaneous CAMS NO2 using the mean bias correction factor.
    
    Args:
        raw_cams_no2: Raw ground NO2 concentration from CAMS (ug/m3).
        
    Returns:
        Calibrated ground NO2 concentration (ug/m3).
    """
    if raw_cams_no2 is None:
        return 35.0
    
    calibrated = round(max(0.0, float(raw_cams_no2) * NO2_MEAN_BIAS_CORRECTION), 2)
    return calibrated


def calibrate_cams_chemistry(
    raw_cams_o3: float, 
    raw_cams_no2: float, 
    target_hour_utc: Optional[int] = None
) -> Tuple[float, float]:
    """
    Calibrates both CAMS Ozone and NO2 simultaneously.
    
    Returns:
        (calibrated_o3, calibrated_no2) tuple.
    """
    cal_o3 = calibrate_o3(raw_cams_o3, target_hour_utc)
    cal_no2 = calibrate_no2(raw_cams_no2)
    return cal_o3, cal_no2
