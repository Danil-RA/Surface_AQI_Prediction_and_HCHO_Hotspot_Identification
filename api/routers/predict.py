from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any
import datetime

from api.services.feature_service import get_features
from api.services.model_service import predict_pollutants
from api.services.aqi_service import calculate_aqi_from_predictions
from api.services import MissingDataError

router = APIRouter()

class Location(BaseModel):
    latitude: float
    longitude: float

class PredictRequest(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    date: datetime.date

class AQIDetails(BaseModel):
    value: int
    category: str

class PredictResponse(BaseModel):
    location: Location
    date: str
    predictions: Dict[str, float]
    aqi: AQIDetails
    dominant_pollutant: str
    sub_indices: Dict[str, int]
    provenance: Dict[str, Any]
    data_quality: str
    satellite_provenance: Dict[str, Any]

@router.post("/predict", response_model=PredictResponse)
async def predict(request: PredictRequest):
    lat = request.latitude
    lon = request.longitude
    date_str = request.date.isoformat()
    
    # Step 1: Feature acquisition
    try:
        features, sat_provenance = get_features(lat, lon, date_str)
    except MissingDataError as e:
        detail_obj = {
            "message": "Environmental data is unavailable for this location/date.",
            "missing_data": e.missing_data,
            "available_data": e.available_data
        }
        raise HTTPException(status_code=422, detail=detail_obj)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error during feature acquisition")

    # Step 2: Model inference
    try:
        predictions = predict_pollutants(features)
    except Exception as e:
        import traceback
        traceback.print_exc()
        print("Features causing error:", features)
        raise HTTPException(status_code=500, detail=f"Internal server error during model inference: {str(e)}")

    # Step 3: AQI calculation
    try:
        aqi_result = calculate_aqi_from_predictions(predictions)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error during AQI calculation")

    provenance = {
        "vws": {
            "source": "synthetic_fallback"
        }
    }
    
    # Calculate Data Quality
    quality = "HIGH"
    for k, v in sat_provenance.items():
        if v.get("source") in ("ml_gapfilled", "spatiotemporal_gapfill"):
            quality = "LIMITED"
            break
        elif v.get("source") == "temporal_recovery" and quality != "LIMITED":
            quality = "MODERATE"

    return PredictResponse(
        location=Location(latitude=lat, longitude=lon),
        date=date_str,
        predictions=predictions,
        aqi=AQIDetails(value=aqi_result["overall_aqi"], category=aqi_result["category"]),
        dominant_pollutant=aqi_result["dominant_pollutant"],
        sub_indices=aqi_result["sub_indices"],
        provenance=provenance,
        data_quality=quality,
        satellite_provenance=sat_provenance
    )
