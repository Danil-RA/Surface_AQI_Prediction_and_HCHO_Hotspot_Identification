# Scientific Methodology & Physical Framework

This document outlines the theoretical, mathematical, and algorithmic foundations governing the **Surface Air Quality Prediction** and **Formaldehyde (HCHO) Hotspot Identification** methodologies.

---

## 1. Surface AQI Prediction Methodology

### 1.1 Multi-Source Environmental Feature Engineering
Physical ground monitoring networks in developing regions are spatially sparse. To bridge this observational gap, the platform synthesizes satellite-based atmospheric column retrievals, high-resolution reanalysis meteorology, temporal harmonics, and geospatial coordinates into a unified **23-dimensional feature vector**:

| Index | Feature Key | Physical Parameter | Source Product | Nominal Units |
|:-----:|:------------|:-------------------|:---------------|:--------------|
| 1 | `AOD` | Aerosol Optical Depth (550 nm) | MODIS MAIAC (`MCD19A2`) | Dimensionless |
| 2 | `NO2` | Nitrogen Dioxide Column Density | Sentinel-5P TROPOMI (`OFFL_NO2`) | $\text{mol/m}^2$ |
| 3 | `SO2` | Sulfur Dioxide Column Density | Sentinel-5P TROPOMI (`OFFL_SO2`) | $\text{mol/m}^2$ |
| 4 | `CO` | Carbon Monoxide Column Density | Sentinel-5P TROPOMI (`OFFL_CO`) | $\text{mol/m}^2$ |
| 5 | `O3` | Ozone Column Density | Sentinel-5P TROPOMI (`OFFL_O3`) | $\text{mol/m}^2$ |
| 6 | `HCHO` | Formaldehyde Column Density | Sentinel-5P TROPOMI (`OFFL_HCHO`) | $\text{mol/m}^2$ |
| 7 | `AT (°C)` | Ambient 2-metre Temperature | ECMWF ERA5 Reanalysis | $^\circ\text{C}$ |
| 8 | `RH (%)` | Relative Humidity | ECMWF ERA5 Reanalysis | $\%$ |
| 9 | `WS (m/s)` | 10-metre Wind Speed | ECMWF ERA5 Reanalysis | $\text{m/s}$ |
| 10 | `WD (deg)` | Wind Direction | ECMWF ERA5 Reanalysis | Degrees ($^\circ$) |
| 11 | `TOT-RF (mm)`| Accumulated Total Precipitation | ECMWF ERA5 Reanalysis | $\text{mm}$ |
| 12 | `SR (W/mt2)`| Surface Solar Downward Radiation | ECMWF ERA5 Reanalysis | $\text{W/m}^2$ |
| 13 | `BP (mmHg)` | Barometric Surface Pressure | ECMWF ERA5 Reanalysis | $\text{mmHg}$ |
| 14 | `VWS (m/s)` | Vertical Wind Shear / Speed | Meteorological Derived Parameter | $\text{m/s}$ |
| 15 | `Latitude` | Spatial Coordinate | WGS84 Geodetic Datum | Decimal Degrees |
| 16 | `Longitude` | Spatial Coordinate | WGS84 Geodetic Datum | Decimal Degrees |
| 17 | `Month` | Seasonal Cycle | Calendar Extraction | $1 - 12$ |
| 18 | `DayOfWeek` | Anthropogenic Activity Proxy | Calendar Extraction | $0 - 6$ |
| 19 | `DayOfYear` | Annual Solar Insolation Phase | Calendar Extraction | $1 - 365(6)$ |
| 20 | `AOD_RH_ratio` | Hygroscopic Aerosol Growth Proxy | $\text{AOD} / (\text{RH} / 100)$ | Dimensionless |
| 21 | `U_Wind` | Zonal Wind Velocity Component | $-\text{WS} \cdot \sin(\text{WD} \cdot \pi / 180)$ | $\text{m/s}$ |
| 22 | `V_Wind` | Meridional Wind Velocity Component | $-\text{WS} \cdot \cos(\text{WD} \cdot \pi / 180)$ | $\text{m/s}$ |
| 23 | `Temp_Pressure_Ratio` | Thermal-Baric Air Density Proxy | $\text{AT} / \text{BP}$ | $^\circ\text{C / mmHg}$ |

---

### 1.2 Two-Stage Stacking Regression Ensemble
Individual machine-learning models exhibit varying inductive biases across pollutant classes. To maximize generalization across heterogeneous topography and atmospheric regimes, the platform employs a **Multi-Model Stacking Regressor** architecture:

