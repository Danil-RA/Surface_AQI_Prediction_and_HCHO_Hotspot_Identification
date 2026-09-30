import pandas as pd
import json
import hashlib
import sys
import pickle
import os

print("--- A) DATASET ---")
df = pd.read_csv('final_master_dataset.csv')
print("exact row count:", len(df))
print("exact column count:", len(df.columns))
if 'Date' in df.columns:
    print("date range:", df['Date'].min(), "to", df['Date'].max())
if 'Station' in df.columns:
    print("number of stations:", df['Station'].nunique())
print("all column names:", df.columns.tolist())

targets = ['PM2.5 (µg/m³)', 'PM10 (µg/m³)', 'NO2 (µg/m³)', 'SO2 (µg/m³)', 'Ozone (µg/m³)', 'CO (mg/m³)']
for t in targets:
    if t in df.columns:
        avail = df[t].notna().sum()
        missing = df[t].isna().sum()
        print(f"Target {t}: availability={avail}, missing={missing}")
    else:
        print(f"Target {t}: NOT FOUND")

predictors = ['AOD', 'NO2', 'SO2', 'CO', 'O3', 'HCHO', 'AT (°C)', 'RH (%)', 'WS (m/s)', 'WD (deg)', 'TOT-RF (mm)', 'SR (W/mt2)', 'BP (mmHg)', 'VWS (m/s)']
for p in predictors:
    if p in df.columns:
        avail = df[p].notna().sum()
        missing = df[p].isna().sum()
        print(f"Predictor {p}: availability={avail}, missing={missing}")
    else:
        print(f"Predictor {p}: NOT FOUND")

print("\n--- B) NOTEBOOK EXTRACTION ---")
with open('AQI_non_linear.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

code_cells = [c['source'] for c in nb['cells'] if c['cell_type'] == 'code']
with open('notebook_code.txt', 'w', encoding='utf-8') as f:
    for i, cell in enumerate(code_cells):
        f.write(f"\n# CELL {i}\n")
        f.write("".join(cell))

print("Wrote notebook_code.txt")

print("\n--- F) DATASET IDENTITY ---")
sha256 = hashlib.sha256()
with open('final_master_dataset.csv', 'rb') as f:
    sha256.update(f.read())
print("SHA-256:", sha256.hexdigest())
print("file size:", os.path.getsize('final_master_dataset.csv'), "bytes")

print("\n--- C) EXISTING PKL ---")
# Try to load without scikit-learn first if possible, or just load it.
try:
    import joblib
    model = joblib.load('multi_pollutant_stacking_pipeline.pkl')
    print("top-level keys:", list(model.keys()) if isinstance(model, dict) else "Not a dict")
    
    if isinstance(model, dict):
        if 'models' in model:
            print("number of stored pollutant models:", len(model['models']))
            print("stored targets:", list(model['models'].keys()))
            
            first_pollutant = list(model['models'].keys())[0]
            m = model['models'][first_pollutant]
            print("model type for each pollutant:", type(m))
            
            # extract info from stacking regressor
            if hasattr(m, 'estimators'):
                print("base estimator names/types:", [(name, type(est)) for name, est in m.estimators])
            if hasattr(m, 'estimators_'):
                print("base estimators_ (fitted):", [(name, type(est)) for name, est in m.estimators_])
            if hasattr(m, 'cv'):
                print("stacking cv:", m.cv)
            if hasattr(m, 'final_estimator_'):
                print("final estimator type:", type(m.final_estimator_))
            elif hasattr(m, 'final_estimator'):
                print("final estimator type (unfitted):", type(m.final_estimator))

        if 'features' in model:
            print("stored feature_cols:", model['features'])
            print("stored feature_cols count:", len(model['features']))
except Exception as e:
    print("Error loading PKL:", e)
