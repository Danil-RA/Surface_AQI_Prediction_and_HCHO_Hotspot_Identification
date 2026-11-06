import joblib

try:
    model = joblib.load('multi_pollutant_stacking_pipeline.pkl')
    print("top-level keys:", list(model.keys()) if isinstance(model, dict) else "Not a dict")
    
    if isinstance(model, dict):
        if 'models' in model:
            print("number of stored pollutant models:", len(model['models']))
            print("stored targets:", list(model['models'].keys()))
            
            first_pollutant = list(model['models'].keys())[0]
            m = model['models'][first_pollutant]
            print("model type for each pollutant:", type(m))
            
            # extract info from stacking regressor
            if hasattr(m, 'estimators'):
                print("base estimator names/types:", [(name, type(est)) for name, est in m.estimators])
            if hasattr(m, 'cv'):
                print("stacking cv:", m.cv)
            if hasattr(m, 'final_estimator_'):
                print("final estimator type:", type(m.final_estimator_))
            elif hasattr(m, 'final_estimator'):
                print("final estimator type (unfitted):", type(m.final_estimator))

        if 'feature_cols' in model:
            print("stored feature_cols:", model['feature_cols'])
            print("stored feature_cols count:", len(model['feature_cols']))
except Exception as e:
    print("Error loading PKL:", e)
