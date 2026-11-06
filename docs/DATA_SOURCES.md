# Atmospheric & Earth Observation Data Sources

This document describes the primary data products, remote sensing instruments, meteorological reanalysis models, and ground monitoring datasets integrated into the **Surface Air Quality Prediction and HCHO Hotspot Identification Platform**.

---

## 1. Summary Matrix

| Data Product | Providing Agency | Platform / Sensor | Spatial Resolution | Temporal Frequency | Primary Variables Used |
|:---|:---|:---|:---:|:---:|:---|
| **CAAQMS Ground Truth** | Central Pollution Control Board (CPCB) | In-situ Air Quality Stations | Point-based | 15-min / 1-hour / 24-hour | $\text{PM}_{2.5}$, $\text{PM}_{10}$, $\text{NO}_2$, $\text{SO}_2$, $\text{CO}$, $\text{O}_3$ |
| **Sentinel-5P TROPOMI** | ESA / Copernicus Programme | Sentinel-5 Precursor | $3.5 \times 5.5\text{ km}$ ($7 \times 3.5\text{ km}$ prior to 08/2019) | Daily Overpass (~13:30 LT) | $\text{NO}_2$, $\text{SO}_2$, $\text{CO}$, $\text{O}_3$, $\text{HCHO}$ column densities |
| **MODIS MAIAC AOD** | NASA EOSDIS | Terra & Aqua / MODIS | $1\text{ km}$ grid | Daily Overpass (10:30 & 13:30 LT) | Aerosol Optical Depth (550 nm, `Optical_Depth_055`) |
| **ERA5 / ERA5-Land** | ECMWF / Copernicus Climate Change | Global Atmospheric Reanalysis | $0.25^\circ \times 0.25^\circ$ (~$28\text{ km}$) / $0.1^\circ$ (~$9\text{ km}$) | Hourly / Daily Aggregates | 2m Temperature, Dewpoint, Surface Pressure, 10m Wind ($u, v$), Precipitation, Solar Radiation |
| **MODIS Thermal Anomalies** | NASA EOSDIS | Terra & Aqua / MODIS | $1\text{ km}$ pixel | Daily | Fire Mask (`FireMask`), Active Fire Detection |

---

## 2. In-Situ Ground Monitoring Network

### Central Pollution Control Board (CPCB) Continuous Ambient Air Quality Monitoring Stations (CAAQMS)
- **Authority**: Central Pollution Control Board, Ministry of Environment, Forest and Climate Change (MoEFCC), Government of India.
- **Coverage**: Over 400 continuous automated monitoring stations situated across metro, urban, industrial, and suburban zones throughout India.
- **Instruments & Measurement Methods**:
  - $\text{PM}_{2.5}$ & $\text{PM}_{10}$: Beta Attenuation Monitors (BAM) or Tapered Element Oscillating Microbalance (TEOM).
  - $\text{NO}_2$: Chemiluminescence analyzers.
  - $\text{SO}_2$: Ultraviolet fluorescence analyzers.
  - $\text{CO}$: Non-dispersive infrared (NDIR) gas correlation filter analyzers.
  - $\text{O}_3$: Ultraviolet photometric analyzers.
- **Role in Platform**: Provides the empirical ground truth for model training, leave-one-station-out cross-validation, and operational residual evaluation.

---

## 3. Satellite Remote Sensing Retrievals

### 3.1 Sentinel-5P TROPOMI Atmospheric Column Densities
- **Instrument**: TROPOspheric Monitoring Instrument (TROPOMI) on the ESA Copernicus Sentinel-5 Precursor satellite.
- **Bands & Products**:
  - **$\text{NO}_2$** (`COPERNICUS/S5P/OFFL/L3_NO2`): Tropospheric $\text{NO}_2$ column density ($\text{mol/m}^2$). Screened with quality assurance value $qa\_value > 0.5$ and cloud radiance fraction $< 0.5$.
  - **$\text{SO}_2$** (`COPERNICUS/S5P/OFFL/L3_SO2`): Total vertical column density of $\text{SO}_2$ assuming a planetary boundary layer profile centered at $1\text{ km}$ altitude.
  - **$\text{CO}$** (`COPERNICUS/S5P/OFFL/L3_CO`): Vertically integrated carbon monoxide total column density ($\text{mol/m}^2$).
  - **$\text{O}_3$** (`COPERNICUS/S5P/OFFL/L3_O3`): Ozone total column density ($\text{mol/m}^2$) derived from ultraviolet Hartley and Huggins bands.
  - **$\text{HCHO}$** (`COPERNICUS/S5P/OFFL/L3_HCHO`): Tropospheric formaldehyde column density ($\text{mol/m}^2$) derived through non-linear least squares fitting in the UV spectral range ($328.5 - 359\text{ nm}$).

