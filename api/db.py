"""
DuckDB connection and Parquet-backed prediction store.

Design rules:
- One DuckDB connection per process (singleton), opened once at startup.
- Models are NEVER loaded here. This module reads pre-computed Parquet only.
- Response caching is handled by fastapi-cache2 at the router level.
"""

from __future__ import annotations

import os
import pathlib
import duckdb
from typing import Optional

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

BASE_DIR = pathlib.Path(__file__).parent
FIXTURES_DIR = BASE_DIR / "fixtures"

PREDICTIONS_PARQUET = pathlib.Path(
    os.getenv("PREDICTIONS_PARQUET", str(FIXTURES_DIR / "predictions.parquet"))
)
STATIONS_PARQUET = pathlib.Path(
    os.getenv("STATIONS_PARQUET", str(FIXTURES_DIR / "stations.parquet"))
)
HOTSPOTS_GEOJSON = pathlib.Path(
    os.getenv("HOTSPOTS_GEOJSON", str(FIXTURES_DIR / "hotspots.geojson"))
)
VALIDATION_PARQUET = pathlib.Path(
    os.getenv("VALIDATION_PARQUET", str(FIXTURES_DIR / "validation.parquet"))
)

# ---------------------------------------------------------------------------
# Singleton connection
# ---------------------------------------------------------------------------

_conn: Optional[duckdb.DuckDBPyConnection] = None


def get_connection() -> duckdb.DuckDBPyConnection:
    """Return the process-wide DuckDB connection, creating it on first call."""
    global _conn
    if _conn is None:
        _conn = duckdb.connect(database=":memory:", read_only=False)
        _register_views()
    return _conn


def _register_views() -> None:
    """Register Parquet files as DuckDB views so queries work naturally."""
    conn = _conn
    assert conn is not None

    if PREDICTIONS_PARQUET.exists():
        conn.execute(
            f"CREATE OR REPLACE VIEW predictions AS SELECT * FROM read_parquet('{PREDICTIONS_PARQUET}')"
        )
    else:
        # Schema stub so routers can query even before fixtures are generated
        conn.execute("""
            CREATE OR REPLACE TABLE predictions (
                grid_row    INTEGER,
                grid_col    INTEGER,
                lat         DOUBLE,
                lon         DOUBLE,
                date        DATE,
                coverage    VARCHAR,
                pm25        DOUBLE,
                pm10        DOUBLE,
                no2         DOUBLE,
                so2         DOUBLE,
                co          DOUBLE,
                o3          DOUBLE,
                pm25_ci_low  DOUBLE,
                pm25_ci_high DOUBLE,
                pm10_ci_low  DOUBLE,
                pm10_ci_high DOUBLE,
                no2_ci_low   DOUBLE,
                no2_ci_high  DOUBLE,
                so2_ci_low   DOUBLE,
                so2_ci_high  DOUBLE,
                co_ci_low    DOUBLE,
                co_ci_high   DOUBLE,
                o3_ci_low    DOUBLE,
                o3_ci_high   DOUBLE,
                hcho_column  DOUBLE
            )
        """)

    if STATIONS_PARQUET.exists():
        conn.execute(
            f"CREATE OR REPLACE VIEW stations AS SELECT * FROM read_parquet('{STATIONS_PARQUET}')"
        )
    else:
        conn.execute("""
            CREATE OR REPLACE TABLE stations (
                station_id      VARCHAR,
                name            VARCHAR,
                lat             DOUBLE,
                lon             DOUBLE,
                date            DATE,
                observed_aqi    INTEGER,
                predicted_aqi   INTEGER
            )
        """)

    if VALIDATION_PARQUET.exists():
        conn.execute(
            f"CREATE OR REPLACE VIEW validation_data AS SELECT * FROM read_parquet('{VALIDATION_PARQUET}')"
        )
    else:
        conn.execute("""
            CREATE OR REPLACE TABLE validation_data (
                pollutant       VARCHAR,
                observed        DOUBLE,
                predicted       DOUBLE,
                station_id      VARCHAR,
                date            DATE
            )
        """)


def close_connection() -> None:
    """Close the DuckDB connection (called on app shutdown)."""
    global _conn
    if _conn is not None:
        _conn.close()
        _conn = None


# ---------------------------------------------------------------------------
# Geo helpers
# ---------------------------------------------------------------------------

def nearest_grid_cell(lat: float, lon: float, conn: duckdb.DuckDBPyConnection):
    """
    Return the (grid_row, grid_col, cell_lat, cell_lon) of the nearest grid cell
    using simple Euclidean distance on lat/lon (sufficient for ~10 km cells).
    """
    result = conn.execute("""
        SELECT DISTINCT grid_row, grid_col, lat, lon,
               (lat - ?)*(lat - ?) + (lon - ?)*(lon - ?) AS dist2
        FROM predictions
        ORDER BY dist2
        LIMIT 1
    """, [lat, lat, lon, lon]).fetchone()
    return result