```
[23-Feature Vector]
       │
       ├─────────────────┬─────────────────┬─────────────────┬─────────────────┐
       ▼                 ▼                 ▼                 ▼                 ▼
 ┌───────────┐     ┌───────────┐     ┌───────────┐     ┌───────────┐     ┌───────────┐
 │Extra Trees│     │  Random   │     │ Gradient  │     │  XGBoost  │     │ LightGBM  │
 │ Regressor │     │  Forest   │     │ Boosting  │     │ Regressor │     │ Regressor │
 └─────┬─────┘     └─────┬─────┘     └─────┬─────┘     └─────┬─────┘     └─────┬─────┘
       │                 │                 │                 │                 │
       └─────────────────┴─────────────────┼─────────────────┴─────────────────┘
                                           │ (Out-of-Fold Level-0 Predictions)
                                           ▼
                                 ┌───────────────────┐
                                 │  Huber Regressor  │  (Meta-Learner: Robust to Outliers)
                                 └─────────┬─────────┘
                                           │
                                           ▼
                    [Predicted Pollutant Concentration: Cp]
```

- **Level 0 (Base Learners)**:
  - `ExtraTreesRegressor`: High-variance reduction through randomized orthogonal cut points.
  - `RandomForestRegressor`: Bagged ensemble capturing non-linear interactions.
  - `GradientBoostingRegressor`: Sequential error-gradient boosting.
  - `XGBoost`: Regularized gradient boosting optimized with depth-wise tree growth.
  - `LightGBM`: Leaf-wise gradient boosting with gradient-based one-side sampling (GOSS).
- **Level 1 (Meta Learner)**:
  - `HuberRegressor`: Linear model with an $L_1/L_2$ hybrid loss function, minimizing sensitivity to seasonal concentration spikes and extreme outlier episodes.

---

### 1.3 CPCB Breakpoint Conversion & Composite AQI Determination
Predicted concentrations are converted into standardized sub-indices using the **Central Pollution Control Board (CPCB) National Air Quality Index (2014)** standard. 

#### Mathematical Formulation
The sub-index $I_p$ for pollutant $p$ with concentration $C_p$ is computed via piecewise linear interpolation between defined concentration breakpoints $[BP_{low}, BP_{high}]$ and sub-index limits $[I_{low}, I_{high}]$:

$$I_p = \left( \frac{I_{high} - I_{low}}{BP_{high} - BP_{low}} \right) \cdot (C_p - BP_{low}) + I_{low}$$

#### CPCB Breakpoint Reference Table

| CPCB AQI Category | Sub-Index Range ($I_{low} - I_{high}$) | $\text{PM}_{2.5}$ ($\mu\text{g/m}^3$) | $\text{PM}_{10}$ ($\mu\text{g/m}^3$) | $\text{NO}_2$ ($\mu\text{g/m}^3$) | $\text{SO}_2$ ($\mu\text{g/m}^3$) | $\text{CO}$ ($\text{mg/m}^3$) | $\text{O}_3$ ($\mu\text{g/m}^3$) |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Good** | $0 - 50$ | $0 - 30$ | $0 - 50$ | $0 - 40$ | $0 - 40$ | $0.0 - 1.0$ | $0 - 50$ |
| **Satisfactory** | $51 - 100$ | $31 - 60$ | $51 - 100$ | $41 - 80$ | $41 - 80$ | $1.1 - 2.0$ | $51 - 100$ |
| **Moderate** | $101 - 200$ | $61 - 90$ | $101 - 250$ | $81 - 180$ | $81 - 380$ | $2.1 - 10.0$ | $101 - 168$ |
| **Poor** | $201 - 300$ | $91 - 120$ | $251 - 350$ | $181 - 280$ | $381 - 800$ | $10.1 - 17.0$ | $169 - 208$ |
| **Very Poor** | $301 - 400$ | $121 - 250$ | $351 - 430$ | $281 - 400$ | $801 - 1600$ | $17.1 - 34.0$ | $209 - 748$ |
| **Severe** | $401 - 500$ | $251 - 380$ | $431 - 500$ | $401 - 800$ | $1601 - 2100$ | $34.1 - 50.0$ | $749 - 1000$ |

#### Overall AQI and Dominant Pollutant
Per CPCB specifications, composite AQI is governed by the **maximum sub-index**:

$$\text{Overall AQI} = \max\left( I_{\text{PM2.5}}, I_{\text{PM10}}, I_{\text{NO2}}, I_{\text{SO2}}, I_{\text{CO}}, I_{\text{O3}} \right)$$

$$\text{Dominant Pollutant} = \arg\max_p \left( I_p \right)$$

