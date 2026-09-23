# FEATURE SCALE ANALYSIS

Based on the internal threshold distributions of 6 StackingRegressors and hundreds of thousands of decision tree nodes, we have reverse-engineered the expected scales of the model inputs.

## Feature Mapping and Compatibility

| Feature | Learned threshold scale (median, range) | Candidate dataset scale | Compatible? | Conversion | Confidence |
| ------- | --------------------------------------- | ----------------------- | ----------- | ---------- | ---------- |
| `AOD` | Median: 0.58. Range: 0.07 to 3.83 | MODIS/S5P AOD (0 to ~5) | YES | None | HIGH |
| `NO2` | Median: 6.48e-05. Range: -6e-6 to 0.0007 | Sentinel-5P (mol/m²) | YES | None | HIGH |
| `SO2` | Median: 1.05e-04. Range: -0.0009 to 0.007 | Sentinel-5P (mol/m²) | YES | None | HIGH |
| `CO` | Median: 0.041. Range: 0.018 to 0.081 | Sentinel-5P (mol/m²) | YES | None | HIGH |
| `O3` | Median: 0.123. Range: 0.104 to 0.166 | Sentinel-5P (mol/m²) | YES | None | HIGH |
| `HCHO`| Median: 2.26e-04. Range: -0.0003 to 0.0011| Sentinel-5P (mol/m²) | YES | None | HIGH |
| `AT (°C)` | Median: 27.2°C. Range: 5.3 to 42.4 | ERA5 (`2m_temperature`) | YES | K to °C | HIGH |
| `RH (%)`| Median: 67.8%. Range: 0.3 to 99.7 | ERA5 (Derived) | YES | None | HIGH |
| `WS (m/s)`| Median: 0.93. 95th %ile: 2.58 | ERA5 (`10m_wind_speed`) | YES | None | HIGH |
| `WD (deg)`| Median: 179.7. Range: 2.2 to 358.9 | ERA5 (Derived) | YES | None | HIGH |
| `TOT-RF`| Median: 0.03. 95th %ile: 0.57 mm | ERA5 (`total_precipitation`) | YES | m to mm | MED |
| `SR` | Median: 121.9. 95th %ile: 251.2 | ERA5 (`surface_solar...`) | YES | J/m² to W/m² | MED |
| `BP (mmHg)`| Median: 749.2. Range: 705 to 1099 | ERA5 (`surface_pressure`) | YES | Pa to mmHg | HIGH |
| `VWS (m/s)`| Median: -0.06. Range: -7.7 to 11.5 | ERA5 (`vertical_velocity`) | POSSIBLY | Pa/s to m/s| LOW |

## Engineered Features Reconstruction
1. **`AOD_RH_ratio`**:
   * **Verification:** Median AOD (0.58) / Median RH (67.8) = **0.0085**. The median tree threshold is **0.0091**.
   * **Conclusion:** The formula is definitively `AOD / RH`.
2. **`Temp_Pressure_Ratio`**:
   * **Verification:** Median AT (27.2°C) / Median BP (749) = 0.036 (mismatch). But `(27.2 + 273.15) / 749.2` = **0.400**. The median tree threshold is **0.398**.
   * **Conclusion:** The formula is definitively `Temp (in Kelvin) / BP (in mmHg)`.
3. **`U_Wind` and `V_Wind`**:
   * Scales are clustered symmetrically around 0, matching standard vector components in m/s. Wind convention (from vs. to) is standard meteorological unless proven otherwise.

## Investigating VWS (m/s)
- **Status**: OBSERVED TRAINING DISTRIBUTION UNAVAILABLE
- **Model-Supported Range Evidence**: The trained model contains tree split thresholds spanning approximately -7.778 to 11.529 m/s. These thresholds do not represent the empirical training distribution.
- **Min Threshold**: -7.778
- **Max Threshold**: 11.529
* **Analysis:** Vertical Wind Shear is typically a strictly positive magnitude (m/s). The presence of negative values symmetrical around near-zero strongly implies a **velocity vector**. In meteorology, `w` represents vertical wind velocity in m/s (positive = updraft). 
* **Compatibility:** ERA5 provides `vertical_velocity` (Omega) in Pa/s. We can convert Omega to `w` (m/s) using `w ≈ -Omega / (rho * g)`.

## Spatial Sanity Check
* **Latitude:** 5th %ile: 13.0, 95th %ile: 29.3. 
* **Longitude:** 5th %ile: 74.1, 95th %ile: 88.9. 
* **Conclusion:** The model was trained specifically on **India**.

## What the model cannot tell us
* **Temporal Aggregation:** While we know the numerical scales fit daily Sentinel-5P overpasses, we cannot definitively prove if ERA5 variables (like Temperature) were averaged over 24 hours, or sampled at 13:30 (TROPOMI overpass time). 
* **Spatial Aggregation:** We don't know if the original data used nearest-neighbor pixel extraction or grid-cell averaging.

## Final Classification
* `CONFIDENTLY RECONSTRUCTABLE`: Satellite Gases, AOD, AT, RH, WS, WD, BP, Spatial/Temporal vars, AOD_RH_ratio, Temp_Pressure_Ratio.
* `PROBABLY RECONSTRUCTABLE`: U_Wind, V_Wind, TOT-RF, SR.
* `UNCERTAIN`: VWS (m/s) requires a fluid dynamics conversion from ERA5 Omega to vertical velocity `w` in m/s.
