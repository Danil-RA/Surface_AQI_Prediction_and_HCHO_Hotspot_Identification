import ee
import math
from datetime import datetime, timedelta
from api.services import MissingDataError

def _init_gee():
    if not ee.data.is_initialized():
        ee.Initialize(project="mystic-sun-502006-p5")

def get_era5_features(latitude: float, longitude: float, date_str: str) -> dict:
    _init_gee()
    
    point = ee.Geometry.Point([longitude, latitude])
    target_date = datetime.strptime(date_str, "%Y-%m-%d")
    
    start_date = target_date.strftime("%Y-%m-%d")
    end_date = (target_date + timedelta(days=1)).strftime("%Y-%m-%d")

    # Use the ECMWF/ERA5/HOURLY dataset for surface variables
    dataset_id = "ECMWF/ERA5/HOURLY"
    collection = ee.ImageCollection(dataset_id).filterBounds(point).filterDate(start_date, end_date)
    
    if collection.size().getInfo() == 0:
        return {
            "AT": None, "RH": None, "WS": None, "WD": None,
            "TOT-RF": None, "SR": None, "BP": None
        }

    # Mean aggregation for temperatures, wind components, pressure
    mean_bands = [
        "temperature_2m", 
        "dewpoint_temperature_2m", 
        "u_component_of_wind_10m", 
        "v_component_of_wind_10m", 
        "surface_pressure"
    ]
    mean_image = collection.select(mean_bands).mean()
    
    # Sum aggregation for precipitation and radiation (accumulated variables)
    sum_bands = [
        "total_precipitation",
        "surface_solar_radiation_downwards"
    ]
    sum_image = collection.select(sum_bands).sum()
    
    # Extract
    scale = 27830  # ERA5 ~0.25 deg
    mean_res = mean_image.reduceRegion(reducer=ee.Reducer.first(), geometry=point, scale=scale).getInfo()
    sum_res = sum_image.reduceRegion(reducer=ee.Reducer.first(), geometry=point, scale=scale).getInfo()

    # Apply conversions
    
    # Temperatures & RH
    t_kelvin = mean_res.get("temperature_2m")
    td_kelvin = mean_res.get("dewpoint_temperature_2m")
    if t_kelvin is not None and td_kelvin is not None:
        at_c = t_kelvin - 273.15
        td_c = td_kelvin - 273.15
        def magnus_e(t):
            return 6.11 * (10.0 ** (7.5 * t / (237.3 + t)))
        rh = 100.0 * (magnus_e(td_c) / magnus_e(at_c))
    else:
        at_c = None
        rh = None

    # Wind
    u = mean_res.get("u_component_of_wind_10m")
    v = mean_res.get("v_component_of_wind_10m")
    if u is not None and v is not None:
        ws = math.sqrt(u**2 + v**2)
        wd = (math.degrees(math.atan2(-u, -v)) + 360) % 360
    else:
        ws = None
        wd = None
    
    # Precipitation: meters to mm
    raw_precip = sum_res.get("total_precipitation")
    tot_rf = raw_precip * 1000.0 if raw_precip is not None else None
    
    # Solar Radiation
    raw_sr = sum_res.get("surface_solar_radiation_downwards")
    sr = raw_sr / (24 * 3600) if raw_sr is not None else None
    
    # Pressure
    raw_bp = mean_res.get("surface_pressure")
    bp = raw_bp / 133.322 if raw_bp is not None else None

    return {
        "AT": at_c,
        "RH": rh,
        "WS": ws,
        "WD": wd,
        "TOT-RF": tot_rf,
        "SR": sr,
        "BP": bp
    }
