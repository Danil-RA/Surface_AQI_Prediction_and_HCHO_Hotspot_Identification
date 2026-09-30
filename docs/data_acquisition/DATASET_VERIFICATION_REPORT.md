# DATASET VERIFICATION REPORT

This report verifies the accessibility, units, and extraction properties of the candidate datasets for the requested coordinates (`8.523, 76.941`) on `2026-03-15`.

## A. AOD (Aerosol Optical Depth)

| Property | Value | Status |
| :--- | :--- | :--- |
| **Model Feature** | `AOD` | |
| **Dataset ID** | `MODIS/061/MCD19A2_GRANULES` | DOCUMENTED DATASET PROPERTY |
| **Band/Variable** | `Optical_Depth_047` | DOCUMENTED DATASET PROPERTY |
| **Native Units** | Unitless | VERIFIED FACT |
| **Scale factor** | `0.001` (Must multiply raw value by 0.001) | VERIFIED FACT |
| **Temporal resolution** | Daily | VERIFIED FACT |
| **Spatial resolution** | 1000m | VERIFIED FACT |
| **Quality filtering** | Use `AOD_QA` band to filter out clouds | OUR RECONSTRUCTION ASSUMPTION |
| **Extraction method** | `reduceRegion(first, 1000m)` | OUR RECONSTRUCTION ASSUMPTION |
| **Test-date availability**| Missing/Masked for this specific pixel/date | VERIFIED FACT |
| **Raw test value** | `null` | VERIFIED FACT |
| **Converted test value**| `null` | VERIFIED FACT |

## B. Satellite trace gases

| Model Feature | Dataset ID | Band/Variable | Native Units | Scale Factor | Extracted Value | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `NO2` | `COPERNICUS/S5P/OFFL/L3_NO2` | `NO2_column_number_density` | mol/m² | None | `null` (cloud mask) | VERIFIED FACT |
| `SO2` | `COPERNICUS/S5P/OFFL/L3_SO2` | `SO2_column_number_density` | mol/m² | None | `null` (cloud mask) | VERIFIED FACT |
| `CO`  | `COPERNICUS/S5P/OFFL/L3_CO` | `CO_column_number_density` | mol/m² | None | `null` (cloud mask) | VERIFIED FACT |
| `O3`  | `COPERNICUS/S5P/OFFL/L3_O3` | `O3_column_number_density` | mol/m² | None | `null` (cloud mask) | VERIFIED FACT |
| `HCHO`| `COPERNICUS/S5P/OFFL/L3_HCHO` | `tropospheric_HCHO_column_number_density` | mol/m² | None | `null` (cloud mask) | VERIFIED FACT |

**Notes:** 
* The units exactly match the expected scale (mol/m²).
* Sentinel-5P OFFL products have rigorous internal cloud masking (qa_value > 0.5 or 0.75). The query executed successfully, but returned `null` for `8.523, 76.941` on `2026-03-15`, proving that spatial averaging or temporal buffering is required to avoid missing data.

## C. Meteorology

| Model Feature | Candidate Dataset ID | Band/Variable | Native Units | Status |
| :--- | :--- | :--- | :--- | :--- |
| `AT (°C)` | `ECMWF/ERA5/DAILY` (Deprecated) | `mean_2m_air_temperature` | K | NEEDS INVESTIGATION |
| `RH (%)`  | `ECMWF/ERA5/DAILY` (Deprecated) | `dewpoint_2m_temperature` | K | NEEDS INVESTIGATION |
| `WS (m/s)`| `ECMWF/ERA5/DAILY` (Deprecated) | `u/v_component_of_wind_10m` | m/s | NEEDS INVESTIGATION |
| `WD (deg)`| `ECMWF/ERA5/DAILY` (Deprecated) | `u/v_component_of_wind_10m` | m/s | NEEDS INVESTIGATION |
| `TOT-RF`  | `ECMWF/ERA5/DAILY` (Deprecated) | `total_precipitation` | meters | NEEDS INVESTIGATION |
| `SR`      | `ECMWF/ERA5/DAILY` (Deprecated) | `surface_solar_radiation_downwards` | J/m² | NEEDS INVESTIGATION |
| `BP`      | `ECMWF/ERA5/DAILY` (Deprecated) | `surface_pressure` | Pa | NEEDS INVESTIGATION |

**Critical Finding:** The `ECMWF/ERA5/DAILY` dataset is deprecated in Google Earth Engine and does not have data for 2026. Querying it returned an explicit error: `Image.reduceRegion: Parameter 'image' is required and may not be null.`
*   **Resolution Required:** We must switch to `ECMWF/ERA5_LAND/HOURLY` and write custom Earth Engine reducers to aggregate the 24 hourly images into a daily mean/sum for inference. 
*   **Conversion Required:** Temp (K to °C), Precip (m to mm), Solar Radiation (J/m² to W/m²), Pressure (Pa to mmHg).

## D. Wind
*   **Source:** U and V components are provided natively by ERA5 in m/s.
*   **Formulas Required:** 
    * `WS = sqrt(U^2 + V^2)`
    * `WD = atan2(-U, -V) * (180/pi)` (Meteorological convention: angle from which wind is blowing).
*   **Status:** The exact original training convention remains an assumption, but the meteorological standard is the most defensible choice.

## E. VWS (Vertical Wind Speed)
*   **Variable:** `vertical_velocity` (Omega).
*   **Units:** Pa/s.
*   **Meaning:** Rate of pressure change for an air parcel.
*   **Status:** `VWS_STATUS = UNRESOLVED`. It is not present in ERA5-Land (surface), and converting from atmospheric pressure levels (which are also deprecated in the standard monthly collection) to m/s requires unjustifiable physics assumptions (density, specific altitude level).

---

### VERIFIED
*   **AOD & Trace Gases:** The dataset IDs, bands, units, and scale factors for MODIS AOD and Sentinel-5P trace gases are confirmed. The extraction code correctly hits the Google Earth Engine API.

### NEEDS INVESTIGATION
*   **Meteorology (All Surface Variables):** The candidate dataset `ECMWF/ERA5/DAILY` is outdated/deprecated and lacks 2026 data. We must pivot to `ECMWF/ERA5_LAND/HOURLY` and implement manual daily aggregation (Mean for Temp/Pressure/Wind, Sum for Precipitation/Radiation).

### UNRESOLVED
*   **VWS:** `VWS (m/s)` cannot be defensibly mapped to a Google Earth Engine dataset. 
*   **Missing Pixel Handling:** Sentinel-5P and MODIS returned `null` for the exact test point due to cloud masking. A spatial averaging buffer (e.g., 5km - 10km radius) or temporal interpolation is required, or else the model will crash on missing inputs.
