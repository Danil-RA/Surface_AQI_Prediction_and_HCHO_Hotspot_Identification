import math
from datetime import datetime
from typing import Dict, Any

from api.services.gee_service import get_satellite_features
from api.services.era5_service import get_era5_features
from api.services.vws_service import get_vws_data

def get_features(latitude: float, longitude: float, date_str: str) -> Dict[str, Any]:
    """
    Generates the complete 23-feature vector for the model inference.
    Order must exactly match the model contract.
    """
    # 1. Base time features
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    month = dt.month
    day_of_week = dt.weekday()  # Monday=0, Sunday=6
    day_of_year = dt.timetuple().tm_yday
    
    # 2. External Features
    sat_feat = get_satellite_features(latitude, longitude, date_str)
    era_feat = get_era5_features(latitude, longitude, date_str)
    
    # 3. Engineered Features
    aod = sat_feat["AOD"]
    rh = era_feat["RH"]
    at = era_feat["AT"]
    bp = era_feat["BP"]
    ws = era_feat["WS"]
    wd = era_feat["WD"]
    
    aod_rh_ratio = aod / (rh + 1e-5)
    u_wind = -ws * math.sin(math.radians(wd))
    v_wind = -ws * math.cos(math.radians(wd))
    temp_pressure_ratio = (at + 273.15) / (bp + 1e-5)
    
    vws_data = get_vws_data(latitude, longitude, date_str)
    vws = vws_data["value"]
    
    # 5. Assemble exact 23-feature vector
    final_features = {
        "AOD": aod,
        "NO2": sat_feat["NO2"],
        "SO2": sat_feat["SO2"],
        "CO": sat_feat["CO"],
        "O3": sat_feat["O3"],
        "HCHO": sat_feat["HCHO"],
        "AT (°C)": at,
        "RH (%)": rh,
        "WS (m/s)": ws,
        "WD (deg)": wd,
        "TOT-RF (mm)": era_feat["TOT-RF"],
        "SR (W/mt2)": era_feat["SR"],
        "BP (mmHg)": bp,
        "VWS (m/s)": vws,
        "Latitude": latitude,
        "Longitude": longitude,
        "Month": month,
        "DayOfWeek": day_of_week,
        "DayOfYear": day_of_year,
        "AOD_RH_ratio": aod_rh_ratio,
        "U_Wind": u_wind,
        "V_Wind": v_wind,
        "Temp_Pressure_Ratio": temp_pressure_ratio
    }
    
    # Validation
    assert len(final_features) == 23, "Feature vector must have exactly 23 features"
    
    return final_features
