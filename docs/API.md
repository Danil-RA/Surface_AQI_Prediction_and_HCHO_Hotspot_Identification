# API Documentation & Endpoint Reference

The platform backend provides a RESTful interface implemented in **FastAPI** (`http://localhost:8000`). Interactive Swagger documentation and OpenAPI schemas are automatically available at `/docs` and `/redoc`.

---

## 1. Authentication & Protocols
- **Base URL**: `http://localhost:8000` (or reverse-proxied via Vite frontend at `/api/*`)
- **Transport**: Standard HTTP/1.1 or HTTP/2 over TLS
- **Content-Type**: `application/json`

---

## 2. Core Endpoints

### 2.1 Live Surface AQI Prediction
`POST /api/predict`

Executes real-time remote sensing feature extraction, runs the 6-pollutant stacking regression ensemble, and returns computed CPCB pollutant sub-indices and overall AQI.

#### Request Body
```json
{
  "latitude": 28.6139,
  "longitude": 77.2090,
  "date": "2023-11-04"
}
```

| Field | Type | Description |
|:---|:---:|:---|
| `latitude` | `float` | Target latitude in decimal degrees ($-90.0 \le \text{lat} \le 90.0$). |
| `longitude` | `float` | Target longitude in decimal degrees ($-180.0 \le \text{lon} \le 180.0$). |
| `date` | `string` | ISO 8601 calendar date (`YYYY-MM-DD`). |

#### Successful Response (`200 OK`)
```json
{
  "location": {
    "latitude": 28.6139,
    "longitude": 77.209
  },
  "date": "2023-11-04",
  "predictions": {
    "PM2.5": 253.28,
    "PM10": 373.92,
    "NO2": 103.49,
    "SO2": 21.62,
    "O3": 40.79,
    "CO": 2.77
  },
  "aqi": {
    "value": 403,
    "category": "Severe"
  },
  "dominant_pollutant": "PM2.5",
  "sub_indices": {
    "PM2.5": 403,
    "PM10": 330,
    "NO2": 123,
    "SO2": 27,
    "CO": 109,
    "O3": 41
  },
  "provenance": {
    "vws": { "source": "synthetic_fallback" }
  },
  "data_quality": "HIGH",
  "satellite_provenance": {
    "AOD": { "value": 0.85, "source": "observed" },
    "NO2": { "value": 0.00018, "source": "observed" },
    "SO2": { "value": 0.00004, "source": "observed" },
    "CO": { "value": 0.0021, "source": "observed" },
    "O3": { "value": 0.00032, "source": "temporal_recovery" },
    "HCHO": { "value": 0.00012, "source": "observed" }
  }
}
```

#### Error Response: Missing Environmental Data (`422 Unprocessable Entity`)
Returned when satellite inputs exceed cloud masking thresholds and cannot be gap-filled:
```json
{
  "detail": {
    "message": "Environmental data is unavailable for this location/date.",
    "missing_data": [
      { "source": "Sentinel-5P", "variables": ["NO2", "SO2"] }
    ],
    "available_data": [
      { "source": "MODIS MAIAC", "variables": ["AOD"] }
    ]
  }
}
```

---

### 2.2 Precomputed Location AQI
`GET /api/aqi`

Fetches cached precomputed concentrations, CPCB sub-indices, and nearest CAAQMS station distance.

#### Query Parameters
- `lat` (`float`, required): Latitude in decimal degrees.
- `lon` (`float`, required): Longitude in decimal degrees.
- `date` (`string`, required): ISO date (`YYYY-MM-DD`).

#### Response (`200 OK`)
```json
{
  "lat": 28.61,
  "lon": 77.21,
  "date": "2023-11-04",
  "grid_cell": [28.60, 77.20],
  "aqi": 385,
  "category": "Very Poor",
  "category_color": "#E93F33",
  "dominant_pollutant": "PM2.5",
  "sub_indices": { "PM2.5": 385, "PM10": 310, "NO2": 115 },
  "concentrations": {
    "PM2.5": { "value": 235.4, "unit": "µg/m³", "ci_low": 210.0, "ci_high": 260.8 }
  },
  "hcho_column": 0.00014,
  "hcho_unit": "mol/m²",
  "coverage": "full",
  "nearest_station": {
    "id": "DL001",
    "name": "Mandir Marg, Delhi",
    "distance_km": 4.2
  }
}
```

