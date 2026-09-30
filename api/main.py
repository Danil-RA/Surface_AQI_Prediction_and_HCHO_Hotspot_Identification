"""
FastAPI application entry point.

Architecture rules enforced here:
- No model loading (no joblib.load, no pickle.load) anywhere in this file or imports.
- AQI computation only via aqi/breakpoints.py.
- All data read from DuckDB/Parquet (pre-computed offline).
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend

from api.db import get_connection, close_connection
from api.routers import aqi, timeseries, hotspots, stations, validation, grid, predict


# ---------------------------------------------------------------------------
# Lifespan: open DB on startup, close on shutdown
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    get_connection()  # initialises the DuckDB singleton and registers Parquet views
    FastAPICache.init(InMemoryBackend(), prefix="aqi-cache")
    yield
    # Shutdown
    close_connection()


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Surface AQI & HCHO Hotspots API",
    description=(
        "Research API serving model-estimated ground-level AQI and HCHO hotspot data. "
        "Models are never loaded at request time; all values come from a pre-computed store."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# CORS — allow the Vite dev server and any configured production origin
# ---------------------------------------------------------------------------

ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    *[o.strip() for o in os.getenv("EXTRA_CORS_ORIGINS", "").split(",") if o.strip()],
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

app.include_router(aqi.router,        prefix="/api", tags=["AQI"])
app.include_router(grid.router,       prefix="/api", tags=["Grid"])
app.include_router(timeseries.router, prefix="/api", tags=["Timeseries"])
app.include_router(hotspots.router,   prefix="/api", tags=["Hotspots"])
app.include_router(stations.router,   prefix="/api", tags=["Stations"])
app.include_router(validation.router, prefix="/api", tags=["Validation"])
app.include_router(predict.router,    prefix="/api", tags=["Prediction"])


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@app.get("/health", tags=["Meta"])
async def health():
    return {"status": "ok"}
