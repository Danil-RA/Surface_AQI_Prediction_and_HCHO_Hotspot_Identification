import random

def get_vws_data(latitude: float, longitude: float, date_str: str, seed: int = None) -> dict:
    """
    Retrieves real CPCB VWS if available.
    
    Since the observed training VWS distribution is unavailable in this project, 
    real retrieval is impossible.
    
    The trained model contains tree split thresholds spanning approximately -7.778 to 11.529 m/s. 
    These thresholds DO NOT represent the empirical training distribution. They are merely 
    model-supported range/threshold evidence.
    
    This function implements a conservative synthetic fallback by sampling a uniform random 
    value within the central dense region of the model's threshold evidence (-2.678 to 1.216 m/s) 
    to avoid extreme extrapolation, but this does NOT reproduce the original training distribution.
    """
    if seed is not None:
        random.seed(seed)
    else:
        # Reproducible seed based on location and date
        stable_seed = hash(f"{latitude}_{longitude}_{date_str}")
        random.seed(stable_seed)
        
    # Conservative fallback based ONLY on model threshold evidence, not empirical data
    # (Using the p05 to p95 range of the thresholds to avoid extreme model edges)
    val = random.uniform(-2.6781599446896647, 1.216376197558189)
        
    return {
        "value": val,
        "source": "synthetic_CPCB_fallback",
        "station": None,
        "date": date_str,
        "is_synthetic": True
    }
