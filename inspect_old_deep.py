import joblib

def inspect_old_deep():
    model_data = joblib.load('multi_pollutant_stacking_pipeline.pkl')
    models = model_data['models']
    for t, m in models.items():
        print(f"\n--- Target: {t} ---")
        if hasattr(m, 'estimators_'):
            print("Ensemble Base Estimators:")
            for est in m.estimators_:
                print(f"  - {type(est).__name__}")
                if hasattr(est, 'steps'):
                    print("    Steps:")
                    for name, step in est.steps:
                         print(f"      * {name}: {type(step).__name__}")
        else:
            print(f"Model is not an ensemble with estimators_. Type: {type(m)}")

if __name__ == '__main__':
    inspect_old_deep()
