# Surface AQI & HCHO Hotspots — Frontend Specification

Reference document for the build. Treat every constraint here as binding unless
explicitly marked optional.

---

## 1. What this application is

A research web application that displays model-estimated ground-level air quality
across a region where physical monitoring stations are sparse. It shows two things:

1. **Surface AQI** — estimated from satellite and meteorological predictors, mapped
   over a continuous grid, including areas with no monitoring station.
2. **HCHO hotspots** — regions of persistently elevated atmospheric formaldehyde,
   with their relationship to biomass-burning and meteorological drivers.

The audience is environmental researchers, pollution-control board staff, and
academic reviewers. Not the general public. This means: show uncertainty, show
validation, do not round away detail to look tidier than the data is.

Primary job of the interface: let someone judge whether the estimates are
trustworthy, and then use them.

---

## 2. Architecture

```
  Offline batch (already done / done separately)
      trained per-pollutant stacked ensembles
                  |
                  v
      grid predictions -> COG rasters + DuckDB/Parquet table
      HCHO hotspots    -> simplified GeoJSON
                  |
   -------------------------------
   |                             |
   v                             v
  Static assets              FastAPI (thin)
  (object storage/CDN)       reads Parquet/DuckDB
   - AQI raster tiles         - /api/aqi
   - pollutant tiles          - /api/timeseries
   - hotspots.geojson         - /api/hotspots
   - stations.json            - /api/stations
                              - /api/validation
   -------------------------------
                  |
                  v
          React + Vite frontend
```

**Models are never loaded at request time.** No `joblib.load` in any route
handler. If a value isn't in the pre-computed store, the API returns a
"no coverage" response and the UI says so.

---

## 3. API contract

Base path `/api`. All responses JSON. All dates ISO `YYYY-MM-DD`.

### `GET /aqi?lat={float}&lon={float}&date={date}`
```json
{
  "lat": 8.52, "lon": 76.94, "date": "2023-03-14",
  "grid_cell": [142, 87],
  "aqi": 168,
  "category": "Moderate",
  "dominant_pollutant": "PM2.5",
  "sub_indices": {
    "PM2.5": 168, "PM10": 121, "NO2": 44,
    "SO2": 19, "CO": 31, "O3": 58
  },
  "concentrations": {
    "PM2.5": {"value": 78.4, "unit": "ug/m3", "ci_low": 61.2, "ci_high": 95.6}
  },
  "hcho_column": 1.42e-4,
  "hcho_unit": "mol/m2",
  "coverage": "full",
  "nearest_station": {"id": "KL007", "name": "...", "distance_km": 6.2}
}
```
`coverage` is one of `full`, `partial`, `none`. When `none`, `aqi` is `null` —
the UI must handle this, not crash or render zero.

### `GET /timeseries?lat=&lon=&from=&to=&variable=aqi|pm25|hcho|...`
Array of `{date, value, ci_low, ci_high, coverage}`. Gaps are returned as
entries with `value: null`, not omitted — the chart needs to break the line.

### `GET /hotspots?season=winter|premonsoon|monsoon|postmonsoon&year=`
GeoJSON `FeatureCollection`. Each feature carries `gi_star`, `p_value`,
`mean_hcho`, `fire_count_mean`, `dominant_driver`
(`pyrogenic` | `biogenic` | `mixed` | `undetermined`).

### `GET /stations`
Station locations with `observed_aqi` and `predicted_aqi` for a given date.

### `GET /validation`
```json
{
  "overall": {"r2": 0.82, "rmse": 18.4, "mae": 13.1, "n": 7320},
  "per_pollutant": [{"pollutant": "PM2.5", "r2": 0.79, "rmse": 21.2, "mae": 15.8}],
  "leave_one_station_out": [{"station_id": "KL007", "name": "...", "r2": 0.71, "rmse": 22.9, "n": 366}],
  "scatter": [{"observed": 142, "predicted": 151, "pollutant": "PM2.5"}],
  "category_confusion": {"labels": ["Good", "..."], "matrix": [[...]]}
}
```

---

## 4. Screens

### 4.1 Map (default route `/`)
- Full-bleed MapLibre GL map, basemap muted so the data layer carries the colour.
- **Date control**: a scrubbable timeline along the bottom. Dates with no
  satellite coverage are visibly marked on the track itself — the user should
  see the gaps before clicking into one.
- **Layer switch**: AQI (default), individual pollutant sub-index, HCHO column,
  hotspot overlay, active-fire points. Layers stack; AQI and pollutant are
  mutually exclusive.
- **Click anywhere** -> detail panel (4.2).
- **Station markers** always visible, distinct from grid data. Clicking a station
  shows observed vs predicted for that date.
- **Legend** is permanent, not a hover tooltip.

### 4.2 Location detail panel
Slides in over the map, does not navigate away.
- AQI number, category, dominant pollutant.
- All six sub-indices as a horizontal bar chart, each bar coloured by its own
  category, with the dominant one marked.
- Concentration values with confidence interval.
- Mini time series (30 days around the selected date), expandable to the full
  series view.
