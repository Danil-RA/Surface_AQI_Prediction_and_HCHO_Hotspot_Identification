"""
GET /api/geocode?q=...

Provides server-side geocoding proxy via OpenStreetMap Nominatim.
Allows robust place search without exposing client-side API keys or triggering CORS issues.
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from typing import List, Dict, Any

from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import JSONResponse

router = APIRouter()

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"


@router.get("/geocode")
async def geocode_place(
    q: str = Query(..., min_length=1, description="Place name or address to search"),
    limit: int = Query(5, ge=1, le=10, description="Maximum number of results"),
):
    query = q.strip()
    if not query:
        return JSONResponse([])

    params = {
        "format": "json",
        "q": query,
        "limit": limit,
        "addressdetails": 1,
    }
    encoded_url = f"{NOMINATIM_URL}?{urllib.parse.urlencode(params)}"

    req = urllib.request.Request(
        encoded_url,
        headers={
            "User-Agent": "SurfaceAQI-Platform/1.0 (academic-research-aqi-platform)"
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=6) as response:
            if response.status == 200:
                raw_bytes = response.read()
                data = json.loads(raw_bytes.decode("utf-8"))
                results = []
                for item in data:
                    try:
                        results.append({
                            "display_name": item.get("display_name", ""),
                            "lat": float(item.get("lat")),
                            "lon": float(item.get("lon")),
                            "type": item.get("type", "locality"),
                            "class": item.get("class", "place"),
                        })
                    except (ValueError, TypeError):
                        continue
                return JSONResponse(results)
            else:
                return JSONResponse([])
    except Exception as e:
        # Fallback gracefully with empty list on network or rate limit issues
        return JSONResponse([], status_code=200)
