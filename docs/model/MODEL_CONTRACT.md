# MODEL CONTRACT

This document outlines the exact input features required by the `multi_pollutant_stacking_pipeline.pkl` model, their intended units, and their likely sources.

| # | Feature | Exact model column | Unit | Role | Required at inference? | Source certainty |
| - | ------- | ------------------ | ---- | ---- | ---------------------- | ---------------- |
| 1 | AOD | `AOD` | Unitless | Satellite Aerosol | Yes | LIKELY_SOURCE |
| 2 | Nitrogen Dioxide | `NO2` | mol/m² (likely) | Satellite Gas | Yes | LIKELY_SOURCE |
| 3 | Sulfur Dioxide | `SO2` | mol/m² (likely) | Satellite Gas | Yes | LIKELY_SOURCE |
| 4 | Carbon Monoxide | `CO` | mol/m² (likely) | Satellite Gas | Yes | LIKELY_SOURCE |
| 5 | Ozone | `O3` | mol/m² (likely) | Satellite Gas | Yes | LIKELY_SOURCE |
| 6 | Formaldehyde | `HCHO` | mol/m² (likely) | Satellite Gas | Yes | LIKELY_SOURCE |
| 7 | Ambient Temperature | `AT (°C)` | °C | Meteorology | Yes | KNOWN_SOURCE |
| 8 | Relative Humidity | `RH (%)` | % | Meteorology | Yes | KNOWN_SOURCE |
| 9 | Wind Speed | `WS (m/s)` | m/s | Meteorology | Yes | KNOWN_SOURCE |
| 10 | Wind Direction | `WD (deg)` | Degrees | Meteorology | Yes | KNOWN_SOURCE |
| 11 | Total Rainfall | `TOT-RF (mm)` | mm | Meteorology | Yes | LIKELY_SOURCE |
| 12 | Solar Radiation | `SR (W/mt2)` | W/m² | Meteorology | Yes | LIKELY_SOURCE |
| 13 | Barometric Pressure | `BP (mmHg)` | mmHg | Meteorology | Yes | LIKELY_SOURCE |
| 14 | Vertical Wind Speed/Shear | `VWS (m/s)` | m/s | Meteorology | Yes | SOURCE_UNKNOWN |
| 15 | Latitude | `Latitude` | Decimal Degrees | Spatial | Yes | KNOWN_SOURCE |
| 16 | Longitude | `Longitude` | Decimal Degrees | Spatial | Yes | KNOWN_SOURCE |
| 17 | Month | `Month` | 1-12 | Temporal | Yes | KNOWN_SOURCE |
| 18 | Day of Week | `DayOfWeek` | 0-6 | Temporal | Yes | KNOWN_SOURCE |
| 19 | Day of Year | `DayOfYear` | 1-365(6) | Temporal | Yes | KNOWN_SOURCE |
| 20 | AOD/RH Ratio | `AOD_RH_ratio` | Unitless | Engineered Feature | Yes | LIKELY_SOURCE |
| 21 | U-Component of Wind | `U_Wind` | m/s | Engineered Feature | Yes | SOURCE_UNKNOWN |
| 22 | V-Component of Wind | `V_Wind` | m/s | Engineered Feature | Yes | SOURCE_UNKNOWN |
| 23 | Temp to Pressure Ratio | `Temp_Pressure_Ratio`| °C/mmHg | Engineered Feature | Yes | LIKELY_SOURCE |

### Temporal Semantics
*   **Missing Information:** It is completely unknown whether the satellite and meteorological variables represent a daily mean, a daily maximum, an overpass value, or a 24-hour average.
*   *Assumption for implementation:* A 24-hour daily mean is the most standard aggregation for daily AQI prediction.

### Spatial Semantics
*   **Missing Information:** The spatial aggregation technique (nearest neighbor vs. spatial averaging) and the grid resolution of the original training data are unknown.
*   *Assumption for implementation:* Extracting the value of the grid cell (pixel) containing the target latitude/longitude.
