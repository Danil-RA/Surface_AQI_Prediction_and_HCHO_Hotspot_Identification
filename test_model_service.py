import sys
from api.services.model_service import ModelService

def run():
    features = {
        "AOD": 0.5, "NO2": 0.5, "SO2": 0.5, "CO": 0.5, "O3": 0.5, "HCHO": 0.5, 
        "AT (°C)": 25.0, "RH (%)": 50.0, "WS (m/s)": 2.0, "WD (deg)": 180.0, 
        "TOT-RF (mm)": 0.0, "SR (W/mt2)": 100.0, "BP (mmHg)": 740.0, "VWS (m/s)": 2.0, 
        "Latitude": 28.65, "Longitude": 77.31, 
        "Month": 5, "DayOfWeek": 3, "DayOfYear": 135, "AOD_RH_ratio": 0.01, 
        "U_Wind": 1.0, "V_Wind": 1.0, "Temp_Pressure_Ratio": 0.03
    }
    
    svc = ModelService()
    try:
        preds = svc.predict(features)
        print("Success:", preds)
    except Exception as e:
        print("Exception caught:")
        print(type(e).__name__, str(e))

if __name__ == "__main__":
    run()
