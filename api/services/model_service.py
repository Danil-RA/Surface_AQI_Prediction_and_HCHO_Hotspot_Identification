import os
import json
import subprocess
from typing import Dict, Any

WORKER_SCRIPT = os.path.join(os.path.dirname(__file__), "model_worker.py")
# The path to the isolated Python interpreter
PYTHON_EXE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "retrain_env", "Scripts", "python.exe")

class ModelServiceError(Exception):
    pass

class ModelService:
    _instance = None
    
    EXPECTED_FEATURES = [
        "AOD", "NO2", "SO2", "CO", "O3", "HCHO", "AT (°C)", "RH (%)", "WS (m/s)", "WD (deg)", 
        "TOT-RF (mm)", "SR (W/mt2)", "BP (mmHg)", "VWS (m/s)", "Latitude", "Longitude", 
        "Month", "DayOfWeek", "DayOfYear", "AOD_RH_ratio", "U_Wind", "V_Wind", "Temp_Pressure_Ratio"
    ]
    
    EXPECTED_TARGETS = [
        "PM2.5", "PM10", "NO2", "SO2", "O3", "CO"
    ]

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ModelService, cls).__new__(cls)
            cls._instance._verify_environment()
        return cls._instance

    def _verify_environment(self):
        if not os.path.exists(PYTHON_EXE):
            raise ModelServiceError(f"Isolated Python interpreter missing at {PYTHON_EXE}")
        if not os.path.exists(WORKER_SCRIPT):
            raise ModelServiceError(f"Worker script missing at {WORKER_SCRIPT}")

    def predict(self, feature_dict: Dict[str, Any]) -> Dict[str, float]:
        # Validate missing features
        missing_features = [feat for feat in self.EXPECTED_FEATURES if feat not in feature_dict]
        if missing_features:
            raise ModelServiceError(f"Missing input feature(s): {', '.join(missing_features)}")
            
        # Extract exactly in order and validate
        for feat in self.EXPECTED_FEATURES:
            val = feature_dict[feat]
            # Validate numeric
            if val is None or not isinstance(val, (int, float)):
                raise ModelServiceError(f"Invalid numeric value for feature {feat}: {val}")
                
        # Call isolated worker
        input_data = json.dumps(feature_dict)
        try:
            result = subprocess.run(
                [PYTHON_EXE, WORKER_SCRIPT],
                input=input_data,
                text=True,
                capture_output=True,
                check=False,
                timeout=30
            )
        except subprocess.TimeoutExpired:
            raise ModelServiceError("Model prediction timed out.")
        except Exception as e:
            raise ModelServiceError(f"Failed to execute model worker: {str(e)}")

        if result.returncode != 0:
            raise ModelServiceError(f"Model worker failed: {result.stderr.strip()} (STDOUT: {result.stdout.strip()})")

        try:
            output_data = json.loads(result.stdout)
        except json.JSONDecodeError:
            raise ModelServiceError(f"Invalid JSON response from model worker: {result.stdout.strip()}")

        if output_data.get("status") != "success":
            error_msg = output_data.get("message", "Unknown error in model worker")
            raise ModelServiceError(f"Prediction failure: {error_msg}")

        predictions = output_data.get("predictions")
        if not predictions or not isinstance(predictions, dict):
            raise ModelServiceError("Model worker did not return predictions dictionary")
            
        for target in self.EXPECTED_TARGETS:
            if target not in predictions:
                raise ModelServiceError(f"Model worker missed target: {target}")
                
        return predictions

def predict_pollutants(feature_dict: Dict[str, Any]) -> Dict[str, float]:
    """
    Predict all 6 pollutants given the required 23-feature dictionary.
    """
    service = ModelService()
    return service.predict(feature_dict)

