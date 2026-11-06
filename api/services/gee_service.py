import ee
from datetime import datetime, timedelta
from api.services import MissingDataError

def _init_gee():
    if not ee.data.is_initialized():
        ee.Initialize(project="mystic-sun-502006-p5")

def get_satellite_features(latitude: float, longitude: float, date_str: str) -> dict:
    _init_gee()
    
    point = ee.Geometry.Point([longitude, latitude])
    # Historical spatial method: ~1000m station area buffer
    buffer_geom = point.buffer(1000)
    target_date = datetime.strptime(date_str, "%Y-%m-%d")
    
    features = {}

    datasets = {
        "AOD": {
            "id": "MODIS/061/MCD19A2_GRANULES",
            "band": "Optical_Depth_055",
            "scale": 1000,
            "multiplier": 0.001
        },
        "NO2": {
            "id": "COPERNICUS/S5P/OFFL/L3_NO2",
            "band": "NO2_column_number_density",
            "scale": 1113.2,
            "multiplier": 1.0
        },
        "SO2": {
            "id": "COPERNICUS/S5P/OFFL/L3_SO2",
            "band": "SO2_column_number_density",
            "scale": 1113.2,
            "multiplier": 1.0
        },
        "CO": {
            "id": "COPERNICUS/S5P/OFFL/L3_CO",
            "band": "CO_column_number_density",
            "scale": 1113.2,
            "multiplier": 1.0
        },
        "O3": {
            "id": "COPERNICUS/S5P/OFFL/L3_O3",
            "band": "O3_column_number_density",
            "scale": 1113.2,
            "multiplier": 1.0
        },
        "HCHO": {
            "id": "COPERNICUS/S5P/OFFL/L3_HCHO",
            "band": "tropospheric_HCHO_column_number_density",
            "scale": 1113.2,
            "multiplier": 1.0
        }
    }

    for feat_name, config in datasets.items():
        raw_val = None
        best_offset = 0
        best_date_str = date_str
        
        # Phase 2: Temporal recovery up to 3 days backwards (T, T-1, T-2, T-3)
        max_days = 4
        
        for offset in range(max_days):
            current_date = target_date - timedelta(days=offset)
            start_date = current_date.strftime("%Y-%m-%d")
            end_date = (current_date + timedelta(days=1)).strftime("%Y-%m-%d")
            
            collection = (ee.ImageCollection(config["id"])
                          .select(config["band"])
                          .filterBounds(buffer_geom)
                          .filterDate(start_date, end_date))
            
            # Aggregate available pixels using the historical mean behavior
            image = collection.mean()
            
            result = image.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=buffer_geom,
                scale=config["scale"]
            ).getInfo()
            
            if result is not None and result.get(config["band"]) is not None:
                raw_val = result.get(config["band"])
                best_offset = offset
                best_date_str = start_date
                break
                
        if raw_val is None:
            features[feat_name] = None
        else:
            source = "observed" if best_offset == 0 else "temporal_recovery"
            features[feat_name] = {
                "value": raw_val * config["multiplier"],
                "source": source,
                "source_date": best_date_str
            }
        
    return features
