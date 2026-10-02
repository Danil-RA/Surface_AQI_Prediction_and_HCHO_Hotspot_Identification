import joblib
import os
import pandas as pd
from typing import Dict, Any, Tuple
from api.services.spatial_neighbor_service import spatial_neighbor_service

# Distance Operational Threshold from Phase 3 empirical distribution (90th percentile ~500km)
MAX_SPATIAL_DISTANCE_KM = 500.0

# High-pollution operational thresholds based on Phase 3 training distribution (90th percentile)
HIGH_POLLUTION_THRESHOLDS = {
    'AOD': 1.165,
    'NO2': 0.000137
}

# Supported targets for each model type
SPATIAL_SUPPORTED_VARS = ["O3", "CO", "NO2", "AOD"]
METEO_SUPPORTED_VARS = ["HCHO"] # HCHO stays on Phase 2 model

def predict_missing_satellite(target: str, features: Dict[str, Any], date_str: str) -> Tuple[float, dict]:
    """
    Returns (predicted_value, provenance_info) or (None, None)
    """
    lat = features.get('Latitude')
    lon = features.get('Longitude')
    
    if target in METEO_SUPPORTED_VARS:
        # Fallback to pure meteorology model (Phase 2 Model A)
        model_path = os.path.join(os.path.dirname(__file__), 'gapfill_models', f'lgb_{target}.pkl')
        if not os.path.exists(model_path): return None, None
        model = joblib.load(model_path)
        feature_list = [
            features.get('AT'), features.get('RH'), features.get('WS'), features.get('WD'),
            features.get('TOT-RF'), features.get('SR'), features.get('BP'), features.get('VWS'),
            lat, lon, features.get('Month'), features.get('DayOfYear')
        ]
        for t in ['AOD', 'NO2', 'SO2', 'CO', 'O3', 'HCHO']:
            if t != target:
                val = features.get('Satellite', {}).get(t)
                feature_list.append(val if val is not None else float('nan'))
        df = pd.DataFrame([feature_list])
        pred = float(model.predict(df)[0])
        return pred, {
            "source": "ml_gapfilled",
            "model": "Model_A_Meteo",
            "method": "HistGradientBoostingRegressor"
        }
        
    if target in SPATIAL_SUPPORTED_VARS:
        # Phase 3 Spatial gap-filling (Model C)
        neighbors = spatial_neighbor_service.get_neighbors(lat, lon, date_str, target, k=3)
        if len(neighbors) < 3:
            return None, None
            
        # Distance Guardrail
        max_dist = max([n['distance_km'] for n in neighbors])
        if max_dist > MAX_SPATIAL_DISTANCE_KM:
            # Nearest required neighbor exceeds operational limit
            return None, None
            
        # High-Pollution Guardrail
        if target in HIGH_POLLUTION_THRESHOLDS:
            mean_neighbor_val = sum([n['value'] for n in neighbors]) / 3.0
            if mean_neighbor_val > HIGH_POLLUTION_THRESHOLDS[target]:
                # Validation showed unacceptable AQI stability at extreme tails. Reject spatial gapfill.
                return None, None
                
        # Range Sanity Check
        # Instead of strict hardcoding, the gradient booster handles ranges inherently, but we can do a sanity check post-prediction.
        
        model_path = os.path.join(os.path.dirname(__file__), 'gapfill_models', f'spatial_lgb_{target}.pkl')
        if not os.path.exists(model_path): return None, None
        model = joblib.load(model_path)
        
        feature_list = [
            features.get('AT'), features.get('RH'), features.get('WS'), features.get('WD'),
            features.get('TOT-RF'), features.get('SR'), features.get('BP'), features.get('VWS'),
            lat, lon, features.get('Month'), features.get('DayOfYear')
        ]
        
        for t in ['AOD', 'NO2', 'SO2', 'CO', 'O3', 'HCHO']:
            if t != target:
                val = features.get('Satellite', {}).get(t)
                feature_list.append(val if val is not None else float('nan'))
                
        # Add spatial features (Model C order)
        for i in range(3):
            feature_list.append(neighbors[i]['value'])
            feature_list.append(neighbors[i]['distance_km'])
            
        df = pd.DataFrame([feature_list])
        pred = float(model.predict(df)[0])
        
        # Range Sanity Check: if prediction is negative for concentrations, it's invalid.
        if pred < 0:
            # Spatiotemporal prediction < 0 is mathematically impossible for these concentrations.
            # Reject spatial reconstruction and let the fallback hierarchy continue.
            return None, None
            
        return pred, {
            "source": "spatiotemporal_gapfill",
            "model": "Model_C",
            "neighbor_count": 3,
            "neighbor_distances_km": [n['distance_km'] for n in neighbors],
            "source_dates": [n['source_date'] for n in neighbors]
        }
        
    return None, None

