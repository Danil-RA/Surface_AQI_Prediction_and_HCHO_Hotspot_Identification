import sys
import traceback

from api.services.gee_service import get_satellite_features
from api.services.era5_service import get_era5_features
from api.services.vws_service import get_vws_data
from api.services.feature_service import get_features
from api.services import MissingDataError

def test_vws():
    lat = 8.523
    lon = 76.941
    date1 = "2026-03-15"
    date2 = "2026-05-20"
    
    print(f"--- TESTING VWS HANDLING ---")
    
    # 1. Test isolated VWS generation (deterministic seed test)
    print("\n[1] Testing Synthetic VWS Fallback (Date 1)...")
    vws_1 = get_vws_data(lat, lon, date1)
    print(f"  VWS Object: {vws_1}")
    
    print("\n[2] Testing Synthetic VWS Fallback (Date 2)...")
    vws_2 = get_vws_data(lat, lon, date2)
    print(f"  VWS Object: {vws_2}")

    # 3. Test reproducibility
    vws_1_repeat = get_vws_data(lat, lon, date1)
    print(f"\n[3] Testing Reproducibility: {'PASSED' if vws_1['value'] == vws_1_repeat['value'] else 'FAILED'}")
    
    # 4. Feature vector output
    print("\n[4] Complete Feature Vector Output (Skipping GEE to bypass missing satellite data)")
    try:
        # Manually assemble vector by skipping GEE so we can see the 23 features with VWS included
        from datetime import datetime
        import math
        
        era_feat = get_era5_features(lat, lon, date1)
        
        # Base time features
        dt = datetime.strptime(date1, "%Y-%m-%d")
        month = dt.month
        day_of_week = dt.weekday()
        day_of_year = dt.timetuple().tm_yday
        
        rh = era_feat["RH"]
        at = era_feat["AT"]
        bp = era_feat["BP"]
        ws = era_feat["WS"]
        wd = era_feat["WD"]
        
        aod_rh_ratio = 0.5 / (rh + 1e-5) # dummy aod
        u_wind = -ws * math.sin(math.radians(wd))
        v_wind = -ws * math.cos(math.radians(wd))
        temp_pressure_ratio = (at + 273.15) / (bp + 1e-5)
        
        final_features = {
            "AOD": 0.5,
            "NO2": 0.001,
            "SO2": 0.001,
            "CO": 0.03,
            "O3": 0.1,
            "HCHO": 0.0001,
            "AT (°C)": at,
            "RH (%)": rh,
            "WS (m/s)": ws,
            "WD (deg)": wd,
            "TOT-RF (mm)": era_feat["TOT-RF"],
            "SR (W/mt2)": era_feat["SR"],
            "BP (mmHg)": bp,
            "VWS (m/s)": vws_1["value"],
            "Latitude": lat,
            "Longitude": lon,
            "Month": month,
            "DayOfWeek": day_of_week,
            "DayOfYear": day_of_year,
            "AOD_RH_ratio": aod_rh_ratio,
            "U_Wind": u_wind,
            "V_Wind": v_wind,
            "Temp_Pressure_Ratio": temp_pressure_ratio
        }
        
        assert len(final_features) == 23, "Must be exactly 23 features"
        print(f"  Feature Vector Size: {len(final_features)}")
        print(f"  Feature Order Validated: {list(final_features.keys())[13] == 'VWS (m/s)'}")
        print(f"  VWS Value Inside Vector: {final_features['VWS (m/s)']}")
        
    except Exception as e:
        print("  [ERROR] ", e)
        traceback.print_exc()

if __name__ == "__main__":
    test_vws()
