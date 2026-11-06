# -*- coding: utf-8 -*-
import sys, joblib, json, pandas as pd
import warnings
warnings.filterwarnings('ignore')

model_path = sys.argv[1]
features_json = sys.argv[2]
features = json.loads(features_json)
EXPECTED_FEATURES = ['AOD', 'NO2', 'SO2', 'CO', 'O3', 'HCHO', 'AT (°C)', 'RH (%)', 'WS (m/s)', 'WD (deg)', 'TOT-RF (mm)', 'SR (W/mt2)', 'BP (mmHg)', 'VWS (m/s)', 'Latitude', 'Longitude', 'Month', 'DayOfWeek', 'DayOfYear', 'AOD_RH_ratio', 'U_Wind', 'V_Wind', 'Temp_Pressure_Ratio']
feature_values = [features[f] for f in EXPECTED_FEATURES]
df = pd.DataFrame([feature_values], columns=EXPECTED_FEATURES)

est = joblib.load(model_path)
pred = est.predict(df)
print("SUCCESS:", pred[0])
