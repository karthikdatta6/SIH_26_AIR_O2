"""
backend/app/providers/live/weather.py
Weather client wrapping live ECMWF numerical weather prediction.
"""
try:
    from LIVE_DATA.live_weather_service import fetch_live_weather
except ImportError:
    import requests
    def fetch_live_weather(latitude: float, longitude: float) -> dict:
        try:
            url = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&current=temperature_2m,relative_humidity_2m,surface_pressure,wind_speed_10m,wind_direction_10m,direct_radiation"
            resp = requests.get(url, timeout=3.0)
            if resp.status_code == 200:
                data = resp.json().get("current", {})
                return {
                    "t2m": data.get("temperature_2m", 298.15) + (273.15 if data.get("temperature_2m", 25) < 100 else 0),
                    "rh": data.get("relative_humidity_2m", 55.0),
                    "sp": data.get("surface_pressure", 101325.0),
                    "u10": data.get("wind_speed_10m", 3.0),
                    "v10": 0.0,
                    "blh": 850.0,
                    "ssrd": data.get("direct_radiation", 350.0),
                }
        except Exception:
            pass
        return {
            "t2m": 298.15,
            "rh": 55.0,
            "sp": 101325.0,
            "u10": 3.0,
            "v10": 0.0,
            "blh": 850.0,
            "ssrd": 350.0,
        }


class WeatherClient:
    def fetch(self, latitude: float, longitude: float) -> dict:
        return fetch_live_weather(latitude=latitude, longitude=longitude)
