import requests
import json
import time
import sys

def test_api():
    base_url = "http://localhost:8000"
    
    # Wait for API to be ready
    for i in range(10):
        try:
            resp = requests.get(f"{base_url}/health")
            if resp.status_code == 200:
                print("Backend health check: PASS")
                break
        except Exception:
            pass
        time.sleep(2)
    else:
        print("Backend health check: FAIL")
        sys.exit(1)
        
    # Test predict endpoint
    print("\nTesting /api/predict workflow...")
    payload = {
        "latitude": 8.523, 
        "longitude": 76.941, 
        "date": "2023-01-01"
    }
    
    try:
        resp = requests.post(f"{base_url}/api/predict", json=payload)
        
        print(f"Status Code: {resp.status_code}")
        
        if resp.status_code == 200:
            print("Prediction API: PASS")
            data = resp.json()
            print("Response:", json.dumps(data, indent=2))
        else:
            print("Prediction API: FAIL")
            print("Error details:", resp.text)
            
    except Exception as e:
        print(f"Prediction API Exception: {e}")

if __name__ == "__main__":
    test_api()