### 3.2 MODIS MAIAC Aerosol Optical Depth (AOD)
- **Product ID**: `MODIS/061/MCD19A2_GRANULES`
- **Algorithm**: Multi-Angle Implementation of Atmospheric Correction (MAIAC) utilizing time series analysis and spatial surface reflectance ratio modeling.
- **Band**: `Optical_Depth_055` (Aerosol Optical Depth at $550\text{ nm}$).
- **Quality Screening**: Cloud-screened, water-masked, quality-assured retrievals over both bright desert surfaces and dark vegetated targets. Multiplied by internal scale factor ($0.001$).

### 3.3 MODIS Active Fire & Thermal Anomalies
- **Product ID**: `MODIS/061/MOD14A1`
- **Detection Algorithm**: Uses contextual brightness temperature differences between $4\text{ }\mu\text{m}$ (channel 21/22) and $11\text{ }\mu\text{m}$ (channel 31) to identify sub-pixel combustion.
- **Classification Criterion**: Pixels with `FireMask >= 7` indicate low, nominal, or high confidence active flaming or smoldering combustion.

---

## 4. Meteorological Reanalysis Models

### ECMWF ERA5 & ERA5-Land Reanalysis
- **Provider**: European Centre for Medium-Range Weather Forecasts (ECMWF) via Copernicus Climate Change Service (C3S).
- **Core Parameters**:
  - `temperature_2m` ($^\circ\text{C}$): Ambient air temperature at $2\text{ m}$ height above surface.
  - `dewpoint_temperature_2m` ($^\circ\text{C}$): Dewpoint temperature used to calculate surface relative humidity ($RH$).
  - `surface_pressure` ($\text{mmHg}$): Absolute atmospheric barometric pressure at ground surface level.
  - `u_component_of_wind_10m` & `v_component_of_wind_10m` ($\text{m/s}$): Zonal (east-west) and meridional (north-south) wind vectors at $10\text{ m}$ elevation.
  - `total_precipitation` ($\text{mm}$): Accumulated rain and snowfall over the forecast cycle.
  - `surface_solar_radiation_downwards` ($\text{W/m}^2$): Direct and diffuse solar insolation reaching the surface.

---

## 5. Data Access & Acquisition Pipelines

The platform interfaces with remote sensing providers via:
1. **Google Earth Engine (GEE)** Python API: Server-side parallel spatial extraction and zonal statistics over satellite image collections (`MOD19A2`, `S5P/OFFL`, `MOD14A1`, `ERA5`).
2. **Open-Meteo & CDS APIs**: Near-real-time atmospheric reanalysis retrieval fallbacks.
3. **OpenStreetMap Nominatim**: Reverse and forward geocoding service queried under Open Database License (ODbL) terms.

---

## 6. Citations & Attribution

- **CPCB Data**: Central Pollution Control Board, Government of India (https://cpcb.nic.in / https://app.cpcbccr.com).
- **Copernicus Sentinel-5P**: Contains modified Copernicus Sentinel data processed by the European Space Agency (ESA).
- **MODIS MAIAC & Fire**: NASA EOSDIS Land Processes Distributed Active Archive Center (LP DAAC), USGS Earth Resources Observation and Science (EROS) Center, Sioux Falls, South Dakota.
- **ERA5 Reanalysis**: Hersbach, H., et al. (2020). "The ERA5 global reanalysis." *Quarterly Journal of the Royal Meteorological Society*, 146(730), 1999-2049.

