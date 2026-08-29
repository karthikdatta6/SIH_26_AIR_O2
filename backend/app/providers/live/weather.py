"""
backend/app/providers/live/weather.py
Weather client wrapping live ECMWF numerical weather prediction.
"""
from LIVE_DATA.live_weather_service import fetch_live_weather


class WeatherClient:
    def fetch(self, latitude: float, longitude: float) -> dict:
        return fetch_live_weather(latitude=latitude, longitude=longitude)
