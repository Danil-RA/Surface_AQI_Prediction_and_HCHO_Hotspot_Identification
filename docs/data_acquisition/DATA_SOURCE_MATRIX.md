# DATA SOURCE MATRIX

| Feature | Candidate source | Exact dataset | Variable/Band | Unit | Spatial resolution | Temporal resolution | Evidence | Confidence | GEE available? |
| ------- | ---------------- | ------------- | ------------- | ---- | ------------------ | ------------------- | -------- | ---------- | -------------- |
| `AOD` | NASA MODIS | `MODIS/061/MCD19A2_GRANULES` | `Optical_Depth_047` | Unitless | 1 km | Daily | Standard for AOD | Medium | Yes |
| `NO2` | ESA Sentinel-5P | `COPERNICUS/S5P/OFFL/L3_NO2` | `NO2_column_number_density` | mol/m² | ~1113m | Daily | TROPOMI standard | High | Yes |
| `SO2` | ESA Sentinel-5P | `COPERNICUS/S5P/OFFL/L3_SO2` | `SO2_column_number_density` | mol/m² | ~1113m | Daily | TROPOMI standard | High | Yes |
| `CO` | ESA Sentinel-5P | `COPERNICUS/S5P/OFFL/L3_CO` | `CO_column_number_density` | mol/m² | ~1113m | Daily | TROPOMI standard | High | Yes |
| `O3` | ESA Sentinel-5P | `COPERNICUS/S5P/OFFL/L3_O3` | `O3_column_number_density` | mol/m² | ~1113m | Daily | TROPOMI standard | High | Yes |
| `HCHO` | ESA Sentinel-5P | `COPERNICUS/S5P/OFFL/L3_HCHO` | `tropospheric_HCHO_column_number_density`| mol/m² | ~1113m | Daily | TROPOMI standard | High | Yes |
| `AT (°C)` | ECMWF ERA5 | `ECMWF/ERA5/DAILY` | `mean_2m_air_temperature` | °C (converted) | 0.25° | Daily | Best reanalysis | High | Yes |
| `RH (%)` | ECMWF ERA5 | `ECMWF/ERA5/DAILY` | Derived from dewpoint & temp | % | 0.25° | Daily | Standard meteorology | High | Yes |
| `WS (m/s)`| ECMWF ERA5 | `ECMWF/ERA5/DAILY` | Derived from u_component & v_component | m/s | 0.25° | Daily | Standard meteorology | High | Yes |
| `WD (deg)`| ECMWF ERA5 | `ECMWF/ERA5/DAILY` | Derived from u_component & v_component | deg | 0.25° | Daily | Standard meteorology | High | Yes |
| `TOT-RF` | ECMWF ERA5 | `ECMWF/ERA5/DAILY` | `total_precipitation` | mm (converted) | 0.25° | Daily | Standard meteorology | Medium | Yes |
| `SR` | ECMWF ERA5 | `ECMWF/ERA5/DAILY` | `surface_solar_radiation_downwards` | W/m² (converted)| 0.25° | Daily | Standard meteorology | Medium | Yes |
| `BP (mmHg)`| ECMWF ERA5 | `ECMWF/ERA5/DAILY` | `surface_pressure` | mmHg (converted) | 0.25° | Daily | Standard meteorology | High | Yes |
| `VWS (m/s)`| UNKNOWN | UNKNOWN | UNKNOWN | m/s | UNKNOWN | UNKNOWN | No logical match | Low | No |
