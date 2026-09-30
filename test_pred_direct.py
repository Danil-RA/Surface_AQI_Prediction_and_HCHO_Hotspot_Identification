import joblib
import sys
import pandas as pd
import numpy as np

def verify():
    path = "multi_pollutant_stacking_pipeline.pkl"
    print(f"Loading {path}...")
    pipeline = joblib.load(path)
    models = pipeline["models"]
    
    EXPECTED_FEATURES = [
        "AOD", "NO2", "SO2", "CO", "O3", "HCHO", "AT (°C)", "RH (%)", "WS (m/s)", "WD (deg)", 
        "TOT-RF (mm)", "SR (W/mt2)", "BP (mmHg)", "VWS (m/s)", "Latitude", "Longitude", 
        "Month", "DayOfWeek", "DayOfYear", "AOD_RH_ratio", "U_Wind", "V_Wind", "Temp_Pressure_Ratio"
    ]
    EXPECTED_TARGETS = [
        "PM2.5", "PM10", "NO2", "SO2", "O3", "CO"
    ]
    
    # Dummy data
    feature_values = [0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 25.0, 50.0, 2.0, 180.0, 0.0, 100.0, 740.0, 2.0, 28.65, 77.31, 5, 3, 135, 0.01, 1.0, 1.0, 0.03]
    df = pd.DataFrame([feature_values], columns=EXPECTED_FEATURES)
    
    for target in EXPECTED_TARGETS:
        print(f"Predicting for {target}...")
        model = models[target]
        pred = model.predict(df)[0]
        print(f"{target}: {pred}")
        
if __name__ == "__main__":
    verify()
