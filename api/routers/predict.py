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

@router.post("/predict", response_model=PredictResponse)
async def predict(request: PredictRequest):
    lat = request.latitude
    lon = request.longitude
    date_str = request.date.isoformat()
    
    # Step 1: Feature acquisition
    try:
        # Phase 1: get_features handles GEE, ERA5, and VWS internally
        features = get_features(lat, lon, date_str)
    except MissingDataError as e:
        # Return 422 Unprocessable Entity for missing environmental data
        raise HTTPException(status_code=422, detail=f"Environmental data unavailable: {str(e)}")
    except Exception as e:
        # Avoid exposing stack traces
        raise HTTPException(status_code=500, detail="Internal server error during feature acquisition")

    # Step 2: Model inference
    try:
        # Phase 2: prediction service (singleton internally loaded)
        predictions = predict_pollutants(features)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error during model inference")

    # Step 3: AQI calculation
    try:
        # Phase 3: AQI wrapper connecting predictions to CPCB logic
        aqi_result = calculate_aqi_from_predictions(predictions)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error during AQI calculation")

    # As the Phase 1 feature service currently does not bubble up provenance metadata
    # for the synthetic VWS fallback, we document it explicitly here.
    provenance = {
        "vws": {
            "source": "synthetic_fallback"
        }
    }

    return PredictResponse(
        location=Location(latitude=lat, longitude=lon),
        date=date_str,
        predictions=predictions,
        aqi=AQIDetails(value=aqi_result["overall_aqi"], category=aqi_result["category"]),
        dominant_pollutant=aqi_result["dominant_pollutant"],
        sub_indices=aqi_result["sub_indices"],
        provenance=provenance
    )
