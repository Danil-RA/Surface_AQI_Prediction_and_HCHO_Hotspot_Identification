"""
Fixture dataset generator for local development.

Generates a realistic but synthetic prediction store so the frontend can be
built and tested before real model predictions are wired in.

Grid:    ~200 × 200 cells covering a representative region
         (lat 8°–28° N, lon 68°–88° E — roughly the Indian subcontinent)
Days:    90 days ending today
Pollutants: PM2.5, PM10, NO2, SO2, CO, O3 + HCHO column
Coverage: ~15% of cell-day combinations marked as 'none' (satellite gap)

OUTPUT
------
fixtures/predictions.parquet   — main prediction store
fixtures/stations.parquet      — 30 monitoring stations
fixtures/validation.parquet    — 7 320 observed/predicted pairs
fixtures/hotspots.geojson      — 10 synthetic HCHO hotspot polygons

HOW TO DELETE
-------------
Delete this file and fixtures/*.parquet / fixtures/*.geojson, then swap in
your real prediction store at the paths configured in api/db.py (or via env
vars PREDICTIONS_PARQUET / STATIONS_PARQUET / VALIDATION_PARQUET /
HOTSPOTS_GEOJSON).
"""

from __future__ import annotations

import json
import math
import pathlib
import random
from datetime import date, timedelta

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SEED = 42
GRID_ROWS = 200
GRID_COLS = 200
DAYS = 90
NO_COVERAGE_FRACTION = 0.15  # ~15% of cell-days

LAT_MIN, LAT_MAX = 8.0, 36.0
LON_MIN, LON_MAX = 68.0, 96.0

NUM_STATIONS = 30
NUM_HOTSPOTS = 10

OUTPUT_DIR = pathlib.Path(__file__).parent

rng = np.random.default_rng(SEED)
random.seed(SEED)


# ---------------------------------------------------------------------------
# Helper: realistic spatially-correlated concentration generator
# ---------------------------------------------------------------------------

def _smooth_field(rows: int, cols: int, scale: float = 8.0) -> np.ndarray:
    """Generate smooth 2D field using multi-scale sinusoidal waves."""
    y, x = np.mgrid[0:rows, 0:cols]
    field = np.zeros((rows, cols))
    for freq in [1.0, 2.0, 4.0]:
        phase_x = rng.uniform(0, 2 * np.pi)
        phase_y = rng.uniform(0, 2 * np.pi)
        field += (1.0 / freq) * np.sin(2 * np.pi * freq * x / (cols * 0.8) + phase_x) * np.cos(2 * np.pi * freq * y / (rows * 0.8) + phase_y)
    # Indo-Gangetic Plain elevation/pollution gradient: higher towards North/Central
    gradient = np.exp(-((y - rows * 0.65) ** 2) / (2 * (rows * 0.25) ** 2)) * 1.5
    field += gradient
    # Normalise between 0.2 and 1.8
    field = (field - field.min()) / (field.max() - field.min()) * 1.6 + 0.2
    return field


def _concs(n: int, rows: int = GRID_ROWS, cols: int = GRID_COLS) -> dict[str, np.ndarray]:
    """Generate spatially correlated plausible pollutant concentration arrays."""
    field = _smooth_field(rows, cols).flatten()
    pm25 = (rng.lognormal(mean=3.6, sigma=0.4, size=n) * field).clip(5, 350)
    pm10 = (pm25 * rng.uniform(1.6, 2.2, size=n)).clip(10, 480)
    no2  = (rng.lognormal(mean=2.8, sigma=0.5, size=n) * field).clip(5, 190)
    so2  = (rng.lognormal(mean=2.2, sigma=0.5, size=n) * field).clip(2, 180)
    co   = (rng.lognormal(mean=0.6, sigma=0.4, size=n) * field).clip(0.2, 15)
    o3   = (rng.lognormal(mean=3.7, sigma=0.4, size=n) * (2.0 - field * 0.5)).clip(10, 190)
    hcho = (rng.lognormal(mean=-9.5, sigma=0.4, size=n) * field).clip(1e-6, 1e-3)
    return dict(pm25=pm25, pm10=pm10, no2=no2, so2=so2, co=co, o3=o3, hcho=hcho)


def _ci(arr: np.ndarray, frac: float = 0.20) -> tuple[np.ndarray, np.ndarray]:
    """Generate symmetric ±frac CI bounds."""
    delta = arr * frac * rng.uniform(0.5, 1.5, size=len(arr))
    return (arr - delta).clip(0), arr + delta


