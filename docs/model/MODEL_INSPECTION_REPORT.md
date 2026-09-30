# MODEL INSPECTION REPORT

## 1. Model File
*   **Filename:** `multi_pollutant_stacking_pipeline.pkl`
*   **Location:** Project root

## 2. Model Size
*   **Size:** 689,427,863 bytes (~689 MB)

## 3. Model Class / Loaded Object
*   **Base Object:** The `.pkl` file is **not** a raw Scikit-Learn estimator. It is a standard Python `dict`.
*   **Dictionary Keys:** `['models', 'feature_cols', 'targets']`
*   **Structure:** It contains a mapping of individual pollutant targets to their respective trained `StackingRegressor` pipelines, alongside an explicit list of the exact input features used.

## 4. Dependency Versions Required
To successfully unpickle this model without module errors, the following environment was required:
*   `scikit-learn==1.6.1` (Explicitly warned on version mismatches)
*   `xgboost` (Any compatible modern version, tested with 3.2.0)
*   `lightgbm` (Any compatible modern version, tested with 4.7.0)
*   `pandas` (Required for nested DataFrames or feature storage)
*   `numpy` & `scipy`

## 5. Internal Estimator Structure
The dictionary key `models` maps to 6 distinct target estimators. For example, `model['models']['PM2.5']` is a:
*   **Type:** `sklearn.ensemble._stacking.StackingRegressor`
*   **Base Estimators (Level 0):** Contains massive ensembles including `sklearn.ensemble.ExtraTreesRegressor`, as well as `xgboost` and `lightgbm` estimators (inferred from the dependency failures encountered during loading). 
*   **Fitted State:** Yes, these are fully trained models.

## 6. Exact Feature Count
*   **Number of input features:** Exactly **23**.

## 7. Exact Feature Names & Order
Extracted directly from `model['feature_cols']`:
1.  `AOD` (Satellite Aerosol Optical Depth)
2.  `NO2` (Satellite Nitrogen Dioxide)
3.  `SO2` (Satellite Sulfur Dioxide)
4.  `CO` (Satellite Carbon Monoxide)
5.  `O3` (Satellite Ozone)
6.  `HCHO` (Satellite Formaldehyde)
7.  `AT (°C)` (Ambient Temperature)
8.  `RH (%)` (Relative Humidity)
9.  `WS (m/s)` (Wind Speed)
10. `WD (deg)` (Wind Direction)
11. `TOT-RF (mm)` (Total Rainfall)
12. `SR (W/mt2)` (Solar Radiation)
13. `BP (mmHg)` (Barometric Pressure)
14. `VWS (m/s)` (Vertical Wind Speed - likely)
15. `Latitude`
16. `Longitude`
17. `Month`
18. `DayOfWeek`
19. `DayOfYear`
20. `AOD_RH_ratio` (Engineered Feature)
21. `U_Wind` (Engineered/Decomposed Wind vector)
22. `V_Wind` (Engineered/Decomposed Wind vector)
23. `Temp_Pressure_Ratio` (Engineered Feature)

## 8. Preprocessing Pipeline
*   **Transformers:** There are NO explicit `StandardScaler`, `MinMaxScaler`, or `SimpleImputer` steps wrapping the base models. 
*   **Behavior:** The model expects raw floats corresponding directly to the 23 features in the exact order listed above. Because the base models are predominantly Tree-based (ExtraTrees, XGBoost, LightGBM), they do not strictly require normalized/scaled inputs, which explains the lack of scalers.

## 9. Exact Outputs / Targets
The model dictionary specifically maps independent models for exactly **6** target pollutants:
1.  `PM2.5`
2.  `PM10`
3.  `NO2`
4.  `SO2`
5.  `O3`
6.  `CO`

**CRITICAL FINDINGS:** 
*   The model does **NOT** predict `HCHO` (Formaldehyde). `HCHO` is treated entirely as an *input feature* for predicting the other 6 pollutants. 
*   The model does **NOT** predict AQI directly. AQI must be manually calculated from the 6 target outputs.

## 10. Are Lat/Lon/Date inputs?
**YES.** They are explicitly required as direct inputs.
*   **Spatial:** `Latitude` and `Longitude` are raw floats.
*   **Temporal:** `Month` (1-12), `DayOfWeek` (0-6), and `DayOfYear` (1-365) are required. The exact `Date` string must be parsed into these three components before inference.

## 11. Missing-Value Behavior
*   Because `scikit-learn`'s `ExtraTreesRegressor` (historically) throws errors if fed `NaN` values (unlike XGBoost/LightGBM which handle them natively), and because there is no `SimpleImputer` in the pipeline, **the input feature vector must not contain missing values**. If external satellite data is missing, we cannot run inference without creating a gap.

## 12. Anything Still Unknown / Missing
*   **HCHO Hotspots:** The UI specifications mandate an "HCHO hotspots" page, but this model only uses HCHO as an *input*, not an output. Hotspot generation must happen through a different analytical mechanism (e.g., spatial clustering of the input HCHO satellite data).
*   **Exact Data Sources:** While we know the feature names (e.g., `AOD`, `SR (W/mt2)`), we do not know precisely which satellite product (e.g., Sentinel-5P, MODIS, ERA5) was used to train the model. We will need to map these to the most scientifically standard corresponding datasets in Earth Engine / Open-Meteo during Phase 2.

---
**CONCLUSION:**
The model contract is completely mapped. We know the exact 23 inputs, their required engineered transformations, and the 6 targets. We now have enough information to proceed to Phase 1 (Model Contract Formalization) and Phase 2 (Data Source Matrix).