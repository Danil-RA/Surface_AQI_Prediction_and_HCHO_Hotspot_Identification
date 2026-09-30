import urllib.request
import urllib.error
import json

url = "http://127.0.0.1:8000/api/predict"
data = {
    "latitude": 0.0,
    "longitude": 0.0,
    "date": "2026-05-15"
}

req = urllib.request.Request(
    url, 
    data=json.dumps(data).encode('utf-8'),
    headers={'Content-Type': 'application/json'},
    method='POST'
)

try:
    with urllib.request.urlopen(req) as response:
        result = json.loads(response.read().decode('utf-8'))
        print("SUCCESS (Unexpected, should have failed due to missing data)")
        print(json.dumps(result, indent=2))
except urllib.error.HTTPError as e:
    print(f"HTTPError: {e.code}")
    print(e.read().decode('utf-8'))
except Exception as e:
    print(f"Error: {e}")
