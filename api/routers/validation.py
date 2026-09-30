"""
GET /api/validation

Returns all data needed for the validation page:
- Overall metrics (R², RMSE, MAE, n)
- Per-pollutant metrics
- Leave-one-station-out results (sorted worst-first by default)
- Scatter points (observed vs predicted)
- AQI category confusion matrix
"""

from __future__ import annotations

import math
from collections import defaultdict
from typing import Optional

from fastapi import APIRouter
from fastapi_cache.decorator import cache
from pydantic import BaseModel

from api.aqi.breakpoints import get_category, compute_aqi
from api.db import get_connection

router = APIRouter()

# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------

class Metrics(BaseModel):
    r2: float
    rmse: float
    mae: float
    n: int


class PollutantMetrics(BaseModel):
    pollutant: str
    r2: float
    rmse: float
    mae: float
    n: int


class LeaveOneOut(BaseModel):
    station_id: str
    name: str
    r2: float
    rmse: float
    n: int


class ScatterPoint(BaseModel):
    observed: float
    predicted: float
    pollutant: str


class ValidationResponse(BaseModel):
    overall: Metrics
    per_pollutant: list[PollutantMetrics]
    leave_one_station_out: list[LeaveOneOut]  # sorted worst-first (lowest r2)
    scatter: list[ScatterPoint]
    category_confusion: dict  # {"labels": [...], "matrix": [[...]]}


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------

@router.get("/validation", response_model=ValidationResponse)
@cache(expire=3600)
async def get_validation():
    conn = get_connection()

    rows = conn.execute("""
        SELECT pollutant, observed, predicted, station_id
        FROM validation_data
        WHERE observed IS NOT NULL AND predicted IS NOT NULL
    """).fetchall()

    if not rows:
        return _empty_response()

    # Organise by pollutant and station
    by_pollutant: dict[str, list[tuple[float, float]]] = defaultdict(list)
    by_station: dict[str, list[tuple[float, float]]] = defaultdict(list)
    all_pairs: list[tuple[float, float]] = []
    station_names: dict[str, str] = {}

    for pollutant, obs, pred, sid in rows:
        by_pollutant[pollutant].append((obs, pred))
        by_station[sid].append((obs, pred))
        all_pairs.append((obs, pred))

    # Station names (join from stations table if available)
    sname_rows = conn.execute("SELECT DISTINCT station_id, name FROM stations").fetchall()
    for sid, name in sname_rows:
        station_names[sid] = name

    # Metrics
    overall = _metrics(all_pairs)

    per_pollutant = [
        PollutantMetrics(pollutant=p, **_metrics(pairs).__dict__)
        for p, pairs in sorted(by_pollutant.items())
    ]

    loo = [
        LeaveOneOut(
            station_id=sid,
            name=station_names.get(sid, sid),
            **_metrics(pairs).__dict__,
        )
        for sid, pairs in by_station.items()
    ]
    # Worst-first (lowest r2 first)
    loo.sort(key=lambda x: x.r2)

    scatter = [
        ScatterPoint(observed=o, predicted=p, pollutant=pol)
        for pol, pairs in by_pollutant.items()
        for o, p in pairs
    ]

    # AQI category confusion matrix
    confusion = _category_confusion(rows)

    return ValidationResponse(
        overall=overall,
        per_pollutant=per_pollutant,
        leave_one_station_out=loo,
        scatter=scatter,
        category_confusion=confusion,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _metrics(pairs: list[tuple[float, float]]) -> Metrics:
    n = len(pairs)
    if n == 0:
        return Metrics(r2=0.0, rmse=0.0, mae=0.0, n=0)

    obs = [p[0] for p in pairs]
    pred = [p[1] for p in pairs]
    mean_obs = sum(obs) / n

    ss_res = sum((o - p) ** 2 for o, p in pairs)
    ss_tot = sum((o - mean_obs) ** 2 for o in obs)
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0
    rmse = math.sqrt(ss_res / n)
    mae = sum(abs(o - p) for o, p in pairs) / n

    return Metrics(r2=round(r2, 4), rmse=round(rmse, 2), mae=round(mae, 2), n=n)


def _category_confusion(rows) -> dict:
    """Build confusion matrix for CPCB AQI categories."""
    from api.aqi.breakpoints import CATEGORIES

    labels = [c.name for c in CATEGORIES]
    label_idx = {c.name: i for i, c in enumerate(CATEGORIES)}
    n = len(labels)
    matrix = [[0] * n for _ in range(n)]

    for _, obs, pred, _ in rows:
        obs_cat = get_category(round(obs)).name
        pred_cat = get_category(round(pred)).name
        if obs_cat in label_idx and pred_cat in label_idx:
            matrix[label_idx[obs_cat]][label_idx[pred_cat]] += 1

    return {"labels": labels, "matrix": matrix}


def _empty_response() -> ValidationResponse:
    return ValidationResponse(
        overall=Metrics(r2=0.0, rmse=0.0, mae=0.0, n=0),
        per_pollutant=[],
        leave_one_station_out=[],
        scatter=[],
        category_confusion={"labels": [], "matrix": []},
    )
