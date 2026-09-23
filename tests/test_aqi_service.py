import sys
import traceback
import math

from api.services.aqi_service import calculate_aqi_from_predictions
from api.aqi.breakpoints import compute_aqi

def test_aqi_service():
    print("--- TESTING AQI SERVICE (PHASE 3) ---")

    # 1. Test deterministic breakpoint/interpolation behavior
    print("\n[1] Testing Deterministic Breakpoint Behavior...")
    # PM2.5 of 40 should be between 30 (AQI 50) and 60 (AQI 100)
    # Ih=100, Il=51, BPh=60, BPl=31
    # SI = ((100-51)/(60-31))*(40-31) + 51 = (49/29)*9 + 51 = 15.2 + 51 = 66
    
    test_preds = {
        "PM2.5": 40.0,
        "PM10": 45.0, # (50-0)/(50-0)*45 + 0 = 45
        "NO2": 15.0,  # (50-0)/(40-0)*15 = 18.75 = 19
        "SO2": 10.0,  # (50-0)/(40-0)*10 = 12.5 = 12/13
        "CO": 0.5,    # (50-0)/(1-0)*0.5 = 25
        "O3": 30.0    # (50-0)/(50-0)*30 = 30
    }
    
    try:
        result = calculate_aqi_from_predictions(test_preds)
        print("  Service successfully processed 6 pollutants.")
        print(f"  Overall AQI: {result['overall_aqi']}")
        print(f"  Dominant Pollutant: {result['dominant_pollutant']}")
        print(f"  Category: {result['category']}")
        print(f"  Sub-indices: {result['sub_indices']}")
        
        # Verify dominant pollutant logic
        max_si = max(result['sub_indices'].values())
        if result['overall_aqi'] == max_si:
            print("  [OK] Overall AQI matches highest sub-index.")
        else:
            print("  [FAILED] Overall AQI does NOT match highest sub-index.")
            
        if result['sub_indices'][result['dominant_pollutant']] == max_si:
            print("  [OK] Dominant pollutant matches highest sub-index.")
        else:
            print("  [FAILED] Dominant pollutant incorrect.")
            
    except Exception as e:
        print(f"  [FAILED] {e}")

    # 2. Test Missing inputs
    print("\n[2] Testing Missing Input Rejection...")
    try:
        bad_preds = test_preds.copy()
        del bad_preds["PM2.5"]
        calculate_aqi_from_predictions(bad_preds)
        print("  [FAILED] Did not reject missing pollutant.")
    except ValueError as e:
        print(f"  [OK] Rejected missing successfully: {e}")

    # 3. Test NaN/Inf
    print("\n[3] Testing NaN / Infinity Rejection...")
    try:
        bad_preds = test_preds.copy()
        bad_preds["O3"] = float('inf')
        calculate_aqi_from_predictions(bad_preds)
        print("  [FAILED] Did not reject infinity.")
    except ValueError as e:
        print(f"  [OK] Rejected infinity successfully: {e}")

    try:
        bad_preds = test_preds.copy()
        bad_preds["NO2"] = float('nan')
        calculate_aqi_from_predictions(bad_preds)
        print("  [FAILED] Did not reject NaN.")
    except ValueError as e:
        print(f"  [OK] Rejected NaN successfully: {e}")

    # 4. Test Negative concentrations (should be dropped via existing logic)
    print("\n[4] Testing Negative Concentration Handling...")
    try:
        neg_preds = test_preds.copy()
        neg_preds["PM2.5"] = -10.0 # Negative PM2.5
        neg_preds["CO"] = 1.5      # Ensure at least one valid exists
        
        res_neg = calculate_aqi_from_predictions(neg_preds)
        if "PM2.5" not in res_neg["sub_indices"]:
            print("  [OK] Negative pollutant omitted from sub-indices per existing logic.")
        else:
            print("  [FAILED] Negative pollutant was calculated.")
    except Exception as e:
        print(f"  [FAILED] Unexpected error for negative concentration: {e}")

    # 5. Integration Test (Phase 2 Model output -> Phase 3 AQI)
    print("\n[5] INTERNAL SOFTWARE INTEGRATION TEST")
    print("  Testing Phase 2 Fixture -> Phase 3 AQI Service")
    # This is exactly the output from the INTERNAL MODEL-SERVICE TEST FIXTURE
    fixture_predictions = {
        "PM2.5": 29.8409,
        "PM10": 104.4420,
        "NO2": 14.4025,
        "SO2": 8.7408,
        "O3": 20.5751,
        "CO": 0.8618
    }
    
    try:
        integration_result = calculate_aqi_from_predictions(fixture_predictions)
        print("  [OK] Integration test processed fixture successfully.")
        print("  Integration Result Output:")
        print(f"    Overall AQI: {integration_result['overall_aqi']}")
        print(f"    Dominant Pollutant: {integration_result['dominant_pollutant']}")
        print(f"    Category: {integration_result['category']}")
        print(f"    Sub-indices: {integration_result['sub_indices']}")
    except Exception as e:
        print(f"  [FAILED] Integration test failed: {e}")

if __name__ == "__main__":
    test_aqi_service()
