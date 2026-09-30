# SCIENTIFIC & DATA RECONSTRUCTION RISKS

This document highlights critical uncertainties that make proceeding to real-world inference scientifically risky based on the current lack of training metadata.

## 1. The `VWS (m/s)` Feature is Unknown (BLOCKING)
*   **The Risk:** The model requires a feature called `VWS (m/s)`. In standard meteorology, vertical wind speed is measured in Pascals/second (Omega) or it might refer to Vertical Wind Shear. If we pass in standard vertical wind velocity, but the model was trained on wind shear between pressure levels, the entire prediction will be mathematically corrupted. 
*   **Resolution Needed:** We must determine what VWS represents. We cannot arbitrarily guess.

## 2. Unknown Engineered Wind Conventions (BLOCKING)
*   **The Risk:** The model uses `U_Wind` and `V_Wind`. In meteorology, Wind Direction (`WD`) can be defined as the direction the wind is blowing *from* (standard) or *to* (oceanographic). The formulas `U = -WS * sin(WD)` vs `U = WS * sin(WD)` flip the sign of the input. If we choose the wrong convention, we invert the wind direction entering the model.
*   **Resolution Needed:** Verify the mathematical convention used during feature engineering.

## 3. Unknown Temporal Aggregation (HIGH RISK)
*   **The Risk:** Satellite overpasses happen at specific times (e.g., Sentinel-5P at ~13:30 local time). Does the model expect the *instantaneous* temperature at 13:30 (`AT (°C)`), or the 24-hour daily mean? If the model was trained on 13:30 temperatures but we feed it daily means, the temperature inputs will be artificially low every day.
*   **Resolution Needed:** Clarify the temporal semantics (instantaneous overpass vs. daily mean).

## 4. Unverified Satellite Base Units (HIGH RISK)
*   **The Risk:** Sentinel-5P provides gases in `mol/m²`. Did the original authors convert these to `molecules/cm²` or `Dobson Units` before training? Tree-based models are extremely sensitive to unit scaling (they split on specific float thresholds). Feeding `0.0001` when the model expects `1.0e15` will cause all trees to route identically.
*   **Resolution Needed:** We need access to a single original training row to confirm feature scales, or we must inspect the internal tree thresholds directly to infer expected magnitudes.

## 5. Potential `AOD_RH_ratio` Divide-By-Zero (LOW RISK)
*   **The Risk:** Relative Humidity (`RH`) can theoretically be near zero, though practically rare in India. How did the training script handle `AOD / 0`?
*   **Resolution Needed:** Implement a standard epsilon addition (`RH + 1e-6`) or clamp to a max value.