---

### 2.3 Formaldehyde Hotspot Clusters
`GET /api/hotspots`

Retrieves seasonal Getis-Ord $G_i^*$ hotspot clusters as an authoritative GeoJSON FeatureCollection with driver attribution.

#### Query Parameters
- `season` (`string`, required): One of `winter`, `premonsoon`, `monsoon`, `postmonsoon`.
- `year` (`int`, optional, default: 2023): Analysis year.

#### Response (`200 OK`)
GeoJSON FeatureCollection containing polygons with properties:
- `cluster_id` (`string`): Unique UUID.
- `gi_star` (`float`): Mean Getis-Ord $Z$-score for the cluster.
- `p_value` (`float`): Statistical significance.
- `mean_hcho` (`float`): Mean column density ($\text{mol/m}^2$).
- `fire_count_total` (`int`): Sum of MODIS active fire detections over the season.
- `dominant_driver` (`string`): `pyrogenic_associated` | `non_fire_associated` | `undetermined`.
- `mean_temperature` ($^\circ\text{C}$), `mean_relative_humidity` ($\%$), `mean_wind_speed` ($\text{m/s}$), `prevailing_wind_direction` ($^\circ$).

---

### 2.4 Monitoring Stations Network
`GET /api/stations`

Returns active CAAQMS monitoring stations across India with paired observed vs. estimated values.

#### Query Parameters
- `date` (`string`, required): ISO date (`YYYY-MM-DD`).

#### Response (`200 OK`)
```json
[
  {
    "station_id": "DL001",
    "name": "Mandir Marg, Delhi",
    "lat": 28.636,
    "lon": 77.201,
    "date": "2023-11-04",
    "observed_aqi": 412,
    "predicted_aqi": 398,
    "bias": -14.0
  }
]
```

---

### 2.5 Time Series & Uncertainty Bounds
`GET /api/timeseries`

Provides multi-day trend vectors with 95% empirical confidence intervals for chart rendering.

#### Query Parameters
- `lat` (`float`, required): Latitude.
- `lon` (`float`, required): Longitude.
- `from` (`string`, required): Start date (`YYYY-MM-DD`).
- `to` (`string`, required): End date (`YYYY-MM-DD`).
- `variable` (`string`, required): `aqi`, `pm25`, `pm10`, `no2`, `so2`, `co`, `o3`, or `hcho`.

---

### 2.6 Model Validation Metrics
`GET /api/validation`

Outputs independent validation metrics, out-of-fold scatter points, and categorical confusion matrices.

#### Response (`200 OK`)
- `overall`: `{ "r2": 0.862, "rmse": 19.96, "mae": 11.20, "n": 4820 }`
- `per_pollutant`: List of metric records for all 6 target pollutants.
- `leave_one_station_out`: Cross-validation scores across spatial holdout stations.
- `category_confusion`: $6 \times 6$ confusion matrix over CPCB categories.

---

### 2.7 Server-Side Geocoding Proxy
`GET /api/geocode`

Proxies OpenStreetMap Nominatim queries server-side to prevent client-side CORS issues and rate limits.

#### Query Parameters
- `q` (`string`, required): Search term (minimum 1 character).
- `limit` (`int`, optional, default: 5): Maximum results ($1 - 10$).

#### Response (`200 OK`)
```json
[
  {
    "display_name": "Thiruvananthapuram, Kerala, India",
    "lat": 8.5241,
    "lon": 76.9366,
    "type": "city",
    "class": "place"
  }
]
```

---

### 2.8 System Health
`GET /health`

Lightweight probe for container orchestrators and readiness monitors.

#### Response (`200 OK`)
```json
{ "status": "ok" }
```

