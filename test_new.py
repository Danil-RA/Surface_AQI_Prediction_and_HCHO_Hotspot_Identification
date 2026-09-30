import sys, json, joblib, pandas as pd
model_data = joblib.load('new_multi_pollutant_stacking_pipeline.pkl')
models = model_data['models']
feature_dict = json.loads(sys.stdin.read())
EXPECTED_FEATURES = [
    'AOD', 'NO2', 'SO2', 'CO', 'O3', 'HCHO', 'AT (°C)', 'RH (%)', 'WS (m/s)', 'WD (deg)', 
    'TOT-RF (mm)', 'SR (W/mt2)', 'BP (mmHg)', 'VWS (m/s)', 'Latitude', 'Longitude', 
    'Month', 'DayOfWeek', 'DayOfYear', 'AOD_RH_ratio', 'U_Wind', 'V_Wind', 'Temp_Pressure_Ratio'
]
feature_values = [feature_dict[f] for f in EXPECTED_FEATURES]
df = pd.DataFrame([feature_values], columns=EXPECTED_FEATURES)
predictions = {}
for target in ['PM2.5', 'PM10', 'NO2', 'SO2', 'O3', 'CO']:
    predictions[target] = float(models[target].predict(df)[0])
print(json.dumps({'status': 'success', 'predictions': predictions}))
