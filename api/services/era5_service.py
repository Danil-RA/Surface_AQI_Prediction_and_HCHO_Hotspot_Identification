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
        raise MissingDataError("ERA5 Variables", dataset_id, f"No ERA5 hourly images found for {date_str}.")

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
    
    # Check for missing values
    for b in mean_bands:
        if mean_res.get(b) is None:
            raise MissingDataError(b, dataset_id, "ERA5 variable is masked out at this location.")
            
    for b in sum_bands:
        if sum_res.get(b) is None:
            raise MissingDataError(b, dataset_id, "ERA5 variable is masked out at this location.")

    # Apply conversions
    
    # Temperatures: K to °C
    t_kelvin = mean_res["temperature_2m"]
    td_kelvin = mean_res["dewpoint_temperature_2m"]
    at_c = t_kelvin - 273.15
    td_c = td_kelvin - 273.15
    
    # Relative Humidity (%) via Magnus formula
    # E = 6.11 * 10.0 ** (7.5 * T / (237.3 + T))
    # RH = 100 * (E_dew / E_air)
    def magnus_e(t):
        return 6.11 * (10.0 ** (7.5 * t / (237.3 + t)))
    
    rh = 100.0 * (magnus_e(td_c) / magnus_e(at_c))
    
    # Wind
    u = mean_res["u_component_of_wind_10m"]
    v = mean_res["v_component_of_wind_10m"]
    ws = math.sqrt(u**2 + v**2)
    # Meteorological wind direction: angle from which the wind is blowing
    wd = (math.degrees(math.atan2(-u, -v)) + 360) % 360
    
    # Precipitation: meters to mm
    tot_rf = sum_res["total_precipitation"] * 1000.0
    
    # Solar Radiation: Accumulated J/m^2 over 24h to average W/m^2 (J/s per m^2)
    sr = sum_res["surface_solar_radiation_downwards"] / (24 * 3600)
    
    # Pressure: Pascals to mmHg
    bp = mean_res["surface_pressure"] / 133.322

    return {
        "AT": at_c,
        "RH": rh,
        "WS": ws,
        "WD": wd,
        "TOT-RF": tot_rf,
        "SR": sr,
        "BP": bp
    }
