# -*- coding: utf-8 -*-
import sys, json, pandas as pd
import lightgbm as lgb

model_str_path = sys.argv[1]
features_json = sys.argv[2]
features = json.loads(features_json)
EXPECTED_FEATURES = ['AOD', 'NO2', 'SO2', 'CO', 'O3', 'HCHO', 'AT (°C)', 'RH (%)', 'WS (m/s)', 'WD (deg)', 'TOT-RF (mm)', 'SR (W/mt2)', 'BP (mmHg)', 'VWS (m/s)', 'Latitude', 'Longitude', 'Month', 'DayOfWeek', 'DayOfYear', 'AOD_RH_ratio', 'U_Wind', 'V_Wind', 'Temp_Pressure_Ratio']
feature_values = [features[f] for f in EXPECTED_FEATURES]
df = pd.DataFrame([feature_values], columns=EXPECTED_FEATURES)

with open(model_str_path, 'r', encoding='utf-8') as f:
    model_str = f.read()

try:
    booster = lgb.Booster(model_str=model_str)
    
    # Try prediction
    pred1 = booster.predict(df.values)[0]
    pred2 = booster.predict(df.values)[0]
    print(f"SUCCESS: {pred1:.4f} {pred2:.4f} {booster.num_trees()} {booster.num_feature()}")
except Exception as e:
    print(str(e))
    sys.exit(1)
