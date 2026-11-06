import joblib
import sys
import os

def verify():
    if len(sys.argv) > 1:
        path = sys.argv[1]
    else:
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        candidate = os.path.join(project_root, "multi_pollutant_stacking_pipeline_RETRAINED_TEST.pkl")
        path = candidate if os.path.exists(candidate) else "multi_pollutant_stacking_pipeline_RETRAINED_TEST.pkl"
    print(f"Loading {path}...")
    try:
        pipeline = joblib.load(path)
        print("Loaded successfully.")
        
        models = pipeline.get("models")
        if not models:
            print("ERROR: No 'models' key found.")
            sys.exit(1)
            
        print(f"Found {len(models)} models.")
        for pollutant, model in models.items():
            print(f" - {pollutant}: {type(model)}")
            
        feature_cols = pipeline.get("feature_cols")
        if not feature_cols:
            print("ERROR: No 'feature_cols' key found.")
            sys.exit(1)
        print(f"Found {len(feature_cols)} feature cols: {feature_cols}")
        
        targets = pipeline.get("targets")
        if not targets:
            print("ERROR: No 'targets' key found.")
            sys.exit(1)
        print(f"Found {len(targets)} targets: {targets}")
        
    except Exception as e:
        print(f"Error loading model: {e}")
        sys.exit(1)

if __name__ == "__main__":
    verify()
