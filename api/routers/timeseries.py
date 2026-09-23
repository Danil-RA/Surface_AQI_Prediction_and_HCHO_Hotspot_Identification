"""
GET /api/timeseries?lat=&lon=&from=&to=&variable=aqi|pm25|pm10|no2|so2|co|o3|hcho

Returns an ordered array of {date, value, ci_low, ci_high, coverage}.
Gaps (no-coverage days) are returned as entries with value=null — the chart
must break the line at these points, never interpolate across them.
"""

import datetime
from typing import Optional

from fastapi import APIRouter, Query
from fastapi_cache.decorator import cache
from pydantic import BaseModel

from api.aqi.breakpoints import compute_aqi
from api.db import get_connection, nearest_grid_cell

router = APIRouter()

VARIABLE_CHOICES = frozenset(["aqi", "pm25", "pm10", "no2", "so2", "co", "o3", "hcho"])

_VAR_TO_COLS = {
    "pm25": ("pm25", "pm25_ci_low", "pm25_ci_high"),
    "pm10": ("pm10", "pm10_ci_low", "pm10_ci_high"),
    "no2":  ("no2",  "no2_ci_low",  "no2_ci_high"),
    "so2":  ("so2",  "so2_ci_low",  "so2_ci_high"),
    "co":   ("co",   "co_ci_low",   "co_ci_high"),
    "o3":   ("o3",   "o3_ci_low",   "o3_ci_high"),
    "hcho": ("hcho_column", None, None),
}


class TimeseriesPoint(BaseModel):
    date: str
    value: Optional[float]
    ci_low: Optional[float]
    ci_high: Optional[float]
    coverage: str


@router.get("/timeseries", response_model=list[TimeseriesPoint])
@cache(expire=300)
async def get_timeseries(
    lat: float = Query(...),
    lon: float = Query(...),
    from_date: datetime.date = Query(..., alias="from"),
    to_date: datetime.date = Query(..., alias="to"),
    variable: str = Query("aqi", description="aqi | pm25 | pm10 | no2 | so2 | co | o3 | hcho"),
):
    if variable not in VARIABLE_CHOICES:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=f"variable must be one of {sorted(VARIABLE_CHOICES)}")

    conn = get_connection()
    cell = nearest_grid_cell(lat, lon, conn)
    if cell is None:
        return []

    grid_row, grid_col, *_ = cell

    rows = conn.execute("""
        SELECT date, coverage,
               pm25, pm10, no2, so2, co, o3,
               pm25_ci_low, pm25_ci_high,
               pm10_ci_low, pm10_ci_high,
               no2_ci_low,  no2_ci_high,
               so2_ci_low,  so2_ci_high,
               co_ci_low,   co_ci_high,
               o3_ci_low,   o3_ci_high,
               hcho_column
        FROM predictions
        WHERE grid_row = ? AND grid_col = ?
          AND date BETWEEN ? AND ?
        ORDER BY date
    """, [grid_row, grid_col, from_date, to_date]).fetchall()

    points: list[TimeseriesPoint] = []
    for r in rows:
        (d, cov,
         pm25, pm10, no2, so2, co, o3,
         pm25_lo, pm25_hi, pm10_lo, pm10_hi,
         no2_lo, no2_hi, so2_lo, so2_hi,
         co_lo, co_hi, o3_lo, o3_hi, hcho) = r

        if cov == "none":
            points.append(TimeseriesPoint(date=str(d), value=None, ci_low=None, ci_high=None, coverage="none"))
            continue

        if variable == "aqi":
            concs = _build_concs(pm25, pm10, no2, so2, co, o3)
            if not concs:
                points.append(TimeseriesPoint(date=str(d), value=None, ci_low=None, ci_high=None, coverage=cov))
                continue
            try:
                aqi_val, _, _ = compute_aqi(concs)
            except ValueError:
                points.append(TimeseriesPoint(date=str(d), value=None, ci_low=None, ci_high=None, coverage=cov))
                continue
            points.append(TimeseriesPoint(date=str(d), value=float(aqi_val), ci_low=None, ci_high=None, coverage=cov))

        elif variable == "hcho":
            points.append(TimeseriesPoint(date=str(d), value=hcho, ci_low=None, ci_high=None, coverage=cov))

        else:
            col_map = {
                "pm25": (pm25, pm25_lo, pm25_hi),
                "pm10": (pm10, pm10_lo, pm10_hi),
                "no2":  (no2,  no2_lo,  no2_hi),
                "so2":  (so2,  so2_lo,  so2_hi),
                "co":   (co,   co_lo,   co_hi),
                "o3":   (o3,   o3_lo,   o3_hi),
            }
            val, ci_lo, ci_hi = col_map[variable]
            points.append(TimeseriesPoint(date=str(d), value=val, ci_low=ci_lo, ci_high=ci_hi, coverage=cov))

    return points


def _build_concs(pm25, pm10, no2, so2, co, o3) -> dict[str, float]:
    m = {}
    if pm25 is not None: m["PM2.5"] = pm25
    if pm10 is not None: m["PM10"]  = pm10
    if no2  is not None: m["NO2"]   = no2
    if so2  is not None: m["SO2"]   = so2
    if co   is not None: m["CO"]    = co
    if o3   is not None: m["O3"]    = o3
    return m