# ---------------------------------------------------------------------------
# 1. Predictions
# ---------------------------------------------------------------------------

def generate_predictions() -> None:
    print("Generating predictions parquet …")
    end_date = date.today()
    start_date = end_date - timedelta(days=DAYS - 1)
    dates = [start_date + timedelta(days=i) for i in range(DAYS)]

    lat_vals = np.linspace(LAT_MIN, LAT_MAX, GRID_ROWS)
    lon_vals = np.linspace(LON_MIN, LON_MAX, GRID_COLS)

    total = GRID_ROWS * GRID_COLS * DAYS
    print(f"  {total:,} total records …")

    # Build arrays cell-by-cell to keep memory manageable
    records: dict[str, list] = {
        "grid_row": [], "grid_col": [], "lat": [], "lon": [],
        "date": [], "coverage": [],
        "pm25": [], "pm10": [], "no2": [], "so2": [], "co": [], "o3": [],
        "pm25_ci_low": [], "pm25_ci_high": [],
        "pm10_ci_low": [], "pm10_ci_high": [],
        "no2_ci_low":  [], "no2_ci_high":  [],
        "so2_ci_low":  [], "so2_ci_high":  [],
        "co_ci_low":   [], "co_ci_high":   [],
        "o3_ci_low":   [], "o3_ci_high":   [],
        "hcho_column": [],
    }

    # Per-cell base concentrations give spatial coherence
    cell_base = _concs(GRID_ROWS * GRID_COLS)

    for day_i, d in enumerate(dates):
        # Day-level noise multiplier
        day_mult = rng.uniform(0.8, 1.2, size=GRID_ROWS * GRID_COLS)
        no_cov_mask = rng.random(size=GRID_ROWS * GRID_COLS) < NO_COVERAGE_FRACTION

        for flat_idx in range(GRID_ROWS * GRID_COLS):
            r = flat_idx // GRID_COLS
            c = flat_idx % GRID_COLS

            records["grid_row"].append(r)
            records["grid_col"].append(c)
            records["lat"].append(float(lat_vals[r]))
            records["lon"].append(float(lon_vals[c]))
            records["date"].append(d)

            if no_cov_mask[flat_idx]:
                records["coverage"].append("none")
                for k in ["pm25","pm10","no2","so2","co","o3",
                           "pm25_ci_low","pm25_ci_high","pm10_ci_low","pm10_ci_high",
                           "no2_ci_low","no2_ci_high","so2_ci_low","so2_ci_high",
                           "co_ci_low","co_ci_high","o3_ci_low","o3_ci_high","hcho_column"]:
                    records[k].append(None)
                continue

            m = day_mult[flat_idx]
            pm25 = float(cell_base["pm25"][flat_idx] * m)
            pm10 = float(cell_base["pm10"][flat_idx] * m)
            no2  = float(cell_base["no2"][flat_idx]  * m)
            so2  = float(cell_base["so2"][flat_idx]  * m)
            co   = float(cell_base["co"][flat_idx]   * m)
            o3   = float(cell_base["o3"][flat_idx]   * m)
            hcho = float(cell_base["hcho"][flat_idx] * m)

            def ci(v, frac=0.20):
                d_ = v * frac * float(rng.uniform(0.5, 1.5))
                return max(0.0, v - d_), v + d_

            records["coverage"].append("full")
            records["pm25"].append(pm25);  lo, hi = ci(pm25); records["pm25_ci_low"].append(lo); records["pm25_ci_high"].append(hi)
            records["pm10"].append(pm10);  lo, hi = ci(pm10); records["pm10_ci_low"].append(lo); records["pm10_ci_high"].append(hi)
            records["no2"].append(no2);    lo, hi = ci(no2);  records["no2_ci_low"].append(lo);  records["no2_ci_high"].append(hi)
            records["so2"].append(so2);    lo, hi = ci(so2);  records["so2_ci_low"].append(lo);  records["so2_ci_high"].append(hi)
            records["co"].append(co);      lo, hi = ci(co);   records["co_ci_low"].append(lo);   records["co_ci_high"].append(hi)
            records["o3"].append(o3);      lo, hi = ci(o3);   records["o3_ci_low"].append(lo);   records["o3_ci_high"].append(hi)
            records["hcho_column"].append(hcho)

    table = pa.table({
        "grid_row": pa.array(records["grid_row"], type=pa.int32()),
        "grid_col": pa.array(records["grid_col"], type=pa.int32()),
        "lat":      pa.array(records["lat"],      type=pa.float64()),
        "lon":      pa.array(records["lon"],      type=pa.float64()),
        "date":     pa.array(records["date"],     type=pa.date32()),
        "coverage": pa.array(records["coverage"], type=pa.string()),
        **{k: pa.array(records[k], type=pa.float64())
           for k in ["pm25","pm10","no2","so2","co","o3",
                      "pm25_ci_low","pm25_ci_high","pm10_ci_low","pm10_ci_high",
                      "no2_ci_low","no2_ci_high","so2_ci_low","so2_ci_high",
                      "co_ci_low","co_ci_high","o3_ci_low","o3_ci_high","hcho_column"]},
    })
    out = OUTPUT_DIR / "predictions.parquet"
    pq.write_table(table, out, compression="snappy")
    print(f"  Wrote {out} ({out.stat().st_size / 1e6:.1f} MB)")


