import urllib.request
import time

def check_backend():
    try:
        req = urllib.request.Request("http://127.0.0.1:8000/health")
        with urllib.request.urlopen(req, timeout=2) as response:
            return response.getcode() == 200
    except Exception:
        return False

def check_frontend():
    try:
        req = urllib.request.Request("http://localhost:5173/")
        with urllib.request.urlopen(req, timeout=2) as response:
            return response.getcode() == 200
    except Exception:
        return False

print("Waiting for backend and frontend...")
backend_ready = False
frontend_ready = False

for _ in range(30):
    if not backend_ready:
        backend_ready = check_backend()
    if not frontend_ready:
        frontend_ready = check_frontend()
    
    if backend_ready and frontend_ready:
        print("Both services are ready!")
        exit(0)
    
    time.sleep(1)

print(f"Timeout. Backend: {backend_ready}, Frontend: {frontend_ready}")
exit(1)
