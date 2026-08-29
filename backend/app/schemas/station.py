"""
station.py - Pydantic schemas for station data.
Per handoff doc Section 19: canonical 10 station IDs only.
Per handoff doc Section 43: one canonical station registry.
"""

from pydantic import BaseModel
from typing import Optional


class StationInfo(BaseModel):
    station_id:  str
    name:        str
    latitude:    float
    longitude:   float
    typology:    str
    road_dist_m: float


class StationResponse(StationInfo):
    current_aqi:      Optional[int]   = None
    current_no2:      Optional[float] = None
    current_o3:       Optional[float] = None
    current_category: Optional[str]   = None
    color:            Optional[str]   = None


# Canonical 10-station registry — per handoff doc Section 43
# Coordinates verified from CPCB station database
STATIONS_DATA = [
    {
        "station_id":  "ANAND_VIHAR",
        "name":        "Anand Vihar",
        "latitude":    28.6469,
        "longitude":   77.3152,
        "typology":    "Traffic + Residential",
        "road_dist_m": 12.0,
    },
    {
        "station_id":  "ITO",
        "name":        "ITO",
        "latitude":    28.6289,
        "longitude":   77.2410,
        "typology":    "Traffic",
        "road_dist_m": 8.0,
    },
    {
        "station_id":  "OKHLA_PHASE_2",
        "name":        "Okhla Phase 2",
        "latitude":    28.5355,
        "longitude":   77.2770,
        "typology":    "Industrial + Residential",
        "road_dist_m": 20.0,
    },
    {
        "station_id":  "AYA_NAGAR",
        "name":        "Aya Nagar",
        "latitude":    28.4765,
        "longitude":   77.1097,
        "typology":    "Suburban + Green",
        "road_dist_m": 45.0,
    },
    {
        "station_id":  "RK_PURAM",
        "name":        "R K Puram",
        "latitude":    28.5647,
        "longitude":   77.1816,
        "typology":    "Residential",
        "road_dist_m": 30.0,
    },
    {
        "station_id":  "DHYAN_CHAND_STADIUM",
        "name":        "Dhyan Chand National Stadium",
        "latitude":    28.6105,
        "longitude":   77.2424,
        "typology":    "Background + Park",
        "road_dist_m": 60.0,
    },
    {
        "station_id":  "MANDIR_MARG",
        "name":        "Mandir Marg",
        "latitude":    28.6394,
        "longitude":   77.1987,
        "typology":    "Commercial + Traffic",
        "road_dist_m": 15.0,
    },
    {
        "station_id":  "PUNJABI_BAGH",
        "name":        "Punjabi Bagh",
        "latitude":    28.6694,
        "longitude":   77.1314,
        "typology":    "Residential",
        "road_dist_m": 18.0,
    },
    {
        "station_id":  "JAHANGIRPURI",
        "name":        "Jahangirpuri",
        "latitude":    28.7283,
        "longitude":   77.1683,
        "typology":    "Residential + Industrial",
        "road_dist_m": 22.0,
    },
    {
        "station_id":  "DWARKA_SECTOR_8",
        "name":        "Dwarka Sector 8",
        "latitude":    28.5854,
        "longitude":   77.0584,
        "typology":    "Residential",
        "road_dist_m": 35.0,
    },
]

# Build lookup dict for O(1) station access
STATIONS_LOOKUP = {s["station_id"]: s for s in STATIONS_DATA}
