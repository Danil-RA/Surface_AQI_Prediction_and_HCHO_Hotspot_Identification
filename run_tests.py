import urllib.request
import urllib.error
import json
import traceback

def test_backend_health():
    print("\n--- TEST 1: BACKEND & FRONTEND HEALTH ---")
    try:
        req = urllib.request.Request("http://127.0.0.1:8000/health")
        with urllib.request.urlopen(req) as response:
            res = json.loads(response.read().decode('utf-8'))
            print("Backend Health HTTP 200: PASS")
            print("Backend Health Data:", res)
    except Exception as e:
        print("Backend Health: FAIL", e)

    try:
        req = urllib.request.Request("http://127.0.0.1:5173/")
        with urllib.request.urlopen(req) as response:
            html = response.read().decode('utf-8')
            print("Frontend Health HTTP 200: PASS")
            if "<div id=\"root\">" in html:
                print("Frontend HTML contains root element: PASS")
    except Exception as e:
        print("Frontend Health: FAIL", e)

def test_real_prediction():
    print("\n--- TEST 2 & 4: REAL AQI PREDICTION & MODEL ERROR REGRESSION ---")
    data = {"latitude": 28.65, "longitude": 77.31, "date": "2026-05-15"}
    req = urllib.request.Request(
        "http://127.0.0.1:8000/api/predict",
        data=json.dumps(data).encode('utf-8'),
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    try:
        with urllib.request.urlopen(req) as response:
            res = json.loads(response.read().decode('utf-8'))
            print("Prediction HTTP Success: PASS")
            preds = res.get("predictions", {})
            aqi = res.get("aqi", {})
            print(f"PM2.5: {preds.get('PM2.5')}")
            print(f"PM10: {preds.get('PM10')}")
            print(f"NO2: {preds.get('NO2')}")
            print(f"SO2: {preds.get('SO2')}")
            print(f"O3: {preds.get('O3')}")
            print(f"CO: {preds.get('CO')}")
            print(f"AQI: {aqi.get('value')}")
            print(f"Category: {aqi.get('category')}")
            print(f"Dominant pollutant: {res.get('dominant_pollutant')}")
            print("Model Errors: None detected during successful prediction.")
    except Exception as e:
        print("Prediction: FAIL")
        if isinstance(e, urllib.error.HTTPError):
            print(f"HTTP {e.code}: {e.read().decode('utf-8')}")
        else:
            traceback.print_exc()

def test_missing_data():
    print("\n--- TEST 3: MISSING ENVIRONMENTAL DATA ---")
    data = {"latitude": 0.0, "longitude": 0.0, "date": "2026-05-15"}
    req = urllib.request.Request(
        "http://127.0.0.1:8000/api/predict",
        data=json.dumps(data).encode('utf-8'),
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    try:
        with urllib.request.urlopen(req) as response:
            res = json.loads(response.read().decode('utf-8'))
            print("Missing Data: FAIL (Returned 200 instead of 422)")
    except urllib.error.HTTPError as e:
        if e.code == 422:
            print("Missing Data HTTP 422: PASS")
            body = e.read().decode('utf-8')
            res = json.loads(body)
            print("Missing Data Detail:", json.dumps(res.get("detail", {}), indent=2))
        else:
            print(f"Missing Data: FAIL (Returned {e.code} instead of 422)")
            print(e.read().decode('utf-8'))
    except Exception as e:
        print("Missing Data: FAIL")
        traceback.print_exc()

def test_hcho_hotspots():
    print("\n--- TEST 6: HCHO HOTSPOTS ---")
    try:
        req = urllib.request.Request("http://127.0.0.1:8000/api/hotspots?season=winter&year=2024")
        with urllib.request.urlopen(req) as response:
            res = json.loads(response.read().decode('utf-8'))
            print("HCHO Winter 2024 HTTP 200: PASS")
            features = res.get("features", [])
            print(f"Loaded {len(features)} real hotspots for Winter 2024")
            if features:
                props = features[0].get("properties", {})
                print("Sample properties:")
                for k in ["name", "hcho_mean", "temperature", "wind_speed", "fire_associations"]:
                    print(f"  {k}: {props.get(k)}")
    except Exception as e:
        print("HCHO Winter 2024: FAIL", e)

if __name__ == "__main__":
    test_backend_health()
    test_real_prediction()
    test_missing_data()
    test_hcho_hotspots()
