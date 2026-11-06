# System Architecture & Technical Design

This document details the software architecture, data flow pathways, and component interactions of the **Surface Air Quality Prediction and HCHO Hotspot Identification Platform**.

---

## 1. High-Level System Architecture

The platform operates as a decoupled full-stack geospatial application comprising a high-performance backend API and a reactive geospatial dashboard:

```
                                  ┌────────────────────────────────────────────────────────┐
                                  │                  External Data Sources                 │
                                  │   (Sentinel-5P, MODIS MAIAC, ERA5, CAAQMS, MOD14A1)    │
                                  └──────────────────────────┬─────────────────────────────┘
                                                             │
                                                             ▼
                                  ┌────────────────────────────────────────────────────────┐
                                  │           Data Processing & Modeling Pipeline          │
                                  │   - Feature Engineering (23 spatial/temporal/met)      │
                                  │   - Multi-Pollutant Stacking Regressors (Level 0/1)    │
                                  │   - Getis-Ord Gi* Spatial Hotspot Detection            │
                                  └───────────────┬────────────────────────┬───────────────┘
                                                  │                        │
                                      (Offline Precomputation)    (Real-Time Inference)
                                                  │                        │
                                                  ▼                        ▼
┌───────────────────────────────┐ ┌───────────────────────────────┐ ┌───────────────────────────────┐
│        Storage Layer          │ │       DuckDB / Parquet        │ │    FastAPI Application        │
│ - Trained Stacking Regressors │ │ - Cached Gridded Predictions  │ │ - Real-Time Predictor Engine  │
│ - GeoJSON Hotspot Polygons    │ │ - Monitoring Station Bias     │ │ - Spatiotemporal Gap-Filling  │
│ - Station Validation Data     │ │ - Leave-One-Out Validation    │ │ - CPCB Breakpoint Engine      │
└───────────────────────────────┘ └───────────────┬───────────────┘ └───────────────┬───────────────┘
                                                  │                                 │
                                                  └────────────────┬────────────────┘
                                                                   │ (REST / JSON)
                                                                   ▼
                                  ┌────────────────────────────────────────────────────────┐
                                  │                Web Frontend (React / Vite)             │
                                  │ - MapLibre GL Interactive Map Canvas                   │
                                  │ - Geospatial Location Search & Suggestion Modal        │
                                  │ - CPCB Air Quality Evaluation Drawer                   │
                                  │ - Formaldehyde (HCHO) Hotspot Analysis Viewer          │
                                  │ - Ground-Truth Validation & Residual Scatter Views     │
                                  │ - Client-Side PDF Executive Report Generator           │
                                  └────────────────────────────────────────────────────────┘
```

---

## 2. Core Subsystems

### 2.1 Backend Engine (`/api`)
Built with **FastAPI** (Python 3.10+ / ASGI), providing asynchronous request processing, data validation via **Pydantic v2**, and low-latency analytics.

Key backend components:
- **`api.main`**: Application entry point configuring middleware (CORS, in-memory caching), lifespan management, and router aggregation.
- **`api.db`**: Thread-safe DuckDB in-memory engine connecting precomputed Parquet stores and exposing SQL views without loading heavy statistical libraries into memory for read operations.
- **`api.routers`**:
  - `predict`: Real-time on-demand inference endpoint acquiring remote sensing features and evaluating stacking models.
  - `aqi`: Location-specific air quality index and pollutant sub-index queries.
  - `hotspots`: Seasonal HCHO spatial cluster retrieval with driver attribution.
  - `stations`: Ground-truth monitoring station coordinates with measured vs. predicted values.
  - `timeseries`: Multi-day historical concentrations with empirical uncertainty bounds.
  - `validation`: Model evaluation metrics, scatter distributions, and confusion matrices.
  - `geocode`: Server-side OpenStreetMap Nominatim proxy for place-name searches.
- **`api.services`**:
  - `feature_service`: Orchestrates satellite feature assembly (Sentinel-5P, MODIS) and ERA5 meteorological parameters.
  - `gapfill_service`: Validated fallback algorithms ensuring robust predictions during cloud cover or satellite observation gaps.
  - `model_service`: Loads and evaluates the multi-target stacking regressor pipelines (`multi_pollutant_stacking_pipeline.pkl`).
  - `aqi_service`: Centralized CPCB breakpoint calculation engine.