---

## 2. Formaldehyde (HCHO) Hotspot Identification Methodology

Formaldehyde ($\text{HCHO}$) serves as an essential intermediate in the atmospheric oxidation of volatile organic compounds (VOCs) and a key precursor to tropospheric ozone.

```
[Sentinel-5P TROPOMI OFFL HCHO] ──► Seasonal Aggregation (Winter, Pre-Monsoon, Monsoon, Post-Monsoon)
                                         │
                                         ▼
                             [0.25° × 0.25° Regular Grid]
                                         │
                                         ▼
                           [Getis-Ord Gi* Spatial Statistics]
                             (Spatial weights threshold: 1.5 * cell size)
                                         │
                                         ▼
                      [Hotspot Selection: Z > 1.96, p < 0.05]
                                         │
                                         ▼
                     [Contiguous Cell Dissolution & National Clipping]
                                         │
                                         ▼
             ┌───────────────────────────┴───────────────────────────┐
             ▼                                                       ▼
 [MODIS Fire Temporal Matching]                              [ERA5 Meteorological Analysis]
 (Daily overpass matching, FireMask >= 7)                    (2m Temp, RH, Wind Speed/Direction, Rain)
             │                                                       │
             └───────────────────────────┬───────────────────────────┘
                                         ▼
                            [Driver Classification]
                         - Pyrogenic Associated
                         - Non-Fire Associated
                         - Undetermined
```

### 2.1 Spatial Grid & Getis-Ord $G_i^*$ Hotspot Analysis
1. **Spatial Discretization**: India is partitioned into a regular $0.25^\circ \times 0.25^\circ$ grid spanning $8.0^\circ\text{N} - 36.0^\circ\text{N}$ and $68.0^\circ\text{E} - 96.0^\circ\text{E}$.
2. **Seasonal Composition**:
   - Winter: January – February
   - Pre-Monsoon: March – May
   - Monsoon: June – September
   - Post-Monsoon: October – December
3. **Local Spatial Autocorrelation**:
   To detect statistically significant spatial clusters of elevated HCHO against regional background noise, the platform evaluates the local Getis-Ord $G_i^*$ statistic:

   $$G_i^* = \frac{\sum_{j=1}^n w_{ij} x_j - \bar{X} \sum_{j=1}^n w_{ij}}{S \sqrt{\frac{n \sum_{j=1}^n w_{ij}^2 - \left(\sum_{j=1}^n w_{ij}\right)^2}{n - 1}}}$$

   Where:
   - $x_j$ is the seasonal mean HCHO tropospheric column density at grid location $j$.
   - $w_{ij}$ is the spatial weight matrix with a distance band threshold of $1.5 \times \text{step size}$ ($\approx 41.7\text{ km}$).
   - $\bar{X} = \frac{1}{n} \sum_{j=1}^n x_j$ is the regional sample mean.
   - $S = \sqrt{\frac{1}{n} \sum_{j=1}^n x_j^2 - \bar{X}^2}$ is the standard deviation.
4. **Significance Threshold**: Cells satisfying $Z > 1.96$ ($95\%$ statistical confidence) and $p < 0.05$ are retained as hotspot cells.
5. **Cluster Aggregation**: Contiguous significant cells are dissolved into geometric polygons and clipped against the authoritative Survey of India boundary.

---

### 2.2 MODIS Active Fire Association & Meteorological Context
For each identified hotspot cluster, a day-by-day temporal co-occurrence analysis is performed across the entire season:

1. **Fire Activity Tracking**: Daily thermal anomaly masks from **MODIS Terra/Aqua (`MOD14A1`)** are queried at $1\text{ km}$ resolution. Pixels with `FireMask >= 7` (indicating high-confidence active fire) are aggregated over the cluster boundary.
2. **Temporal Overpass Matching**: Each day with valid Sentinel-5P HCHO retrieval is evaluated for simultaneous active fire detection.
3. **Driver Classification Rules**:
   - **`pyrogenic_associated`**: Active fires are detected on $>10\%$ of valid HCHO observation days, or the total seasonal fire pixel count within the cluster exceeds $5$.
   - **`non_fire_associated`**: Statistically significant HCHO elevation persists throughout the season with $0$ active fire detections (indicating dominant contributions from biogenic emissions, industrial activity, or urban vehicle precursors).
   - **`undetermined`**: Ambiguous or intermediate conditions.

> **Scientific Attribution Note**: Correlation between satellite-detected thermal anomalies and elevated formaldehyde indicates temporal co-occurrence and plume association; it does not constitute individual source causation.

