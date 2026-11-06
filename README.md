# Surface AQI & HCHO Hotspots

Research web application displaying model-estimated ground-level air quality and HCHO hotspot data across a region with sparse physical monitoring.

**Audience:** Environmental researchers, pollution-control board staff, academic reviewers.

---

## Architecture

```
multi_pollutant_stacking_pipeline.pkl  ← trained model (offline only)
        │
        ▼ (run offline)
api/fixtures/generate_fixtures.py  →  fixtures/*.parquet + *.geojson
                                           │
              ┌────────────────────────────┘
              │
              ▼
       FastAPI (/api)              React + Vite (/web)
       reads Parquet/DuckDB        MapLibre GL, Recharts
       port 8000                   port 5173
```

**The model is never loaded at request time.** All values come from a pre-computed Parquet store.

---

## Local Setup

### Prerequisites

- Python 3.11+
- Node.js 20+
- (Optional) Docker + Docker Compose

### 1. Backend

```bash
cd api

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -r requirements.txt

# Generate fixture data (first run only)
python -m fixtures.generate_fixtures

# Start the API server
uvicorn api.main:app --reload --port 8000
```

Verify: `curl http://localhost:8000/health` → `{"status":"ok"}`

### 2. Frontend

```bash
cd web
npm install
npm run dev
```

Open `http://localhost:5173`. The Vite dev proxy forwards `/api/*` to FastAPI.

### 3. Run tests

```bash
cd api
pytest aqi/test_breakpoints.py -v
```

### 4. Docker (optional)

```bash
cp .env.example .env
docker compose up --build
```

---

## Swapping Fixtures for Real Data

Once step 3 of the build (location detail panel) works against fixtures, replace them:

1. Run your offline prediction pipeline using `multi_pollutant_stacking_pipeline.pkl`
2. Write outputs to Parquet with the schema in `api/db.py`
3. Update the env vars `PREDICTIONS_PARQUET`, `STATIONS_PARQUET`, `VALIDATION_PARQUET`, `HOTSPOTS_GEOJSON` in `.env`
4. Delete `api/fixtures/generate_fixtures.py` and `api/fixtures/*.parquet` / `*.geojson`

---

## Project Highlights

- **Interactive AQI Mapping:** Visualisation of air quality information across geographical locations using an interactive map.
- **Multi-Pollutant Prediction:** Prediction of PM2.5, PM10, NO2, SO2, O3 and CO concentrations using machine learning models.
- **Location-Based Analysis:** Explore air quality predictions for selected geographical coordinates and locations.
- **Temporal Analysis:** Examine air quality variations over time through interactive visualisations.
- **Monitoring Station Insights:** Explore ground-based observations alongside model predictions.
- **HCHO Hotspot Detection:** Identify and analyse seasonal formaldehyde hotspots using satellite observations and spatial statistical techniques.
- **Fire Association Analysis:** Analyse the spatial association between HCHO hotspots and MODIS active fire observations.
- **Model Validation:** Explore model performance and validation metrics through a dedicated dashboard.
- **PDF Report Generation:** Generate downloadable reports containing AQI predictions, pollutant details and data-quality information.

---

## Technical Implementation

| Component | Technologies |
|---|---|
| Frontend | React, TypeScript, Vite, Tailwind CSS |
| Backend | Python, FastAPI, Uvicorn |
| Machine Learning | Scikit-learn, XGBoost, LightGBM |
| Geospatial Visualisation | MapLibre GL JS |
| Data Visualisation | Recharts |
| Satellite Data | Sentinel-5P, MODIS MAIAC AOD, MODIS Active Fire |
| Meteorological Data | ERA5 / ERA5-Land |
| Ground Observations | CPCB monitoring data |
| Spatial Statistics | Getis-Ord Gi* |
| Model Architecture | Stacking Ensemble Regression |
| PDF Reporting | jsPDF, jsPDF-AutoTable |

---

## API Reference

Base path: `http://localhost:8000/api`

| Endpoint | Description |
|----------|-------------|
| `GET /health` | Liveness check |
| `GET /api/aqi?lat=&lon=&date=` | AQI + sub-indices for a location and date |
| `GET /api/timeseries?lat=&lon=&from=&to=&variable=` | Time series with CI band |
| `GET /api/hotspots?season=&year=` | HCHO hotspot GeoJSON |
| `GET /api/stations?date=` | Monitoring stations (observed + predicted) |
| `GET /api/validation` | Validation metrics and scatter data |

Interactive docs: `http://localhost:8000/docs`

---

## Stack

| Layer | Technology |
|-------|------------|
| Backend | FastAPI, DuckDB, PyArrow |
| Frontend | React 18, TypeScript, Vite |
| Map | MapLibre GL JS |
| Charts | Recharts |
| API state | TanStack Query |
| Styling | Tailwind CSS |
| Containerisation | Docker Compose |
