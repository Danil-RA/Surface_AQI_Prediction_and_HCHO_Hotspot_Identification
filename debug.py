import traceback
from api.services.model_service import predict_pollutants

features = {
    'AOD': 0.1, 'NO2': 0.001, 'SO2': 0.001, 'CO': 0.02, 'O3': 0.04, 'HCHO': 0.0001, 
    'AT': 25.0, 'RH': 50.0, 'WS': 2.0, 'WD': 180.0, 'TOT-RF': 0.0, 'SR': 200.0, 'BP': 750.0, 
    'VWS': 0.1, 'Latitude': 22.0, 'Longitude': 82.0, 'Month': 9, 'DayOfWeek': 3, 'DayOfYear': 260, 
    'AOD_RH_ratio': 0.002, 'U_Wind': 1.0, 'V_Wind': 1.0, 'Temp_Pressure_Ratio': 0.033
}

try:
    res = predict_pollutants(features)
    print("SUCCESS:", res)
except Exception as e:
    traceback.print_exc()