# ---------------------------------------------------------------------------
# 2. Stations
# ---------------------------------------------------------------------------

STATIONS_METADATA = [
    ("Delhi Anand Vihar", 28.65, 77.31),
    ("Mumbai Bandra", 19.06, 72.84),
    ("Chennai Manali", 13.16, 80.26),
    ("Kolkata Jadavpur", 22.49, 88.37),
    ("Bengaluru Hebbal", 13.03, 77.59),
    ("Hyderabad Bollaram", 17.55, 78.36),
    ("Ahmedabad Satellite", 23.03, 72.52),
    ("Pune Karve Road", 18.50, 73.83),
    ("Jaipur Adarsh Nagar", 26.90, 75.83),
    ("Lucknow Talkatora", 26.83, 80.91),
    ("Kochi Ernakulam", 9.98, 76.29),
    ("Thiruvananthapuram Central", 8.49, 76.95),
    ("Bhopal TT Nagar", 23.23, 77.40),
    ("Nagpur Civil Lines", 21.15, 79.08),
    ("Indore Palasia", 22.72, 75.89),
    ("Patna Gandhi Maidan", 25.62, 85.14),
    ("Bhubaneswar Unit 3", 20.27, 85.84),
    ("Visakhapatnam Gajuwaka", 17.69, 83.21),
    ("Surat Athwa", 21.17, 72.80),
    ("Vadodara Alkapuri", 22.31, 73.18),
    ("Coimbatore Gandhipuram", 11.02, 76.96),
    ("Madurai Anna Nagar", 9.92, 78.14),
    ("Kanpur Swaroop Nagar", 26.47, 80.32),
    ("Agra Sanjay Place", 27.20, 78.01),
    ("Varanasi Ardhali Bazar", 25.35, 82.98),
    ("Amritsar Pusa Palace", 31.63, 74.87),
    ("Chandigarh Sector 22", 30.73, 76.77),
    ("Dehradun Clock Tower", 30.32, 78.04),
    ("Ranchi Booty More", 23.39, 85.37),
    ("Guwahati Pan Bazar", 26.18, 91.75),
]


def generate_stations() -> None:
    print("Generating stations parquet …")
    end_date = date.today()
    start_date = end_date - timedelta(days=DAYS - 1)
    dates = [start_date + timedelta(days=i) for i in range(DAYS)]

    station_ids = [f"ST{i+1:03d}" for i in range(len(STATIONS_METADATA))]

    rows = {
        "station_id": [], "name": [], "lat": [], "lon": [],
        "date": [], "observed_aqi": [], "predicted_aqi": [],
    }
    for d in dates:
        for i, (name, slat, slon) in enumerate(STATIONS_METADATA):
            obs = int(rng.integers(30, 350))
            pred = int(max(1, obs + rng.integers(-30, 30)))
            rows["station_id"].append(station_ids[i])
            rows["name"].append(name)
            rows["lat"].append(float(slat))
            rows["lon"].append(float(slon))
            rows["date"].append(d)
            rows["observed_aqi"].append(obs)
            rows["predicted_aqi"].append(pred)

    table = pa.table({
        "station_id":    pa.array(rows["station_id"],    type=pa.string()),
        "name":          pa.array(rows["name"],          type=pa.string()),
        "lat":           pa.array(rows["lat"],           type=pa.float64()),
        "lon":           pa.array(rows["lon"],           type=pa.float64()),
        "date":          pa.array(rows["date"],          type=pa.date32()),
        "observed_aqi":  pa.array(rows["observed_aqi"],  type=pa.int32()),
        "predicted_aqi": pa.array(rows["predicted_aqi"], type=pa.int32()),
    })
    out = OUTPUT_DIR / "stations.parquet"
    pq.write_table(table, out, compression="snappy")
    print(f"  Wrote {out} ({out.stat().st_size / 1e6:.1f} MB)")


