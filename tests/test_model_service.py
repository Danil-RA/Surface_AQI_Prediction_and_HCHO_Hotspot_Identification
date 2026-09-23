import sys
import traceback
import math
from datetime import datetime

from api.services.model_service import ModelService, predict_pollutants, ModelServiceError
from api.services.feature_service import get_features

def test_model_service():
    print("--- TESTING MODEL SERVICE ---")
    
    # 1. Test model singleton and loading
    print("\n[1] Testing Model Initialization & Lazy Loading...")
    try:
        service1 = ModelService()
        print("  Model loaded successfully.")
        
        service2 = ModelService()
        if id(service1) == id(service2):
            print("  Singleton verified: Service is reused.")
        else:
            print("  [FAILED] Singleton not reused!")
    except Exception as e:
        print(f"  [FAILED] Model initialization error: {e}")
        return

    # 2. Try obtaining real data, fallback to fixture
    print("\n[2] Assembling Feature Vector...")
    lat = 8.523
    lon = 76.941
    date_str = "2024-01-15"
    
    feature_dict = None
    is_fixture = False
    
    try:
        feature_dict = get_features(lat, lon, date_str)
        print("  Obtained REAL Phase 1 feature data.")
    except Exception as e:
        print(f"  Real data acquisition failed ({type(e).__name__}): {e}")
        print("  Using INTERNAL MODEL-SERVICE TEST FIXTURE.")
        is_fixture = True
        
        # INTERNAL MODEL-SERVICE TEST FIXTURE
        # This is strictly to test the model-service interface and should not be presented as real scientific data.
        feature_dict = {
            "AOD": 0.5,
            "NO2": 0.0001,
            "SO2": 0.0002,
            "CO": 0.03,
            "O3": 0.1,
            "HCHO": 0.00005,
            "AT (°C)": 28.5,
            "RH (%)": 75.0,
            "WS (m/s)": 3.2,
            "WD (deg)": 180.0,
            "TOT-RF (mm)": 0.0,
            "SR (W/mt2)": 200.0,
            "BP (mmHg)": 760.0,
            "VWS (m/s)": 1.5,
            "Latitude": lat,
            "Longitude": lon,
            "Month": 1,
            "DayOfWeek": 0,
            "DayOfYear": 15,
            "AOD_RH_ratio": 0.5 / 75.0,
            "U_Wind": -3.2 * math.sin(math.radians(180.0)),
            "V_Wind": -3.2 * math.cos(math.radians(180.0)),
            "Temp_Pressure_Ratio": (28.5 + 273.15) / 760.0
        }

    # 3. Test Contract Validation
    print("\n[3] Testing Feature Contract...")
    if len(feature_dict) == 23:
        print("  Feature vector length is exactly 23.")
    else:
        print(f"  [FAILED] Feature vector length is {len(feature_dict)}.")
        
    print("  Feature Keys Validation...")
    missing = [f for f in ModelService.EXPECTED_FEATURES if f not in feature_dict]
    if missing:
        print(f"  [FAILED] Missing features: {missing}")
    else:
        print("  Feature dict has all required keys.")

    # 4. Run Inference
    print("\n[4] Running Prediction...")
    try:
        predictions = predict_pollutants(feature_dict)
        print("  Prediction successful.")
        
        expected_targets = ModelService.EXPECTED_TARGETS
        pred_keys = list(predictions.keys())
        
        if pred_keys == expected_targets:
            print(f"  Targets match exactly: {expected_targets}")
        else:
            print(f"  [FAILED] Targets mismatch! Expected: {expected_targets}, Got: {pred_keys}")
            
        print("\n--- EXACT PREDICTION OUTPUT ---")
        if is_fixture:
            print("(Source: INTERNAL MODEL-SERVICE TEST FIXTURE)")
        else:
            print("(Source: REAL Phase 1 Data)")
            
        for k, v in predictions.items():
            print(f"  {k}: {v:.4f}")
            import math as pymath
            if not pymath.isfinite(v):
                print(f"  [FAILED] Non-finite prediction for {k}: {v}")
                
    except Exception as e:
        print(f"  [FAILED] Prediction error: {e}")
        traceback.print_exc()

    # 5. Test Error Handling (Missing Features, NaNs)
    print("\n[5] Testing Error Handling...")
    try:
        bad_dict = feature_dict.copy()
        del bad_dict["AOD"]
        predict_pollutants(bad_dict)
        print("  [FAILED] Did not reject missing features.")
    except ModelServiceError as e:
        print(f"  Missing features rejected correctly: {e}")

    try:
        bad_dict = feature_dict.copy()
        bad_dict["AOD"] = float('nan')
        predict_pollutants(bad_dict)
        print("  [FAILED] Did not reject NaN values.")
    except ModelServiceError as e:
        print(f"  NaN values rejected correctly: {e}")

if __name__ == "__main__":
    test_model_service()
