"""
backend/tests/test_location_and_webhook_alerts.py
Automated test suite for Dynamic Location-Agnostic Ingestion & Webhook Alert Engine.
"""

import os
import sys
import pytest

# Allow import from project root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from httpx import AsyncClient, ASGITransport
from backend.app.main import app


@pytest.mark.asyncio
async def test_geocoding_major_indian_cities():
    """Verifies that geocoding works for non-Delhi Indian cities."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        cities = ["Hyderabad", "Mumbai", "Bengaluru", "Kolkata", "Chennai"]
        for city in cities:
            res = await client.get(f"/api/v1/alerts/geocode?query={city}")
            assert res.status_code == 200
            data = res.json()
            assert len(data) > 0
            assert "latitude" in data[0]
            assert "longitude" in data[0]
            assert isinstance(data[0]["latitude"], (int, float))
            assert isinstance(data[0]["longitude"], (int, float))


@pytest.mark.asyncio
async def test_custom_location_forecast():
    """Verifies that the backend can compute multi-horizon forecasts for custom GPS coordinates."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Test for Hyderabad coordinates
        lat, lon = 17.3850, 78.4867
        res = await client.get(f"/api/v1/alerts/location/forecast?lat={lat}&lon={lon}&name=Hyderabad")
        assert res.status_code == 200
        data = res.json()
        assert data["location_name"] == "Hyderabad"
        assert data["latitude"] == lat
        assert data["longitude"] == lon
        assert "current_aqi" in data
        assert "horizon_12h_no2" in data
        assert "horizon_12h_aqi" in data
        assert "recommended_action" in data
        assert data["current_blh_m"] > 0


@pytest.mark.asyncio
async def test_webhook_simulation_payload():
    """Verifies that webhook dispatcher generates a structured Discord-compatible embed."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "location_name": "Bengaluru, Karnataka",
            "latitude": 12.9716,
            "longitude": 77.5946,
            "target_horizon_hours": 12,
            "min_aqi_threshold": 50,
            "custom_recipient_note": "Test advisory note for municipal team"
        }
        res = await client.post("/api/v1/alerts/webhook/dispatch", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "success"
        assert data["webhook_type_detected"] == "simulation_mode"
        assert "payload_preview" in data
        assert "embeds" in data["payload_preview"]
        assert len(data["payload_preview"]["embeds"]) > 0
