import os
import sys
import datetime
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import json

# Adjust path to import api
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from api.services.feature_service import get_features
from api.services.model_service import predict_pollutants
from api.services.aqi_service import calculate_aqi_from_predictions
from api.services import MissingDataError

LAT_MIN, LAT_MAX = 8.0, 36.0
LON_MIN, LON_MAX = 68.0, 96.0
GRID_ROWS, GRID_COLS = 200, 200

# We will sample a coarser grid to make it run in a reasonable time for the migration demonstration.
# Instead of 200x200 (40000 points), we use a step of 100 -> 2x2 = 4 points.
STEP = 100

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

def generate_real_predictions():
    print("Generating real predictions parquet (coarse 10x10 grid for demonstration)...")
    end_date = datetime.date.today() - datetime.timedelta(days=1)
    # Just run for 1 day to ensure it finishes quickly
    dates = [end_date]
    
    lat_vals = np.linspace(LAT_MIN, LAT_MAX, GRID_ROWS)
    lon_vals = np.linspace(LON_MIN, LON_MAX, GRID_COLS)
    
    records = {
        "grid_row": [], "grid_col": [], "lat": [], "lon": [],
        "date": [], "coverage": [],
        "pm25": [], "pm10": [], "no2": [], "so2": [], "co": [], "o3": [],
        "pm25_ci_low": [], "pm25_ci_high": [],
        "pm10_ci_low": [], "pm10_ci_high": [],
        "no2_ci_low":  [], "no2_ci_high":  [],
        "so2_ci_low":  [], "so2_ci_high":  [],
        "co_ci_low":   [], "co_ci_high":   [],
        "o3_ci_low":   [], "o3_ci_high":   [],
        "hcho_column": [],
    }

    for d in dates:
        date_str = d.isoformat()
        print(f"Processing date: {date_str}")
        for r in range(0, GRID_ROWS, STEP):
            for c in range(0, GRID_COLS, STEP):
                lat = float(lat_vals[r])
                lon = float(lon_vals[c])
                
                records["grid_row"].append(r)
                records["grid_col"].append(c)
                records["lat"].append(lat)
                records["lon"].append(lon)
                records["date"].append(d)
                
                try:
                    features = get_features(lat, lon, date_str)
                    predictions = predict_pollutants(features)
                    
                    records["coverage"].append("full")
                    records["pm25"].append(predictions["PM2.5"])
                    records["pm10"].append(predictions["PM10"])
                    records["no2"].append(predictions["NO2"])
                    records["so2"].append(predictions["SO2"])
                    records["co"].append(predictions["CO"])
                    records["o3"].append(predictions["O3"])
                    
                    # CI - the real model doesn't output CI. Output null.
                    for pol in ["pm25", "pm10", "no2", "so2", "co", "o3"]:
                        records[f"{pol}_ci_low"].append(None)
                        records[f"{pol}_ci_high"].append(None)
                        
                    records["hcho_column"].append(features["HCHO"])
                    
                except MissingDataError as e:
                    print(f"Missing data at {lat}, {lon}: {e}")
                    records["coverage"].append("none")
                    for k in ["pm25","pm10","no2","so2","co","o3",
                               "pm25_ci_low","pm25_ci_high","pm10_ci_low","pm10_ci_high",
                               "no2_ci_low","no2_ci_high","so2_ci_low","so2_ci_high",
                               "co_ci_low","co_ci_high","o3_ci_low","o3_ci_high","hcho_column"]:
                        records[k].append(None)
                except Exception as e:
                    print(f"Error at {lat}, {lon}: {e}")
                    records["coverage"].append("none")
                    for k in ["pm25","pm10","no2","so2","co","o3",
                               "pm25_ci_low","pm25_ci_high","pm10_ci_low","pm10_ci_high",
                               "no2_ci_low","no2_ci_high","so2_ci_low","so2_ci_high",
                               "co_ci_low","co_ci_high","o3_ci_low","o3_ci_high","hcho_column"]:
                        records[k].append(None)

    table = pa.table({
        "grid_row": pa.array(records["grid_row"], type=pa.int32()),
        "grid_col": pa.array(records["grid_col"], type=pa.int32()),
        "lat":      pa.array(records["lat"],      type=pa.float64()),
        "lon":      pa.array(records["lon"],      type=pa.float64()),
        "date":     pa.array(records["date"],     type=pa.date32()),
        "coverage": pa.array(records["coverage"], type=pa.string()),
        **{k: pa.array(records[k], type=pa.float64())
           for k in ["pm25","pm10","no2","so2","co","o3",
                      "pm25_ci_low","pm25_ci_high","pm10_ci_low","pm10_ci_high",
                      "no2_ci_low","no2_ci_high","so2_ci_low","so2_ci_high",
                      "co_ci_low","co_ci_high","o3_ci_low","o3_ci_high","hcho_column"]},
    })
    out = os.path.join(OUTPUT_DIR, "predictions.parquet")
    pq.write_table(table, out, compression="snappy")
    print(f"Wrote {out}")

