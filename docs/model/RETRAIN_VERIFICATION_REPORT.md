# Retraining Verification Report

## 1. Environment and Dataset
- Python: 3.10.0
- NumPy: 2.2.6
- pandas: 2.3.3
- scikit-learn: 1.7.2
- XGBoost: 3.2.0
- LightGBM: 4.7.0
- joblib: 1.6.0
- Dataset Path: final_master_dataset.csv
- Dataset Hash (SHA-256): 5e80312ffd867d2b611b412d8f5998aea338b04d2c193129003f26f38de5060f

## 2. Configuration
- Feature Order: ['AOD', 'NO2', 'SO2', 'CO', 'O3', 'HCHO', 'AT (°C)', 'RH (%)', 'WS (m/s)', 'WD (deg)', 'TOT-RF (mm)', 'SR (W/mt2)', 'BP (mmHg)', 'VWS (m/s)', 'Latitude', 'Longitude', 'Month', 'DayOfWeek', 'DayOfYear', 'AOD_RH_ratio', 'U_Wind', 'V_Wind', 'Temp_Pressure_Ratio']
- Targets: ['PM2.5', 'PM10', 'NO2', 'SO2', 'O3', 'CO']
- Training Configuration: Identical to original notebook (Base estimators: ET, RF, GB, XGB, LGB; Meta: HuberRegressor; CV=5; test_size=0.2; random_state=42)

## 3. Metrics Comparison
| Pollutant | Original R2 | New R2 | Original RMSE | New RMSE | New MAE |
|-----------|-------------|--------|---------------|----------|---------|
| PM2.5     | 0.8639      | 0.8623 | 19.84         | 19.96 | 11.20 |
| PM10      | 0.8550      | 0.8542 | 35.35         | 35.44 | 22.07 |
| NO2       | 0.8463      | 0.8450 | 9.20          | 9.24 | 4.87 |
| SO2       | 0.7186      | 0.7193 | 4.04          | 4.04 | 2.08 |
| O3        | 0.7752      | 0.7760 | 10.88         | 10.87 | 6.12 |
| CO        | 0.7017      | 0.7020 | 0.36          | 0.36 | 0.19 |

## 4. Conclusion
- Training completed successfully: YES
- All six models created: YES
- Predictions from newly trained models work: YES
- Metrics are reasonably consistent with the original notebook: YES
- The retrained artifact is safe to consider for the next replacement step: YES
