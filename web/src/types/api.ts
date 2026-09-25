/**
 * Shared TypeScript types generated from the API contract (SPEC.md §3).
 *
 * These are the single source of truth for all API shapes in the frontend.
 * Do NOT duplicate or redefine these types elsewhere in the codebase.
 *
 * CPCB AQI categories: Good | Satisfactory | Moderate | Poor | Very Poor | Severe
 * Coverage states:     full | partial | none
 * Seasons:             winter | premonsoon | monsoon | postmonsoon
 * Variables:           aqi | pm25 | pm10 | no2 | so2 | co | o3 | hcho
 */

// ---------------------------------------------------------------------------
// Shared primitives
// ---------------------------------------------------------------------------

export type AQICategory =
  | 'Good'
  | 'Satisfactory'
  | 'Moderate'
  | 'Poor'
  | 'Very Poor'
  | 'Severe'

export type Coverage = 'full' | 'partial' | 'none'

export type Season = 'winter' | 'premonsoon' | 'monsoon' | 'postmonsoon'

export type TimeseriesVariable =
  | 'aqi'
  | 'pm25'
  | 'pm10'
  | 'no2'
  | 'so2'
  | 'co'
  | 'o3'
  | 'hcho'

export type Pollutant = 'PM2.5' | 'PM10' | 'NO2' | 'SO2' | 'CO' | 'O3'

export type HotspotDriver = 'pyrogenic_associated' | 'non_fire_associated' | 'undetermined'

// ---------------------------------------------------------------------------
// CPCB AQI colour scale (SPEC.md §6) — use these constants, not hardcoded hex
// ---------------------------------------------------------------------------

export const AQI_COLORS: Record<AQICategory | 'No coverage', string> = {
  Good:         '#55A84F',
  Satisfactory: '#A3C853',
  Moderate:     '#FFF833',
  Poor:         '#F29C33',
  'Very Poor':  '#E93F33',
  Severe:       '#AF2D24',
  'No coverage':'#6B7280', // hatch base at 35% opacity
} as const

export const AQI_BREAKPOINTS: Record<AQICategory, [number, number]> = {
  Good:         [0,   50],
  Satisfactory: [51,  100],
  Moderate:     [101, 200],
  Poor:         [201, 300],
  'Very Poor':  [301, 400],
  Severe:       [401, 500],
} as const

// ---------------------------------------------------------------------------
// GET /api/aqi
// ---------------------------------------------------------------------------

export interface Concentration {
  value: number
  unit: string
  ci_low: number
  ci_high: number
}

export interface NearestStation {
  id: string
  name: string
  distance_km: number
}

/** Full AQI response. When coverage === 'none', aqi is null — never render as zero. */
export interface AQIResponse {
  lat: number
  lon: number
  date: string           // ISO YYYY-MM-DD
  grid_cell: [number, number]
  aqi: number | null     // null when coverage === 'none'
  category: AQICategory | null
  category_color: string | null
  dominant_pollutant: Pollutant | null
  sub_indices: Partial<Record<Pollutant, number>>
  concentrations: Partial<Record<Pollutant, Concentration>>
  hcho_column: number | null
  hcho_unit: string
  coverage: Coverage
  nearest_station: NearestStation | null
}

// ---------------------------------------------------------------------------
// GET /api/timeseries
// ---------------------------------------------------------------------------

/**
 * A single point in the time series.
 * When coverage === 'none', value is null — the chart MUST break the line here.
 * Do not connect across gaps; do not interpolate.
 */
export interface TimeseriesPoint {
  date: string           // ISO YYYY-MM-DD
  value: number | null   // null = no-coverage gap
  ci_low: number | null
  ci_high: number | null
  coverage: Coverage
}

export type TimeseriesResponse = TimeseriesPoint[]

// ---------------------------------------------------------------------------
// POST /api/predict
// ---------------------------------------------------------------------------

