"""
GET /api/grid?date=YYYY-MM-DD&variable=aqi|pm25|pm10|no2|so2|co|o3|hcho

Returns GeoJSON FeatureCollection of grid cells or points for the given date.
Includes computed AQI (using server-side breakpoints) and CPCB category.
Frontend never calculates AQI.
"""

from datetime import date
from typing import Optional

from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import JSONResponse
from fastapi_cache.decorator import cache

from api.aqi.breakpoints import compute_aqi, get_category
from api.db import get_connection

router = APIRouter()

@router.get("/grid")
@cache(expire=600)
async def get_grid(
    date: date = Query(..., description="Date (YYYY-MM-DD)"),
    variable: str = Query("aqi", description="aqi | pm25 | pm10 | no2 | so2 | co | o3 | hcho"),
    step: int = Query(4, description="Sampling stride across grid for map rendering performance"),
):
    conn = get_connection()

    # Step down grid resolution slightly for fast geojson payload (e.g. 50x50 cells)
    rows = conn.execute("""
        SELECT grid_row, grid_col, lat, lon, coverage,
               pm25, pm10, no2, so2, co, o3, hcho_column
        FROM predictions
        WHERE date = ? AND (grid_row % ?) = 0 AND (grid_col % ?) = 0
    """, [date, step, step]).fetchall()

    if not rows:
        return JSONResponse({"type": "FeatureCollection", "features": []})

    features = []
    # Grid spans 28 degrees lat (8-36) and 28 degrees lon (68-96) over 200 cells
    # Each cell spacing is ~0.14 degrees
    delta_lat = (28.0 / 200.0) * step * 0.5
    delta_lon = (28.0 / 200.0) * step * 0.5

    for (r, c, lat, lon, cov,
         pm25, pm10, no2, so2, co, o3, hcho) in rows:

        val = None
        category_name = None
        category_color = None

        if cov != "none":
            if variable == "aqi":
                conc_map = {}
                if pm25 is not None: conc_map["PM2.5"] = pm25
                if pm10 is not None: conc_map["PM10"] = pm10
                if no2 is not None:  conc_map["NO2"] = no2
                if so2 is not None:  conc_map["SO2"] = so2
                if co is not None:   conc_map["CO"] = co
                if o3 is not None:   conc_map["O3"] = o3

                if conc_map:
                    try:
                        aqi_val, dominant, _ = compute_aqi(conc_map)
                        cat = get_category(aqi_val)
                        val = aqi_val
                        category_name = cat.name
                        category_color = cat.color
                    except ValueError:
                        cov = "none"
            elif variable == "hcho":
                val = hcho
            else:
                mapping = {"pm25": pm25, "pm10": pm10, "no2": no2, "so2": so2, "co": co, "o3": o3}
                val = mapping.get(variable)

        # Create polygon cell geometry
        geom = {
            "type": "Polygon",
            "coordinates": [[
                [round(lon - delta_lon, 4), round(lat - delta_lat, 4)],
                [round(lon + delta_lon, 4), round(lat - delta_lat, 4)],
                [round(lon + delta_lon, 4), round(lat + delta_lat, 4)],
                [round(lon - delta_lon, 4), round(lat + delta_lat, 4)],
                [round(lon - delta_lon, 4), round(lat - delta_lat, 4)],
            ]]
        }

        features.append({
            "type": "Feature",
            "geometry": geom,
            "properties": {
                "grid_row": r,
                "grid_col": c,
                "coverage": cov,
                "value": val,
                "category": category_name,
                "category_color": category_color,
            }
        })

    return JSONResponse({"type": "FeatureCollection", "features": features})
