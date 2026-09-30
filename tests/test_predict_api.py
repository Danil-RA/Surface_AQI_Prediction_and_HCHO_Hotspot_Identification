import pytest
from fastapi.testclient import TestClient
from unittest import mock

from api.main import app
from api.services import MissingDataError
from api.services.model_service import ModelServiceError

client = TestClient(app)

def test_predict_validation_errors():
    print("--- TESTING API ENDPOINT (PHASE 4) ---")
    
    # 1. Invalid latitude
    resp = client.post("/api/predict", json={
        "latitude": 150.0,  # Invalid
        "longitude": 76.0,
        "date": "2026-03-15"
    })
    assert resp.status_code == 422, "Failed to reject invalid latitude"
    
    # 2. Invalid longitude
    resp = client.post("/api/predict", json={
        "latitude": 8.0,
        "longitude": 200.0, # Invalid
        "date": "2026-03-15"
    })
    assert resp.status_code == 422, "Failed to reject invalid longitude"
    
    # 3. Invalid date
    resp = client.post("/api/predict", json={
        "latitude": 8.0,
        "longitude": 76.0,
        "date": "not-a-date"
    })
    assert resp.status_code == 422, "Failed to reject invalid date"
    print("  [OK] Request validation handles invalid inputs correctly.")

def test_predict_missing_data(monkeypatch):
    # Mock get_features to raise MissingDataError
    def mock_get_features(*args, **kwargs):
        raise MissingDataError("AOD", "GEE", "Missing satellite data")
        
    monkeypatch.setattr("api.routers.predict.get_features", mock_get_features)
    
    resp = client.post("/api/predict", json={
        "latitude": 8.523,
        "longitude": 76.941,
        "date": "2026-03-15"
    })
    
    assert resp.status_code == 422
    assert "Environmental data unavailable" in resp.json()["detail"]
    print("  [OK] Missing environmental data returns 422 cleanly.")

def test_predict_model_error(monkeypatch):
    def mock_get_features(*args, **kwargs):
        return {"fake": "feature"}
        
    def mock_predict_pollutants(*args, **kwargs):
        raise ModelServiceError("Model failed")
        
    monkeypatch.setattr("api.routers.predict.get_features", mock_get_features)
    monkeypatch.setattr("api.routers.predict.predict_pollutants", mock_predict_pollutants)
    
    resp = client.post("/api/predict", json={
        "latitude": 8.523,
        "longitude": 76.941,
        "date": "2026-03-15"
    })
    
    assert resp.status_code == 500
    assert "Internal server error during model inference" in resp.json()["detail"]
    print("  [OK] Model service failures return 500 without leaking stack traces.")

def test_predict_aqi_error(monkeypatch):
    def mock_get_features(*args, **kwargs):
        return {"fake": "feature"}
        
    def mock_predict_pollutants(*args, **kwargs):
        return {"PM2.5": -10} # Negative, will cause AQI failure
        
    def mock_calculate_aqi(*args, **kwargs):
        raise ValueError("No valid sub-indices")
        
    monkeypatch.setattr("api.routers.predict.get_features", mock_get_features)
    monkeypatch.setattr("api.routers.predict.predict_pollutants", mock_predict_pollutants)
    monkeypatch.setattr("api.routers.predict.calculate_aqi_from_predictions", mock_calculate_aqi)
    
    resp = client.post("/api/predict", json={
        "latitude": 8.523,
        "longitude": 76.941,
        "date": "2026-03-15"
    })
    
    assert resp.status_code == 500
    assert "Internal server error during AQI calculation" in resp.json()["detail"]
    print("  [OK] AQI service failures return 500.")

def test_successful_pipeline_with_fixture(monkeypatch):
    """
    INTERNAL SOFTWARE INTEGRATION TEST
    This test verifies that the API orchestrates the pipeline correctly 
    using a fixture instead of actual GEE data.
    """
    # 1. Mock get_features to return a complete 23-feature dictionary (mimicking Phase 1)
    import math
    def mock_get_features(lat, lon, date_str):
        return {
            "AOD": 0.5, "NO2": 0.0001, "SO2": 0.0002, "CO": 0.03, "O3": 0.1, "HCHO": 0.00005,
            "AT (°C)": 28.5, "RH (%)": 75.0, "WS (m/s)": 3.2, "WD (deg)": 180.0,
            "TOT-RF (mm)": 0.0, "SR (W/mt2)": 200.0, "BP (mmHg)": 760.0, "VWS (m/s)": 1.5,
            "Latitude": lat, "Longitude": lon, "Month": 3, "DayOfWeek": 6, "DayOfYear": 74,
            "AOD_RH_ratio": 0.5 / 75.0,
            "U_Wind": -3.2 * math.sin(math.radians(180.0)),
            "V_Wind": -3.2 * math.cos(math.radians(180.0)),
            "Temp_Pressure_Ratio": (28.5 + 273.15) / 760.0
        }
    monkeypatch.setattr("api.routers.predict.get_features", mock_get_features)
    
    print("\n  Executing INTERNAL SOFTWARE INTEGRATION TEST (Fixture Data)...")
    
    # We do NOT mock model inference or AQI calculation, so it executes the real services
    resp = client.post("/api/predict", json={
        "latitude": 8.523,
        "longitude": 76.941,
        "date": "2026-03-15"
    })
    
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    
    data = resp.json()
    
    # Verify response schema
    assert "location" in data
    assert data["location"]["latitude"] == 8.523
    assert data["date"] == "2026-03-15"
    assert "predictions" in data
    assert "PM2.5" in data["predictions"]
    assert "aqi" in data
    assert "value" in data["aqi"]
    assert "dominant_pollutant" in data
    assert "sub_indices" in data
    assert "provenance" in data
    
    print(f"  [OK] Full pipeline orchestration successful (Status: {resp.status_code}).")
    print("  Integration Schema Validated. Sample response:")
    import json
    print(json.dumps(data, indent=2))