def generate_empty_hotspots():
    fc = {"type": "FeatureCollection", "features": []}
    out = os.path.join(OUTPUT_DIR, "hotspots.geojson")
    with open(out, 'w') as f:
        json.dump(fc, f)
    print(f"Wrote {out} (Empty, real generation not implemented)")

def generate_empty_validation():
    table = pa.table({
        "pollutant":  pa.array([], type=pa.string()),
        "observed":   pa.array([], type=pa.float64()),
        "predicted":  pa.array([], type=pa.float64()),
        "station_id": pa.array([], type=pa.string()),
        "date":       pa.array([], type=pa.date32()),
    })
    out = os.path.join(OUTPUT_DIR, "validation.parquet")
    pq.write_table(table, out, compression="snappy")
    print(f"Wrote {out} (Empty, real validation not implemented)")

def generate_real_stations():
    print("Generating real stations predictions...")
    STATIONS_METADATA = [
        ("Delhi Anand Vihar", 28.65, 77.31),
        ("Mumbai Bandra", 19.06, 72.84),
        ("Chennai Manali", 13.16, 80.26),
    ]
    
    end_date = datetime.date.today() - datetime.timedelta(days=1)
    dates = [end_date]
    station_ids = [f"ST{i+1:03d}" for i in range(len(STATIONS_METADATA))]

    rows = {
        "station_id": [], "name": [], "lat": [], "lon": [],
        "date": [], "observed_aqi": [], "predicted_aqi": [],
    }
    
    for d in dates:
        date_str = d.isoformat()
        for i, (name, slat, slon) in enumerate(STATIONS_METADATA):
            pred = None
            try:
                features = get_features(slat, slon, date_str)
                predictions = predict_pollutants(features)
                aqi_res = calculate_aqi_from_predictions(predictions)
                pred = aqi_res["overall_aqi"]
            except Exception as e:
                print(f"Error predicting for station {name}: {e}")
                
            rows["station_id"].append(station_ids[i])
            rows["name"].append(name)
            rows["lat"].append(float(slat))
            rows["lon"].append(float(slon))
            rows["date"].append(d)
            rows["observed_aqi"].append(None)
            
            # Using 0 as fallback if pred is None, since pa.int32 doesn't always handle Nones cleanly if the whole array is empty
            rows["predicted_aqi"].append(pred if pred is not None else -1)

    table = pa.table({
        "station_id":    pa.array(rows["station_id"],    type=pa.string()),
        "name":          pa.array(rows["name"],          type=pa.string()),
        "lat":           pa.array(rows["lat"],           type=pa.float64()),
        "lon":           pa.array(rows["lon"],           type=pa.float64()),
        "date":          pa.array(rows["date"],          type=pa.date32()),
        "observed_aqi":  pa.array(rows["observed_aqi"],  type=pa.int32()),
        "predicted_aqi": pa.array(rows["predicted_aqi"], type=pa.int32()),
    })
    out = os.path.join(OUTPUT_DIR, "stations.parquet")
    pq.write_table(table, out, compression="snappy")
    print(f"Wrote {out}")

if __name__ == "__main__":
    generate_real_predictions()
    generate_real_stations()
    generate_empty_validation()
    generate_empty_hotspots()