- Distance to nearest station, and that station's observed value if available.
  This is the trust signal — do not bury it.

### 4.3 HCHO hotspots (`/hotspots`)
- Hotspot polygons over the map, opacity keyed to Gi* significance.
- Season selector.
- Side panel: ranked cluster table (location, mean HCHO, seasonality, dominant
  driver, fire correlation coefficient).
- One chart: lagged correlation of HCHO against fire count at lags 0-3 days.

### 4.4 Validation (`/validation`)
This page is the argument for the whole project. Give it room.
- Observed vs predicted scatter, 1:1 line drawn, per-pollutant filter.
- Per-pollutant metrics table.
- Leave-one-station-out table, sorted worst-first by default. Do not hide the
  bad stations.
- AQI category confusion matrix.
- Residual distribution.

### 4.5 Method (`/method`)
Plain-language description of data sources, model, AQI derivation, and known
limitations. Written for a reviewer who has not read the paper. Include the
limitations honestly: cloud-gap loss in monsoon months, HCHO signal-to-noise at
daily resolution, spatial extrapolation beyond the training station footprint.

---

## 5. Non-negotiable data rules

1. **The frontend never computes AQI.** Sub-index breakpoint logic lives in
   Python, server-side, in one module. No breakpoint tables in JavaScript.
2. **CPCB categories are discrete bands, not a gradient.** The colour scale must
   step at the breakpoints. Do not interpolate a smooth ramp across
   Good/Satisfactory/Moderate/Poor/Very Poor/Severe.
3. **Missing is missing.** Cloud-gap cells render as an explicit "no coverage"
   treatment distinguishable from low AQI. Never fill with zero, never
   interpolate across a gap without labelling it as interpolated.
4. **Uncertainty is displayed, not stored and ignored.** Every point estimate
   that has a CI shows it. Time series show a CI band.
5. **Predicted is labelled predicted.** Anywhere a model estimate sits next to a
   station observation, the two are visually distinguishable without reading a
   legend.

---

## 6. Design direction

The subject is atmospheric measurement over land — satellite retrievals, sparse
ground truth, physical uncertainty. The interface should feel like an instrument
readout, not a consumer weather app and not a generic analytics dashboard.

**Palette.** The AQI scale is fixed by CPCB and owns all the saturation on the
page. Everything else must recede so the data layer reads correctly against the
map. Build the chrome from a cool desaturated base — deep slate through pale
grey-blue — and let the only strong colour come from the data itself. Do not
introduce a brand accent that competes with the AQI ramp.

CPCB AQI colours (use exactly these, they are a published standard):
```
Good           0-50     #55A84F
Satisfactory   51-100   #A3C853
Moderate       101-200  #FFF833
Poor           201-300  #F29C33
Very Poor      301-400  #E93F33
Severe         401-500  #AF2D24
No coverage    -        diagonal hatch on #6B7280, 35% opacity
```

**Typography.** One text family with genuine small-size legibility plus a
tabular-figure face for numerics — readouts, metrics tables, coordinates.
Numbers in tables must align on the decimal. Do not use a monospace face for
labels as decoration; use it where tabular alignment actually matters.

**Layout.** Map-first. The map is the page, panels overlay it. Avoid chopping the
analysis pages into a grid of identical rounded cards — the validation page is a
sequence of arguments and should read as one, with the scatter plot large enough
to actually inspect.

**Motion.** Panel open/close and layer crossfade only. No entrance animations on
page sections, no hover lift on every element.

**Avoid:** warm cream backgrounds with terracotta accents; all-caps tracked-out
eyebrow labels above headings; `01 / 02 / 03` numbered markers on content that
is not a sequence; arrow glyphs appended to button text; a soft grey drop shadow
under every container.

---

## 7. Quality floor

- Responsive to tablet. The map view degrades gracefully on phone (detail panel
  becomes a bottom sheet); the validation page may be desktop-first.
- Visible keyboard focus on every interactive element. The map must be
  keyboard-navigable to at least the layer and date controls.
- `prefers-reduced-motion` respected.
- The AQI colour scale is not the only carrier of meaning — category names appear
  as text wherever a colour is used to classify.
- Loading states show what is loading. Empty and error states say what happened
  and what to do.

---

## 8. Stack

- React 18 + TypeScript + Vite
- MapLibre GL JS (no Mapbox token)
- Recharts for charts
- TanStack Query for API state and caching
- Tailwind for styling, with the palette above as design tokens
- FastAPI + DuckDB backend
- No global state library. Query cache plus URL params is enough.

URL carries view state: `/?lat=8.52&lon=76.94&date=2023-03-14&layer=aqi`
so any view is shareable and citable in a paper.

---

## 9. Build order

Ship each step working before starting the next.

1. Map renders with one static AQI layer for one date, with legend.
2. Date timeline and layer switching.
3. Click to detail panel, wired to `/api/aqi`.
4. Time series with CI band and coverage gaps.
5. Station markers with observed vs predicted.
6. HCHO hotspots page.
7. Validation page.
8. Method page, responsive pass, accessibility pass.
