import joblib

try:
    model = joblib.load('multi_pollutant_stacking_pipeline.pkl')
    m = model['models'][list(model['models'].keys())[0]]
    for name, est in m.estimators:
        print(f"\nEstimator: {name}")
        params = est.get_params()
        for k in ['n_estimators', 'max_depth', 'learning_rate', 'random_state', 'n_jobs']:
            if k in params:
                print(f"  {k}: {params[k]}")
except Exception as e:
    print("Error:", e)