# ---------------------------------------------------------------------------
# 3. Validation
# ---------------------------------------------------------------------------

def generate_validation() -> None:
    print("Generating validation parquet …")
    end_date = date.today()
    start_date = end_date - timedelta(days=DAYS - 1)
    dates = [start_date + timedelta(days=i) for i in range(DAYS)]

    pollutants = ["PM2.5", "PM10", "NO2", "SO2", "CO", "O3"]
    rows: dict[str, list] = {"pollutant": [], "observed": [], "predicted": [], "station_id": [], "date": []}

    for d in dates:
        for sid in [f"ST{i+1:03d}" for i in range(NUM_STATIONS)]:
            for pol in pollutants:
                obs = float(rng.lognormal(3.5, 0.7))
                pred = float(max(0.1, obs * rng.normal(1.0, 0.15)))
                rows["pollutant"].append(pol)
                rows["observed"].append(obs)
                rows["predicted"].append(pred)
                rows["station_id"].append(sid)
                rows["date"].append(d)

    table = pa.table({
        "pollutant":  pa.array(rows["pollutant"],  type=pa.string()),
        "observed":   pa.array(rows["observed"],   type=pa.float64()),
        "predicted":  pa.array(rows["predicted"],  type=pa.float64()),
        "station_id": pa.array(rows["station_id"], type=pa.string()),
        "date":       pa.array(rows["date"],       type=pa.date32()),
    })
    out = OUTPUT_DIR / "validation.parquet"
    pq.write_table(table, out, compression="snappy")
    print(f"  Wrote {out} ({out.stat().st_size / 1e6:.1f} MB)")


# ---------------------------------------------------------------------------
# 4. Hotspots GeoJSON
# ---------------------------------------------------------------------------

def _box_polygon(lat, lon, size=0.5):
    """Return a GeoJSON polygon (box) centred on lat/lon."""
    h = size / 2
    coords = [
        [lon - h, lat - h], [lon + h, lat - h],
        [lon + h, lat + h], [lon - h, lat + h],
        [lon - h, lat - h],
    ]
    return {"type": "Polygon", "coordinates": [coords]}


SEASONS = ["winter", "premonsoon", "monsoon", "postmonsoon"]
DRIVERS = ["pyrogenic", "biogenic", "mixed", "undetermined"]


def generate_hotspots() -> None:
    print("Generating hotspot GeoJSON …")
    for season in SEASONS:
        features = []
        for i in range(NUM_HOTSPOTS):
            lat = float(rng.uniform(LAT_MIN + 2, LAT_MAX - 2))
            lon = float(rng.uniform(LON_MIN + 2, LON_MAX - 2))
            gi = float(rng.uniform(1.5, 8.0))
            p  = float(rng.uniform(0.0, 0.05))
            features.append({
                "type": "Feature",
                "geometry": _box_polygon(lat, lon, size=float(rng.uniform(0.3, 1.0))),
                "properties": {
                    "cluster_id":       f"{season}_{i+1:02d}",
                    "gi_star":          round(gi, 3),
                    "p_value":          round(p, 4),
                    "mean_hcho":        round(float(rng.uniform(5e-5, 4e-4)), 6),
                    "fire_count_mean":  round(float(rng.uniform(0, 50)), 1),
                    "dominant_driver":  random.choice(DRIVERS),
                    "season":           season,
                },
            })
        fc = {"type": "FeatureCollection", "features": features}
        out = OUTPUT_DIR / f"hotspots_{season}_2023.geojson"
        out.write_text(json.dumps(fc, indent=2), encoding="utf-8")
        print(f"  Wrote {out}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    generate_predictions()
    generate_stations()
    generate_validation()
    generate_hotspots()
    print("\nDone. Fixture files are in:", OUTPUT_DIR)
    print("To remove fixtures: delete api/fixtures/*.parquet and api/fixtures/*.geojson")
    print("Then point PREDICTIONS_PARQUET etc. env vars at your real data.")
