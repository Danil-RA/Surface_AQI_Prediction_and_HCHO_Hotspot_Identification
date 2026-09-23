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

## Build Order (Prompts 1–8)

| Step | Prompt | What it adds |
|------|--------|-------------|
| 1 | Prompt 1 | Map + legend (one static AQI layer) |
| 2 | Prompt 2 | Date timeline + layer switching |
| 3 | Prompt 3 | Click → detail panel (wired to /api/aqi) |
| 4 | Prompt 4 | Time series with CI band and coverage gaps |
| 5 | Prompt 5 | Station markers (observed vs predicted) |
| 6 | Prompt 6 | HCHO hotspots page (/hotspots) |
| 7 | Prompt 7 | Validation page (/validation) |
| 8 | Prompt 8 | Method page + responsive + accessibility pass |

---

## The Three Things to Check After Every Step

Per `PROMPT.md`:

1. **AQI colour scale is stepped, not a gradient** — hard edges at CPCB breakpoints
2. **No-coverage never renders as a value** — `null` aqi cells show the hatch pattern, not 0
3. **No breakpoint arithmetic in the frontend** — all AQI computation is server-side only

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
