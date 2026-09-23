"""
GET /api/hotspots?season=winter|premonsoon|monsoon|postmonsoon&year=

Serves pre-computed HCHO hotspot GeoJSON (simplified server-side).
GeoJSON geometry simplification is done offline — this router only reads
the stored file. If the payload exceeds a few MB, re-simplify offline.
"""

from __future__ import annotations

import json
import pathlib

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from fastapi_cache.decorator import cache

from api.db import HOTSPOTS_GEOJSON

router = APIRouter()

SEASONS = frozenset(["winter", "premonsoon", "monsoon", "postmonsoon"])


@router.get("/hotspots")
@cache(expire=600)
async def get_hotspots(
    season: str = Query("winter", description="winter|premonsoon|monsoon|postmonsoon"),
    year: int = Query(2023),
):
    if season not in SEASONS:
        raise HTTPException(status_code=400, detail=f"season must be one of {sorted(SEASONS)}")

    # Per-season files: hotspots_winter_2023.geojson, etc.
    season_file = HOTSPOTS_GEOJSON.parent / f"hotspots_{season}_{year}.geojson"
    if not season_file.exists():
        # Fall back to the generic fixture
        if HOTSPOTS_GEOJSON.exists():
            season_file = HOTSPOTS_GEOJSON
        else:
            return JSONResponse({"type": "FeatureCollection", "features": []})

    with open(season_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    return JSONResponse(data)