### 2.2 Analytical Modeling Core
- **Multi-Pollutant Stacking Pipeline**:
  - Predicts 6 criteria air pollutants: $\text{PM}_{2.5}$, $\text{PM}_{10}$, $\text{NO}_2$, $\text{SO}_2$, $\text{O}_3$, and $\text{CO}$.
  - Level-0 Base Learners: Extra Trees, Random Forest, Gradient Boosting, LightGBM, and XGBoost.
  - Level-1 Meta-Learner: Huber Regressor with non-negative constraints.
- **Hotspot Detection Core**:
  - Computes spatial Getis-Ord $G_i^*$ statistics on a $0.25^\circ \times 0.25^\circ$ resolution grid over India ($Z > 1.96, p < 0.05$).
  - Clips polygon boundaries against authoritative national boundary definitions.
  - Contextualizes clusters using MODIS active fire observations and ERA5 reanalysis winds.

### 2.3 Frontend Dashboard (`/web`)
Developed with **React 18**, **TypeScript**, and **Vite**, packaged with Tailwind CSS:
- **`MapView`**: MapLibre GL JS vector canvas rendering stepped CPCB color layers, spatial raster grids, active monitoring stations, and animated marker pulses.
- **`LocationSearch`**: Dual-mode geospatial finder supporting place-name geocoding and coordinate validation ($[-90, 90]^\circ$ lat, $[-180, 180]^\circ$ lon).
- **`PredictionDetailPanel`**: Slide-out drawer presenting real-time AQI readouts, dominant pollutant identification, pollutant grids, data quality indicators, and download triggers.
- **`generateAqiPdfReport`**: In-browser PDF compilation engine leveraging `jsPDF` and `jspdf-autotable` to produce publication-grade executive assessment briefs.

---

## 3. Data Flow Pathways

### 3.1 Real-Time Surface AQI Prediction Flow
```
User Action (Map Click or Location Search)
   │
   ▼
POST /api/predict { latitude, longitude, date }
   │
   ├─► Feature Acquisition (`feature_service.py`)
   │      ├─► Google Earth Engine (MODIS AOD, Sentinel-5P NO2/SO2/CO/O3/HCHO)
   │      ├─► ERA5 Reanalysis (Temperature, Humidity, Wind, Pressure, Rain, Radiation)
   │      └─► Fallback Gap-Filling (if cloud cover exceeds operational threshold)
   │
   ├─► Feature Vector Assembly (Strict 23-feature order)
   │
   ├─► Multi-Target Stacking Regressors (`model_service.py`)
   │      └─► Predicted concentrations: [PM2.5, PM10, NO2, SO2, O3, CO]
   │
   ├─► CPCB Sub-Index Conversion (`api/aqi/breakpoints.py`)
   │      ├─► Compute sub-indices via piecewise linear interpolation
   │      ├─► Determine composite AQI = max(sub_indices)
   │      └─► Assign CPCB category (Good, Satisfactory, Moderate, Poor, Very Poor, Severe)
   │
   ▼
JSON Response to Frontend -> Rendered in Prediction Drawer -> Available for PDF Export
```

### 3.2 Precomputed Analytical Exploration Flow
For browsing historical layers, multi-month time series, and seasonal hotspots:
```
Client Request (GET /api/hotspots, /api/timeseries, /api/validation)
   │
   ▼
FastAPI Router -> FastAPI Cache (In-Memory Check)
   │ (Cache Miss)
   ▼
DuckDB Singleton -> Scans Parquet Store / GeoJSON Feature Collections
   │
   ▼
Cached JSON Response -> High-speed vector rendering in MapLibre & Recharts
```

---

## 4. Reliability and Fault Tolerance

1. **Decoupled Architecture**: Read operations for cached grid cells and stations are decoupled from live satellite APIs, ensuring high availability even if external satellite platforms experience transient downtime.
2. **Strict Scientific Provenance**: Live predictions flag whether data reflects direct observation or reconstructed inputs, preventing false precision.
3. **Client-Side PDF Generation**: Reports are generated entirely within the browser sandbox using retrieved prediction snapshots, eliminating server CPU overhead and scaling seamlessly.

