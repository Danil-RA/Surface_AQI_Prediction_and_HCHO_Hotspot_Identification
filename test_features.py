import sys
import os

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

try:
    from api.services.feature_service import get_features
    features = get_features(28.65, 77.31, "2026-05-15")
    print("SUCCESS_FEATURES")
except Exception as e:
    import traceback
    print("FAILED_FEATURES")
    traceback.print_exc()
