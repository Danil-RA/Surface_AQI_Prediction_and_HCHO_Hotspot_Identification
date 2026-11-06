import joblib
import sys
import pprint
import numpy as np

def deep_inspect_new_model(filename):
    print(f"--- DEEP INSPECT: {filename} ---")
    try:
        model_data = joblib.load(filename)
    except Exception as e:
        print(f"Error loading {filename}: {e}")
        return

    # 1. feats_dict
    print("\n=== 1. feats_dict ===")
    if 'feats_dict' in model_data:
        pprint.pprint(model_data['feats_dict'])
    else:
        print("Not found.")

    # 2. imputers
    print("\n=== 2. imputers ===")
    if 'imputers' in model_data:
        imputers = model_data['imputers']
        for feat, imp in imputers.items():
            print(f"Feature: {feat}")
            print(f"  Type: {type(imp).__name__}")
            if hasattr(imp, 'strategy'):
                print(f"  Strategy: {imp.strategy}")
            if hasattr(imp, 'statistics_'):
                print(f"  Statistics_: {imp.statistics_}")
            if hasattr(imp, 'fill_value'):
                print(f"  Fill_value: {imp.fill_value}")
    else:
        print("Not found.")

    # 3. log_flags
    print("\n=== 3. log_flags ===")
    if 'log_flags' in model_data:
        pprint.pprint(model_data['log_flags'])
    else:
        print("Not found.")

    # 4. Feature Columns
    print("\n=== 4. 33-Feature List (Exact Order) ===")
    if 'feature_cols' in model_data:
        features = list(model_data['feature_cols'])
        for i, f in enumerate(features):
            print(f"{i+1:2d}. {f}")
    else:
        print("Not found.")

    # 5 & 6 & 7 & 10. Check for constants, formulas, transformations
    print("\n=== 5/6/7/10. Model Metadata, Constants, and Preprocessing steps ===")
    # Look for anything else in the dict
    for k, v in model_data.items():
        if k not in ['models', 'imputers', 'feats_dict', 'log_flags', 'feature_cols', 'targets', 'pollutant_lag_cols']:
            print(f"Other key found: {k} (type: {type(v).__name__})")
            print(f"Value: {v}")
    
    print("\nPollutant lag cols:")
    if 'pollutant_lag_cols' in model_data:
         print(model_data['pollutant_lag_cols'])

    # 8. Inspect the estimators (models)
    print("\n=== 8/9. Estimators & Preprocessing ===")
    if 'models' in model_data:
        models = model_data['models']
        for target, model in models.items():
            print(f"\nTarget: {target}")
            print(f"  Model type: {type(model).__name__}")
            if hasattr(model, 'n_features_in_'):
                print(f"  Expected input dimension (n_features_in_): {model.n_features_in_}")
            if hasattr(model, 'feature_names_in_'):
                print(f"  Expected input features matches 33-list: {list(model.feature_names_in_) == list(model_data.get('feature_cols', []))}")
            if hasattr(model, 'steps'):
                print("  Pipeline steps:")
                for name, step in model.steps:
                    print(f"    - {name}: {type(step).__name__}")
                    # check if the step has custom logic
                    if hasattr(step, 'func'):
                        print(f"      Function: {step.func}")
            else:
                print("  Not a pipeline.")

if __name__ == '__main__':
    deep_inspect_new_model('new_multi_pollutant_stacking_pipeline.pkl')
