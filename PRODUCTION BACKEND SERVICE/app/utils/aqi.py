"""
aqi.py - Official CPCB National AQI Calculator
Source: Central Pollution Control Board, India — National AQI methodology.

Uses the linear sub-index formula:
    I = I_low + (I_high - I_low) / (C_high - C_low) * (C - C_low)

Per handoff doc Section 48: DO NOT invent thresholds.
Only official CPCB breakpoints are used here.

Supports:
- NO2 (24-hr avg, ug/m3)
- O3  (8-hr avg, ug/m3)
- PM2.5 (24-hr avg, ug/m3)
- PM10 (24-hr avg, ug/m3)
- CO (8-hr avg, mg/m3 or ppm converted)
- SO2 (24-hr avg, ug/m3)
- Composite Multi-Pollutant AQI calculation
"""

from typing import Optional, Dict, Any


# Official CPCB AQI Breakpoints (Format: C_low, C_high, I_low, I_high, category, color_hex)
_NO2_BREAKPOINTS = [
    (0,   40,  0,  50, "Good",       "#00e400"),
    (40,  80,  51, 100, "Satisfactory", "#92d050"),
    (80,  180, 101, 200, "Moderate",  "#ffff00"),
    (180, 280, 201, 300, "Poor",      "#ff7e00"),
    (280, 400, 301, 400, "Very Poor", "#ff0000"),
    (400, 1000, 401, 500, "Severe",   "#7e0023"),
]

_O3_BREAKPOINTS = [
    (0,   50,  0,  50, "Good",        "#00e400"),
    (50,  100, 51, 100, "Satisfactory", "#92d050"),
    (100, 168, 101, 200, "Moderate",  "#ffff00"),
    (168, 208, 201, 300, "Poor",      "#ff7e00"),
    (208, 748, 301, 400, "Very Poor", "#ff0000"),
    (748, 2000, 401, 500, "Severe",   "#7e0023"),
]

_PM25_BREAKPOINTS = [
    (0,   30,  0,  50, "Good",        "#00e400"),
    (30,  60,  51, 100, "Satisfactory", "#92d050"),
    (60,  90,  101, 200, "Moderate",  "#ffff00"),
    (90,  120, 201, 300, "Poor",      "#ff7e00"),
    (120, 250, 301, 400, "Very Poor", "#ff0000"),
    (250, 500, 401, 500, "Severe",   "#7e0023"),
]

_PM10_BREAKPOINTS = [
    (0,   50,  0,  50, "Good",        "#00e400"),
    (50,  100, 51, 100, "Satisfactory", "#92d050"),
    (100, 250, 101, 200, "Moderate",  "#ffff00"),
    (250, 350, 201, 300, "Poor",      "#ff7e00"),
    (350, 430, 301, 400, "Very Poor", "#ff0000"),
    (430, 600, 401, 500, "Severe",   "#7e0023"),
]

_CO_BREAKPOINTS = [
    (0,   1.0,  0,  50, "Good",        "#00e400"),
    (1.0, 2.0,  51, 100, "Satisfactory", "#92d050"),
    (2.0, 10.0, 101, 200, "Moderate",  "#ffff00"),
    (10.0, 17.0, 201, 300, "Poor",     "#ff7e00"),
    (17.0, 34.0, 301, 400, "Very Poor","#ff0000"),
    (34.0, 50.0, 401, 500, "Severe",   "#7e0023"),
]

_SO2_BREAKPOINTS = [
    (0,   40,  0,  50, "Good",        "#00e400"),
    (40,  80,  51, 100, "Satisfactory", "#92d050"),
    (80,  380, 101, 200, "Moderate",  "#ffff00"),
    (380, 800, 201, 300, "Poor",      "#ff7e00"),
    (800, 1600, 301, 400, "Very Poor","#ff0000"),
    (1600, 2000, 401, 500, "Severe",  "#7e0023"),
]

_BREAKPOINTS = {
    "NO2":   _NO2_BREAKPOINTS,
    "O3":    _O3_BREAKPOINTS,
    "PM2.5": _PM25_BREAKPOINTS,
    "PM10":  _PM10_BREAKPOINTS,
    "CO":    _CO_BREAKPOINTS,
    "SO2":   _SO2_BREAKPOINTS,
}

# CPCB AQI color palette
AQI_PALETTE = {
    "Good":         {"color": "#00e400", "range": "0-50"},
    "Satisfactory": {"color": "#92d050", "range": "51-100"},
    "Moderate":     {"color": "#ffff00", "range": "101-200"},
    "Poor":         {"color": "#ff7e00", "range": "201-300"},
    "Very Poor":    {"color": "#ff0000", "range": "301-400"},
    "Severe":       {"color": "#7e0023", "range": "401-500"},
}


def _linear_subindex(
    c: float,
    c_low: float, c_high: float,
    i_low: int, i_high: int,
) -> float:
    """CPCB linear sub-index interpolation."""
    if c_high == c_low:
        return float(i_low)
    return i_low + (i_high - i_low) / (c_high - c_low) * (c - c_low)


def calculate_aqi(
    pollutant: str,
    concentration_ug_m3: float,
) -> Optional[dict]:
    """
    Calculate CPCB sub-AQI for a single pollutant concentration.
    """
    clean_pol = pollutant.replace("_ground", "").strip().upper()
    if clean_pol == "PM25": clean_pol = "PM2.5"
    
    if clean_pol not in _BREAKPOINTS:
        return None
    if concentration_ug_m3 is None or concentration_ug_m3 < 0:
        return None

    breakpoints = _BREAKPOINTS[clean_pol]
    c = concentration_ug_m3

    for (c_low, c_high, i_low, i_high, category, color) in breakpoints:
        if c_low <= c <= c_high:
            aqi_val = _linear_subindex(c, c_low, c_high, i_low, i_high)
            return {
                "aqi":      int(round(aqi_val)),
                "category": category,
                "color":    color,
            }

    # Off-scale high concentration
    return {
        "aqi":      500,
        "category": "Severe",
        "color":    "#7e0023",
    }


def calculate_composite_aqi(pollutants: Dict[str, float]) -> Dict[str, Any]:
    """
    Calculates the official CPCB National Composite AQI across all available pollutants.
    AQI = max(SubIndex_1, SubIndex_2, ...)
    Prominent Pollutant is the one driving the highest sub-index.
    """
    sub_indices = {}
    max_aqi = 0
    max_cat = "Good"
    max_color = "#00e400"
    prominent_pol = "NO2"

    for pol, val in pollutants.items():
        if val is not None and val >= 0:
            res = calculate_aqi(pol, val)
            if res:
                sub_indices[pol] = res["aqi"]
                if res["aqi"] > max_aqi:
                    max_aqi = res["aqi"]
                    max_cat = res["category"]
                    max_color = res["color"]
                    prominent_pol = pol.replace("_ground", "")

    # If no pollutants gave valid AQI, default baseline
    if max_aqi == 0 and "NO2" in pollutants:
        res = calculate_aqi("NO2", pollutants["NO2"])
        if res:
            max_aqi = res["aqi"]
            max_cat = res["category"]
            max_color = res["color"]

    return {
        "composite_aqi": max_aqi,
        "category": max_cat,
        "color": max_color,
        "prominent_pollutant": prominent_pol,
        "sub_indices": sub_indices
    }
