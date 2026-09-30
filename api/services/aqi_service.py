import math
from typing import Dict, Any

from api.aqi.breakpoints import compute_aqi, get_category, POLLUTANTS

def calculate_aqi_from_predictions(predictions: Dict[str, float]) -> Dict[str, Any]:
    """
    Thin wrapper service that connects Phase 2 model predictions to the 
    existing Phase 1 CPCB AQI calculation logic.
    
    Accepts:
        predictions: Dictionary of the 6 pollutant predictions (PM2.5, PM10, NO2, SO2, O3, CO)
        
    Returns:
        Dict containing:
        - overall_aqi: int
        - dominant_pollutant: str
        - category: str (e.g. "Good", "Satisfactory")
        - category_color: str
        - sub_indices: Dict[str, int]
    """
    
    # 1. Validate inputs: Reject missing pollutants, NaNs, and infinite values
    clean_predictions = {}
    for pol in POLLUTANTS:
        if pol not in predictions:
            raise ValueError(f"Missing required pollutant prediction for AQI: {pol}")
            
        val = predictions[pol]
        if not isinstance(val, (int, float)):
            raise TypeError(f"Prediction for {pol} must be numeric, got {type(val)}")
            
        if not math.isfinite(val):
            raise ValueError(f"Prediction for {pol} must be a finite number, got {val}")
            
        clean_predictions[pol] = float(val)
        
    # 2. Compute AQI using the existing CPCB implementation
    try:
        # Negative concentrations or extremely high values will naturally yield None 
        # in the underlying compute_sub_index() and be omitted from the max() calculation.
        # This honors the existing implementation without inventing new rules.
        aqi, dominant_pollutant, sub_indices = compute_aqi(clean_predictions)
    except ValueError as e:
        # This catches cases like all sub-indices being None 
        # (e.g., all concentrations were negative)
        raise ValueError(f"Failed to compute AQI from predictions: {str(e)}")
        
    # 3. Retrieve AQI category
    cat = get_category(aqi)
    
    return {
        "overall_aqi": aqi,
        "dominant_pollutant": dominant_pollutant,
        "category": cat.name,
        "category_color": cat.color,
        "sub_indices": sub_indices
    }
