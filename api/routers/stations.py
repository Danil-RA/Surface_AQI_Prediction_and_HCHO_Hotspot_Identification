"""
GET /api/stations?date=YYYY-MM-DD

Returns all monitoring station locations with their observed AQI and the
model-predicted AQI for that date. The two values are always labelled
distinctly — predicted is never unlabelled.
"""

import datetime
from typing import Optional

from fastapi import APIRouter, Query
from fastapi_cache.decorator import cache
from pydantic import BaseModel

from api.db import get_connection

router = APIRouter()


class StationFeature(BaseModel):
    station_id: str
    name: str
    lat: float
    lon: float
    date: str
    observed_aqi: Optional[int]    # measured value from sensor — may be null if station offline
    predicted_aqi: Optional[int]   # model estimate — labelled "estimated" in UI
    bias: Optional[int]            # predicted - observed (null if either is null)


@router.get("/stations", response_model=list[StationFeature])
@cache(expire=300)
async def get_stations(
    date: datetime.date = Query(..., description="Date (YYYY-MM-DD)"),
):
    conn = get_connection()

    rows = conn.execute("""
        SELECT station_id, name, lat, lon, date,
               observed_aqi, predicted_aqi
        FROM stations
        WHERE date = ?
        ORDER BY station_id
    """, [date]).fetchall()

    result: list[StationFeature] = []
    for sid, name, lat, lon, d, obs, pred in rows:
        bias = (pred - obs) if (obs is not None and pred is not None) else None
        result.append(StationFeature(
            station_id=sid,
            name=name,
            lat=lat,
            lon=lon,
            date=str(d),
            observed_aqi=obs,
            predicted_aqi=pred,
            bias=bias,
        ))

    return result