export interface PredictionResponse {
  location: {
    latitude: number
    longitude: number
  }
  date: string
  predictions: {
    'PM2.5': number
    PM10: number
    NO2: number
    SO2: number
    O3: number
    CO: number
  }
  aqi: {
    value: number
    category: AQICategory
  }
  dominant_pollutant: Pollutant
  sub_indices: Record<Pollutant, number>
  provenance: {
    vws: {
      source: string
    }
  }
}

// ---------------------------------------------------------------------------
// GET /api/hotspots
// ---------------------------------------------------------------------------

export interface HotspotProperties {
  cluster_id: string
  gi_star: number        // Getis-Ord Gi* statistic — used for polygon opacity
  p_value: number
  mean_hcho: number      // mol/m²
  fire_count_mean: number
  fire_count_total: number
  fire_active_days: number
  fire_associated_date_fraction: number
  mean_temperature: number
  mean_relative_humidity: number
  mean_wind_speed: number
  prevailing_wind_direction: number
  mean_precipitation: number
  observation_count: number
  area_km2: number
  dominant_driver: HotspotDriver
  season: Season
  year: number
}

export interface HotspotFeature extends GeoJSON.Feature<GeoJSON.Polygon, HotspotProperties> {}

export interface HotspotsResponse extends GeoJSON.FeatureCollection<GeoJSON.Polygon, HotspotProperties> {}

// Minimal GeoJSON types (avoids adding @types/geojson as a dependency for now)
declare namespace GeoJSON {
  interface Feature<G extends Geometry, P = Record<string, unknown>> {
    type: 'Feature'
    geometry: G
    properties: P
  }
  interface FeatureCollection<G extends Geometry, P = Record<string, unknown>> {
    type: 'FeatureCollection'
    features: Feature<G, P>[]
  }
  interface Polygon {
    type: 'Polygon'
    coordinates: number[][][]
  }
  type Geometry = Polygon
}

// ---------------------------------------------------------------------------
// GET /api/stations
// ---------------------------------------------------------------------------

/**
 * A monitoring station with both observed (measured) and predicted (estimated) AQI.
 * The UI must label these distinctly — a user must never be unsure which is which.
 */
export interface StationFeature {
  station_id: string
  name: string
  lat: number
  lon: number
  date: string
  observed_aqi: number | null    // measured — label as "Measured"
  predicted_aqi: number | null   // model estimate — label as "Estimated"
  bias: number | null            // predicted - observed
}

export type StationsResponse = StationFeature[]

// ---------------------------------------------------------------------------
// GET /api/validation
// ---------------------------------------------------------------------------

export interface Metrics {
  r2: number
  rmse: number
  mae: number
  n: number
}

export interface PollutantMetrics extends Metrics {
  pollutant: Pollutant
}

export interface LeaveOneOut {
  station_id: string
  name: string
  r2: number
  rmse: number
  n: number
}

export interface ScatterPoint {
  observed: number
  predicted: number
  pollutant: Pollutant
}

export interface CategoryConfusion {
  labels: AQICategory[]
  matrix: number[][]
}

export interface ValidationResponse {
  overall: Metrics
  per_pollutant: PollutantMetrics[]
  leave_one_station_out: LeaveOneOut[]  // sorted worst-first (lowest r2)
  scatter: ScatterPoint[]
  category_confusion: CategoryConfusion
}

// ---------------------------------------------------------------------------
// UI-only types (not API shapes)
// ---------------------------------------------------------------------------

export type LayerKey =
  | 'aqi'
  | 'pm25' | 'pm10' | 'no2' | 'so2' | 'co' | 'o3'
  | 'hcho'
  | 'hotspots'
  | 'fires'

/** URL view state — everything needed to restore a view from the address bar */
export interface ViewState {
  lat: number
  lon: number
  zoom: number
  date: string           // ISO YYYY-MM-DD
  layer: LayerKey
}
