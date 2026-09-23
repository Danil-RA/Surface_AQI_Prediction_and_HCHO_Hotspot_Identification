"""
GET /api/aqi?lat=&lon=&date=

Returns the AQI and sub-indices for the nearest grid cell on the given date.
AQI computation is delegated entirely to aqi/breakpoints.py.
"""

import math
import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi_cache.decorator import cache
from pydantic import BaseModel

from api.aqi.breakpoints import compute_aqi, get_category
from api.db import get_connection, nearest_grid_cell

router = APIRouter()

# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------

class Concentration(BaseModel):
    value: float
    unit: str
    ci_low: float
    ci_high: float


class NearestStation(BaseModel):
    id: str
    name: str
    distance_km: float


class AQIResponse(BaseModel):
    lat: float
    lon: float
    date: str
    grid_cell: list[int]
    aqi: Optional[int]
    category: Optional[str]
    category_color: Optional[str]
    dominant_pollutant: Optional[str]
    sub_indices: dict[str, Optional[int]]
    concentrations: dict[str, Concentration]
    hcho_column: Optional[float]
    hcho_unit: str
    coverage: str
    nearest_station: Optional[NearestStation]


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------

@router.get("/aqi", response_model=AQIResponse)
@cache(expire=300)
async def get_aqi(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude"),
    date: datetime.date = Query(..., description="Date (YYYY-MM-DD)"),
):
    conn = get_connection()

    # Find nearest grid cell
    cell = nearest_grid_cell(lat, lon, conn)
    if cell is None:
        raise HTTPException(status_code=404, detail="No grid data available.")

    grid_row, grid_col, cell_lat, cell_lon, _ = cell

    # Query predictions for that cell and date
    row = conn.execute("""
        SELECT coverage, pm25, pm10, no2, so2, co, o3,
               pm25_ci_low, pm25_ci_high,
               pm10_ci_low, pm10_ci_high,
               no2_ci_low,  no2_ci_high,
               so2_ci_low,  so2_ci_high,
               co_ci_low,   co_ci_high,
               o3_ci_low,   o3_ci_high,
               hcho_column
        FROM predictions
        WHERE grid_row = ? AND grid_col = ? AND date = ?
        LIMIT 1
    """, [grid_row, grid_col, date]).fetchone()

    if row is None:
        # Date not in store → no coverage
        return AQIResponse(
            lat=cell_lat, lon=cell_lon,
            date=str(date),
            grid_cell=[grid_row, grid_col],
            aqi=None, category=None, category_color=None,
            dominant_pollutant=None,
            sub_indices={}, concentrations={},
            hcho_column=None, hcho_unit="mol/m2",
            coverage="none",
            nearest_station=None,
        )

    (coverage, pm25, pm10, no2, so2, co, o3,
     pm25_lo, pm25_hi, pm10_lo, pm10_hi,
     no2_lo, no2_hi, so2_lo, so2_hi,
     co_lo, co_hi, o3_lo, o3_hi, hcho) = row

    if coverage == "none":
        return AQIResponse(
            lat=cell_lat, lon=cell_lon,
            date=str(date),
            grid_cell=[grid_row, grid_col],
            aqi=None, category=None, category_color=None,
            dominant_pollutant=None,
            sub_indices={}, concentrations={},
            hcho_column=hcho, hcho_unit="mol/m2",
            coverage="none",
            nearest_station=None,
        )

    # Collect non-null concentrations
    conc_map: dict[str, float] = {}
    if pm25 is not None:  conc_map["PM2.5"] = pm25
    if pm10 is not None:  conc_map["PM10"]  = pm10
    if no2  is not None:  conc_map["NO2"]   = no2
    if so2  is not None:  conc_map["SO2"]   = so2
    if co   is not None:  conc_map["CO"]    = co
    if o3   is not None:  conc_map["O3"]    = o3

    if not conc_map:
        coverage = "none"
        return AQIResponse(
            lat=cell_lat, lon=cell_lon,
            date=str(date),
            grid_cell=[grid_row, grid_col],
            aqi=None, category=None, category_color=None,
            dominant_pollutant=None,
            sub_indices={}, concentrations={},
            hcho_column=hcho, hcho_unit="mol/m2",
            coverage="none",
            nearest_station=None,
        )

    aqi_val, dominant, sub_indices = compute_aqi(conc_map)
    cat = get_category(aqi_val)

    ci_map = {
        "PM2.5": (pm25_lo, pm25_hi, "ug/m3"),
        "PM10":  (pm10_lo, pm10_hi, "ug/m3"),
        "NO2":   (no2_lo,  no2_hi,  "ug/m3"),
        "SO2":   (so2_lo,  so2_hi,  "ug/m3"),
        "CO":    (co_lo,   co_hi,   "mg/m3"),
        "O3":    (o3_lo,   o3_hi,   "ug/m3"),
    }
    concentrations = {
        p: Concentration(value=v, unit=ci_map[p][2],
                         ci_low=ci_map[p][0] or v, ci_high=ci_map[p][1] or v)
        for p, v in conc_map.items()
    }

    # Find nearest station
    nearest = _nearest_station(cell_lat, cell_lon, date, conn)

    return AQIResponse(
        lat=cell_lat, lon=cell_lon,
        date=str(date),
        grid_cell=[grid_row, grid_col],
        aqi=aqi_val,
        category=cat.name,
        category_color=cat.color,
        dominant_pollutant=dominant,
        sub_indices=sub_indices,
        concentrations=concentrations,
        hcho_column=hcho,
        hcho_unit="mol/m2",
        coverage=coverage,
        nearest_station=nearest,
    )


def _nearest_station(
    lat: float, lon: float, query_date: datetime.date,
    conn,
) -> Optional[NearestStation]:
    """Return the nearest monitoring station and its distance in km."""
    row = conn.execute("""
        SELECT station_id, name, lat, lon
        FROM stations
        WHERE date = ?
        ORDER BY (lat - ?)*(lat - ?) + (lon - ?)*(lon - ?)
        LIMIT 1
    """, [query_date, lat, lat, lon, lon]).fetchone()

    if row is None:
        return None

    sid, name, slat, slon = row
    dist_km = _haversine_km(lat, lon, slat, slon)
    return NearestStation(id=sid, name=name, distance_km=round(dist_km, 1))


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
