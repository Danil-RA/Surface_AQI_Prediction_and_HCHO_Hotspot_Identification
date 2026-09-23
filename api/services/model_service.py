import os
import joblib
import pandas as pd
import numpy as np
from typing import Dict, Any

MODEL_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "multi_pollutant_stacking_pipeline.pkl")

class ModelServiceError(Exception):
    pass

class ModelService:
    _instance = None
    _model_data = None
    
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
            cls._instance._load_model()
        return cls._instance

    def _load_model(self):
        if not os.path.exists(MODEL_PATH):
            raise ModelServiceError(f"Model file missing at {MODEL_PATH}")
            
        try:
            # We use joblib as it is typically used for large scikit-learn pipelines
            self._model_data = joblib.load(MODEL_PATH)
        except Exception as e:
            raise ModelServiceError(f"Invalid or corrupt model file: {str(e)}")
            
        if not isinstance(self._model_data, dict):
            raise ModelServiceError("Unexpected pickle structure: Model is not a dictionary")
            
        if "models" not in self._model_data or "feature_cols" not in self._model_data or "targets" not in self._model_data:
            raise ModelServiceError("Unexpected pickle structure: Missing required keys (models, feature_cols, targets)")
            
        # Validate feature contract
        if list(self._model_data["feature_cols"]) != self.EXPECTED_FEATURES:
            raise ModelServiceError("Feature contract mismatch: Model features do not match the expected 23 features in exact order")
            
        # Validate targets contract
        if list(self._model_data["targets"]) != self.EXPECTED_TARGETS:
            raise ModelServiceError("Target contract mismatch: Model targets do not match the expected 6 targets")

    def predict(self, feature_dict: Dict[str, Any]) -> Dict[str, float]:
        # Validate missing features
        missing_features = [feat for feat in self.EXPECTED_FEATURES if feat not in feature_dict]
        if missing_features:
            raise ModelServiceError(f"Missing input feature(s): {', '.join(missing_features)}")
            
        # Extract exactly in order and validate
        feature_values = []
        for feat in self.EXPECTED_FEATURES:
            val = feature_dict[feat]
            
            # Validate numeric and finite
            if val is None or not isinstance(val, (int, float)):
                raise ModelServiceError(f"Invalid numeric value for feature {feat}: {val}")
            if not np.isfinite(val):
                raise ModelServiceError(f"NaN or infinite value for feature {feat}: {val}")
                
            feature_values.append(val)
            
        # Construct DataFrame
        # A 1-row DataFrame must be created to pass to scikit-learn models properly, keeping the column names
        df = pd.DataFrame([feature_values], columns=self.EXPECTED_FEATURES)
        
        # Predict using each target model
        predictions = {}
        try:
            models = self._model_data["models"]
            
            for target in self.EXPECTED_TARGETS:
                if target not in models:
                    raise ModelServiceError(f"Model missing for target: {target}")
                
                model = models[target]
                pred = model.predict(df)[0]
                predictions[target] = float(pred)
                
        except Exception as e:
            raise ModelServiceError(f"Prediction failure: {str(e)}")
            
        return predictions

def predict_pollutants(feature_dict: Dict[str, Any]) -> Dict[str, float]:
    """
    Predict all 6 pollutants given the required 23-feature dictionary.
    """
    service = ModelService()
    return service.predict(feature_dict)
