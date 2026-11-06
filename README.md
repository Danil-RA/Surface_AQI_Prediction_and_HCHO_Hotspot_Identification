# Surface Air Quality Prediction and HCHO Hotspot Identification

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?style=flat&logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/Frontend-React_18-61DAFB?style=flat&logo=react)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/Language-TypeScript-3178C6?style=flat&logo=typescript)](https://www.typescriptlang.org)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat&logo=python)](https://www.python.org)
[![MapLibre GL](https://img.shields.io/badge/Map-MapLibre_GL_JS-396B99?style=flat)](https://maplibre.org)
[![DuckDB](https://img.shields.io/badge/Analytics-DuckDB-FFF000?style=flat&logo=duckdb)](https://duckdb.org)

An integrated geospatial research and environmental monitoring platform that estimates ground-level criteria air pollutant concentrations, derives Central Pollution Control Board (CPCB) Air Quality Index (AQI) values, and identifies regional Formaldehyde ($\text{HCHO}$) precursor hotspots across India using multi-sensor satellite retrievals and machine-learning ensembles.

---

## Table of Contents
1. [Project Overview & Motivation](#1-project-overview--motivation)
2. [Objectives](#2-objectives)
3. [Key Features](#3-key-features)
4. [System Architecture](#4-system-architecture)
5. [Technology Stack](#5-technology-stack)
6. [Data Sources & Atmospheric Retrievals](#6-data-sources--atmospheric-retrievals)
7. [AQI Prediction Methodology](#7-aqi-prediction-methodology)
8. [HCHO Hotspot Identification Methodology](#8-hcho-hotspot-identification-methodology)
9. [Application Architecture & API Overview](#9-application-architecture--api-overview)
10. [Dashboard & User Interface Features](#10-dashboard--user-interface-features)
11. [Report Generation Functionality (PDF)](#11-report-generation-functionality-pdf)
12. [Results & Validation Performance](#12-results--validation-performance)
13. [Installation & Setup](#13-installation--setup)
14. [Environment Configuration](#14-environment-configuration)
15. [Running the Application](#15-running-the-application)
16. [Model & Dataset Availability](#16-model--dataset-availability)
17. [Future Scope](#17-future-scope)
18. [Documentation Links](#18-documentation-links)
19. [References & Data Attribution](#19-references--data-attribution)

---

## 1. Project Overview & Motivation

Ground-based atmospheric air quality monitoring networks in developing regions face significant spatial heterogeneity. Physical Continuous Ambient Air Quality Monitoring Stations (CAAQMS) are concentrated primarily in tier-1 urban centers and industrial corridors, leaving suburban, agricultural, and rural populations with limited local measurement coverage.

This platform bridges spatial monitoring gaps by combining:
- **High-resolution Earth observation satellite data** (Sentinel-5P TROPOMI and MODIS MAIAC).
- **Global atmospheric reanalysis meteorology** (ECMWF ERA5 / ERA5-Land).
- **Multi-model stacking regression algorithms** calibrated against the national CPCB ground network.
- **Local spatial autocorrelation statistics (Getis-Ord $G_i^*$)** to isolate statistically significant formaldehyde precursor hotspots and evaluate seasonal co-occurrence with active thermal fire detections.

---

## 2. Objectives

- **Spatial Air Quality Synthesis**: Predict surface concentrations for six criteria pollutants ($\text{PM}_{2.5}$, $\text{PM}_{10}$, $\text{NO}_2$, $\text{SO}_2$, $\text{O}_3$, and $\text{CO}$) across unmonitored regions.
- **Regulatory Standard Compliance**: Convert predicted pollutant concentrations into official CPCB sub-indices using strict piecewise linear breakpoint interpolation.
- **Precursor Hotspot Mapping**: Detect seasonal clusters of elevated tropospheric formaldehyde ($\text{HCHO}$) across India and categorize temporal association with active biomass combustion.
- **Transparent Operational Provenance**: Clearly distinguish direct satellite observations from reconstructed inputs, presenting reliable data quality classifications.
- **Actionable Reporting**: Enable users to export structured, publication-grade PDF assessment briefs directly from live or selected predictions.

---

## 3. Key Features

- **Interactive Full-Bleed Map Canvas**: Fast raster and vector rendering using MapLibre GL JS with stepped CPCB categorical color scales.
- **Dual-Mode Geospatial Search**: Forward place-name geocoding via an internal OpenStreetMap Nominatim proxy and coordinate input with boundary validation.
- **Live On-Demand Prediction**: Map-click or search-driven inference querying Earth Engine and reanalysis models to compute real-time AQI in seconds.
- **Temporal Timeline Scrubbing**: Historical day-by-day exploration with dynamic coverage gap detection.
- **HCHO Hotspot Explorer**: Seasonal visualization of Getis-Ord $G_i^*$ clusters with interactive fire association, wind speed, and humidity diagnostics.
- **Station-Level Ground-Truth Modal**: Detailed comparison between physically observed CAAQMS values and model-estimated concentrations with residual tracking.
- **Executive PDF Export**: Client-side compiled A4 assessment document detailing location metadata, individual pollutant concentrations, sub-indices, and data provenance.

---

## 4. System Architecture

The application adopts an asynchronous microservice pattern separating real-time machine-learning inference and cached analytical vector queries:

```
                                  ┌────────────────────────────────────────────────────────┐
                                  │                  Remote Sensing Feeds                  │
                                  │   (Sentinel-5P, MODIS MAIAC, ERA5, CAAQMS, MOD14A1)    │
                                  └──────────────────────────┬─────────────────────────────┘
                                                             │
                                                             ▼
                                  ┌────────────────────────────────────────────────────────┐
                                  │           Data Processing & Modeling Pipeline          │
                                  │   - 23-Feature Engineering Matrix                      │
                                  │   - Multi-Model Stacking Regressors (Level 0/1)        │
                                  │   - Getis-Ord Gi* Spatial Hotspot Detection            │
                                  └───────────────┬────────────────────────┬───────────────┘
                                                  │                        │
                                      (Offline Precomputation)    (Live Inference)
                                                  │                        │
                                                  ▼                        ▼
┌───────────────────────────────┐ ┌───────────────────────────────┐ ┌───────────────────────────────┐
│        Storage Layer          │ │       DuckDB / Parquet        │ │    FastAPI Application        │
│ - Trained Stacking Regressors │ │ - Cached Gridded Predictions  │ │ - Live Inference Router       │
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
                                  │ - Location Search & Coordinate Targeting               │
                                  │ - Real-Time Prediction & Breakdown Drawer              │
                                  │ - HCHO Hotspot & Fire Association Explorer             │
                                  │ - In-Browser Executive PDF Report Generator            │
                                  └────────────────────────────────────────────────────────┘
```

For full architectural details, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

---

## 5. Technology Stack

### Backend
- **Framework**: FastAPI (Python 3.10+) / Uvicorn ASGI
- **Data Query Engine**: DuckDB in-memory database with PyArrow Parquet views
- **Earth Observation**: Google Earth Engine Python API (`earthengine-api`)
- **Machine Learning**: Scikit-Learn (`StackingRegressor`, `HuberRegressor`), XGBoost, LightGBM
- **Spatial Statistics**: GeoPandas, Shapely, Libpysal, ESDA

### Frontend
- **Framework**: React 18, TypeScript, Vite
- **Styling**: Tailwind CSS
- **Map Engine**: MapLibre GL JS
- **Data Visualization**: Recharts
- **State Management & Caching**: TanStack React Query v5
- **Document Generation**: `jspdf` & `jspdf-autotable`

---

## 6. Data Sources & Atmospheric Retrievals

The platform synthesizes five core earth observation and ground monitoring datasets:

1. **CPCB CAAQMS Network**: Continuous ground-level air quality observations across India used for ensemble training, baseline calibration, and out-of-fold validation.
2. **Sentinel-5P TROPOMI**: Daily tropospheric column densities ($\text{mol/m}^2$) of $\text{NO}_2$, $\text{SO}_2$, $\text{CO}$, $\text{O}_3$, and $\text{HCHO}$ at $3.5 \times 5.5\text{ km}$ spatial resolution.
3. **MODIS MAIAC AOD**: Multi-Angle Implementation of Atmospheric Correction 1 km Aerosol Optical Depth at 550 nm (`MCD19A2`) merged across Terra and Aqua platforms.
4. **ECMWF ERA5 / ERA5-Land**: Hourly and daily atmospheric reanalysis delivering 2m temperature, relative humidity, surface pressure, 10m wind components ($u, v$), precipitation, and solar radiation.
5. **MODIS Active Fire (`MOD14A1`)**: Contextual thermal anomaly detections at 1 km resolution (`FireMask >= 7`) for temporal biomass burning association.

Detailed dataset specifications, band descriptions, and acquisition workflows are documented in [docs/DATA_SOURCES.md](docs/DATA_SOURCES.md).

---

## 7. AQI Prediction Methodology

### 7.1 23-Feature Vector Assembly
Live inference constructs an ordered 23-dimensional feature vector combining satellite columns, meteorological fields, spatial coordinates, and engineered interaction terms:
1. `AOD` (MODIS MAIAC 550nm)
2. `NO2` (Sentinel-5P tropospheric column)
3. `SO2` (Sentinel-5P column)
4. `CO` (Sentinel-5P column)
5. `O3` (Sentinel-5P column)
6. `HCHO` (Sentinel-5P column)
7. `AT (°C)` (2m ambient temperature)
8. `RH (%)` (relative humidity)
9. `WS (m/s)` (10m wind speed)
10. `WD (deg)` (wind direction)
11. `TOT-RF (mm)` (accumulated rainfall)
12. `SR (W/mt2)` (solar radiation)
13. `BP (mmHg)` (barometric surface pressure)
14. `VWS (m/s)` (vertical wind speed / shear proxy)
15. `Latitude` (WGS84 decimal degrees)
16. `Longitude` (WGS84 decimal degrees)
17. `Month` ($1 - 12$)
18. `DayOfWeek` ($0 - 6$)
19. `DayOfYear` ($1 - 365$)
20. `AOD_RH_ratio` (hygroscopic aerosol growth proxy: $\text{AOD} / (\text{RH} / 100)$)
21. `U_Wind` (zonal wind velocity component: $-\text{WS} \cdot \sin(\text{WD})$)
22. `V_Wind` (meridional wind velocity component: $-\text{WS} \cdot \cos(\text{WD})$)
23. `Temp_Pressure_Ratio` (air density proxy: $\text{AT} / \text{BP}$)

### 7.2 Multi-Model Stacking Regression
Predictions are generated by six independent two-level stacking regression ensembles:
- **Level 0 (Base Estimators)**: Extra Trees, Random Forest, Gradient Boosting, XGBoost, and LightGBM.
- **Level 1 (Meta Estimator)**: Huber Regressor, offering mathematical robustness against extreme outlier concentration spikes.

### 7.3 CPCB Breakpoint Calculation
Predicted concentrations ($C_p$) are transformed into individual pollutant sub-indices ($I_p$) via official CPCB piecewise linear interpolation:

$$I_p = \left( \frac{I_{high} - I_{low}}{BP_{high} - BP_{low}} \right) \cdot (C_p - BP_{low}) + I_{low}$$

The composite AQI is strictly governed by the **maximum pollutant sub-index**:

$$\text{Overall AQI} = \max\left( I_{\text{PM2.5}}, I_{\text{PM10}}, I_{\text{NO2}}, I_{\text{SO2}}, I_{\text{CO}}, I_{\text{O3}} \right)$$

$$\text{Dominant Pollutant} = \arg\max_p \left( I_p \right)$$

Categorical classifications:
- **Good** ($0 - 50$)
- **Satisfactory** ($51 - 100$)
- **Moderate** ($101 - 200$)
- **Poor** ($201 - 300$)
- **Very Poor** ($301 - 400$)
- **Severe** ($401 - 500$)

A complete step-by-step breakdown is available in [docs/METHODOLOGY.md](docs/METHODOLOGY.md).

---

## 8. HCHO Hotspot Identification Methodology

Formaldehyde ($\text{HCHO}$) acts as an indicator for volatile organic compound (VOC) emissions that catalyze tropospheric ozone formation.

1. **Spatial Discretization**: India is gridded into $0.25^\circ \times 0.25^\circ$ regular cells ($8.0^\circ\text{N} - 36.0^\circ\text{N}$, $68.0^\circ\text{E} - 96.0^\circ\text{E}$).
2. **Seasonal Composition**: Analyzed across Winter (Jan–Feb), Pre-Monsoon (Mar–May), Monsoon (Jun–Sep), and Post-Monsoon (Oct–Dec).
3. **Getis-Ord $G_i^*$ Spatial Statistics**: Evaluates local spatial autocorrelation against national background concentrations. Cells with $Z > 1.96$ ($95\%$ confidence) and $p < 0.05$ are selected as hotspot cells.
4. **Cluster Polygon Formation**: Contiguous cells are dissolved into geometric clusters and clipped to the authoritative national boundary.
5. **MODIS Active Fire Co-Occurrence**: Daily satellite overpasses are checked for thermal fire detections (`FireMask >= 7`):
   - `pyrogenic_associated`: Active fires detected on $>10\%$ of valid observation days, or total seasonal fire count $> 5$.
   - `non_fire_associated`: High HCHO elevation with $0$ active fire detections (indicating dominant contributions from biogenic emissions, industrial activity, or urban vehicle emissions).
   - `undetermined`: Ambiguous or intermediate conditions.

> **Note on Causality**: Temporal fire association reflects observational co-occurrence between thermal anomalies and elevated formaldehyde; it does not constitute individual source causation.

---

## 9. Application Architecture & API Overview

| Endpoint | Method | Purpose |
|:---|:---:|:---|
| `/api/predict` | `POST` | Live on-demand surface AQI prediction from coordinates and date |
| `/api/aqi` | `GET` | Precomputed surface AQI, sub-indices, and nearest CAAQMS station |
| `/api/timeseries` | `GET` | Multi-day historical trends with 95% empirical confidence intervals |
| `/api/hotspots` | `GET` | GeoJSON FeatureCollection of seasonal HCHO hotspot clusters |
| `/api/stations` | `GET` | Ground monitoring stations with paired measured vs. predicted values |
| `/api/validation` | `GET` | Comprehensive evaluation metrics, residual scatter, and confusion matrix |
| `/api/geocode` | `GET` | Server-side proxy for OpenStreetMap Nominatim place queries |
| `/health` | `GET` | Liveness health check |

Interactive OpenAPI documentation is hosted at `http://localhost:8000/docs`. Full endpoint contracts are detailed in [docs/API.md](docs/API.md).

---

## 10. Dashboard & User Interface Features

- **Map View (`/`)**: Main interactive exploration surface displaying composite AQI and individual pollutant raster layers with stepped CPCB legends.
- **Find Location Search**: Floating modal allowing search by place name (with auto-suggestions) or exact coordinates.
- **Real-Time Prediction Drawer**: Slide-out panel presenting overall AQI, dominant pollutant, pollutant concentrations, sub-indices, data quality badges, and report export.
- **Hotspots Explorer (`/hotspots`)**: Seasonal filter interface examining formaldehyde clusters, fire counts, wind vectors, and driver classification.
- **Model Validation (`/validation`)**: Interactive scatter plots, $R^2$/RMSE metrics, leave-one-station-out cross-validation rankings, and categorical confusion matrices.
- **Methodology & Framework (`/method`)**: Full scientific descriptions of satellite ingestion, modeling assumptions, and known observational boundaries.

---

## 11. Report Generation Functionality (PDF)

The platform includes a client-side document compiler using `jsPDF` and `jspdf-autotable`:

- **Location**: Triggered via the **"Download Report (PDF)"** action in the prediction drawer.
- **Snapshot Consistency**: Reports are assembled from the immutable prediction response currently on display, preventing stale-state mismatches if coordinates or dates are subsequently altered.
- **Structure**:
  1. Header banner with official assessment title.
  2. Executive summary: Prominent AQI numeric readout, CPCB category badge, and dominant pollutant.
  3. Location metadata: Resolved place name, coordinates, target date, and generation timestamp.
  4. Pollutant table: Six criteria pollutants with predicted concentrations, units ($\mu\text{g/m}^3$ and $\text{mg/m}^3$), and sub-indices.
  5. Data quality & provenance: Quality classification (`HIGH`, `MODERATE`, `LIMITED`), variable availability, and extreme underestimation warnings where spatial reconstruction was utilized.
  6. Methodology note and scientific advisory disclaimer.
- **Sanitized Filename**: Automatically formatted, for example:
  `Surface_AQI_Report_Thiruvananthapuram_2026-11-04.pdf`

---

## 12. Results & Validation Performance

The stacking ensemble was independently validated using out-of-fold leave-one-station-out cross-validation against physical CPCB CAAQMS monitoring stations across India.

### Verified Test Set Performance Metrics

| Pollutant | Coefficient of Determination ($R^2$) | Root Mean Square Error (RMSE) | Mean Absolute Error (MAE) |
|:---|:---:|:---:|:---:|
| **$\text{PM}_{2.5}$** | **0.862** | $19.96\text{ }\mu\text{g/m}^3$ | $11.20\text{ }\mu\text{g/m}^3$ |
| **$\text{PM}_{10}$** | **0.854** | $35.44\text{ }\mu\text{g/m}^3$ | $22.07\text{ }\mu\text{g/m}^3$ |
| **$\text{NO}_2$** | **0.845** | $9.24\text{ }\mu\text{g/m}^3$ | $4.87\text{ }\mu\text{g/m}^3$ |
| **$\text{SO}_2$** | **0.719** | $4.04\text{ }\mu\text{g/m}^3$ | $2.08\text{ }\mu\text{g/m}^3$ |
| **$\text{O}_3$** | **0.776** | $10.87\text{ }\mu\text{g/m}^3$ | $6.12\text{ }\mu\text{g/m}^3$ |
| **$\text{CO}$** | **0.702** | $0.36\text{ mg/m}^3$ | $0.19\text{ mg/m}^3$ |

---

## 13. Installation & Setup

### Prerequisites
- Python 3.10 or 3.11
- Node.js 20+ and npm 10+
- Git and Git LFS

### 1. Clone the Repository
```bash
git clone https://github.com/Danil-RA/Surface_AQI_Prediction_and_HCHO_Hotspot_Identification.git
cd Surface_AQI_Prediction_and_HCHO_Hotspot_Identification
```

### 2. Pull Git LFS Artifacts
```bash
git lfs pull
```

### 3. Backend Setup
```bash
cd api
python -m venv .venv

# On Linux / macOS:
source .venv/bin/activate
# On Windows:
.venv\Scripts\activate

pip install -r requirements.txt
```

### 4. Frontend Setup
```bash
cd ../web
npm install
```

---

## 14. Environment Configuration

Create a `.env` file in the `api/` directory (see `api/.env.example` if present):
```ini
# Google Earth Engine Cloud Project
EE_PROJECT_ID=your-google-cloud-project-id

# Optional Custom Parquet Paths
PREDICTIONS_PARQUET=fixtures/predictions.parquet
STATIONS_PARQUET=fixtures/stations.parquet
HOTSPOTS_GEOJSON=fixtures/hotspots.geojson
VALIDATION_PARQUET=fixtures/validation.parquet
```

### Google Earth Engine Authentication
To execute live satellite feature queries:
```bash
earthengine authenticate
```

---

## 15. Running the Application

### Start the Backend
From the `api/` directory:
```bash
uvicorn api.main:app --reload --port 8000
```
API endpoints and Swagger docs will be accessible at `http://localhost:8000/docs`.

### Start the Frontend
From the `web/` directory:
```bash
npm run dev
```
Open `http://localhost:5173` in your browser. The Vite dev proxy automatically forwards `/api/*` requests to the FastAPI service on port 8000.

---

## 16. Model & Dataset Availability

- **Stacking Regression Pipeline**: Tracked via Git LFS at `multi_pollutant_stacking_pipeline.pkl`.
- **Precomputed Geospatial Stores**: Stored in Apache Parquet format under `api/fixtures/` and queried dynamically via DuckDB.
- **Seasonal Hotspot Polygons**: Standard GeoJSON FeatureCollections structured under `data/hotspots/`.

---

## 17. Future Scope

1. **Expanded Ground Calibration**: Incorporating emerging low-cost sensor meshes and additional state pollution control board stations in rural settings.
2. **Deep Learning Spatiotemporal Ensembles**: Integrating graph neural networks (GNNs) and ConvLSTM architectures to capture transboundary advection patterns.
3. **High-Resolution Urban Downscaling**: Incorporating Sentinel-2 multi-spectral urban land-use indices (NDVI, NDBI) to produce sub-kilometer neighborhood predictions.
4. **Automated Batch Reporting**: Scheduled regional PDF briefings dispatchable via email or messaging webhooks.

---

## 18. Documentation Links

- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) – Detailed system architecture and microservice workflows.
- [docs/METHODOLOGY.md](docs/METHODOLOGY.md) – Stacking mathematics, 23-feature vector, and hotspot algorithms.
- [docs/DATA_SOURCES.md](docs/DATA_SOURCES.md) – Remote sensing products, bands, resolutions, and provider links.
- [docs/API.md](docs/API.md) – RESTful API endpoints, request schemas, and error codes.
- [CONTRIBUTING.md](CONTRIBUTING.md) – Development guidelines and contribution instructions.

---

## 19. References & Data Attribution

- **Central Pollution Control Board (CPCB)**, Ministry of Environment, Forest and Climate Change, Government of India. *National Air Quality Index Report* (2014).
- **Copernicus Sentinel-5P TROPOMI**: European Space Agency (ESA) & Royal Netherlands Meteorological Institute (KNMI).
- **MODIS MAIAC & Thermal Anomalies**: NASA Earth Observing System Data and Information System (EOSDIS) Land Processes DAAC.
- **ECMWF ERA5**: Hersbach, H., et al. (2020). "The ERA5 global reanalysis." *Quarterly Journal of the Royal Meteorological Society*, 146(730), 1999-2049.
- **Getis, A., & Ord, J. K.** (1992). "The analysis of spatial association by use of distance statistics." *Geographical Analysis*, 24(3), 189-206.

---

**Author / Maintainer**: Danil-RA  
**License**: Research and Academic Use
