import os
import sys
import json
import joblib
import pandas as pd
import numpy as np

MODEL_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "multi_pollutant_stacking_pipeline.pkl")

EXPECTED_FEATURES = [
    "AOD", "NO2", "SO2", "CO", "O3", "HCHO", "AT (°C)", "RH (%)", "WS (m/s)", "WD (deg)", 
    "TOT-RF (mm)", "SR (W/mt2)", "BP (mmHg)", "VWS (m/s)", "Latitude", "Longitude", 
    "Month", "DayOfWeek", "DayOfYear", "AOD_RH_ratio", "U_Wind", "V_Wind", "Temp_Pressure_Ratio"
]
EXPECTED_TARGETS = [
    "PM2.5", "PM10", "NO2", "SO2", "O3", "CO"
]

def run():
    try:
        input_data = sys.stdin.read()
        feature_dict = json.loads(input_data)
        
        # Load model
        model_data = joblib.load(MODEL_PATH)
        models = model_data["models"]
        
        feature_values = []
        for feat in EXPECTED_FEATURES:
            val = feature_dict[feat]
            feature_values.append(val)
            
        df = pd.DataFrame([feature_values], columns=EXPECTED_FEATURES)
        
        predictions = {}
        for target in EXPECTED_TARGETS:
            model = models[target]
            pred = model.predict(df)[0]
            predictions[target] = float(pred)
            
        output = {"status": "success", "predictions": predictions}
        print(json.dumps(output))
        sys.exit(0)
    except Exception as e:
        output = {"status": "error", "message": str(e)}
        print(json.dumps(output))
        sys.exit(1)

if __name__ == "__main__":
    run()
