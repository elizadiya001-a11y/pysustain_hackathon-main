"""
src/yield_prediction.py
-----------------------
Multi-factor yield prediction with calibrated 80% prediction intervals
and explainable agronomic drivers for FASAL AI.
"""

from typing import Dict, Any
from core.models import get_yield_predictor
from core.config import CROP_AGRONOMY

Q_PER_ACRE_TO_TONNES_PER_HA = 0.2471  # 1 quintal = 100 kg = 0.1 tonne. 1 ha = 2.471 acres. 0.1 * 2.471 ~ 0.2471


def predict_crop_yield(
    crop: str,
    irrigation_method: str = "Flood / Furrow",
    irrigation_mm: float = 400.0,
    soil_ph: float = 7.0,
    soil_n: float = 80.0,
    applied_n: float = 100.0,
    temp_max: float = 30.0,
    rainfall_mm: float = 100.0,
    weather_scenario: str = "Normal"
) -> Dict[str, Any]:
    """
    Predicts yield in Quintals/Acre and Tonnes/Hectare with 80% prediction interval
    and feature attributions.
    """
    predictor = get_yield_predictor()
    sample = {
        "crop": crop,
        "irrigation_method": irrigation_method,
        "irrigation_mm": irrigation_mm,
        "soil_ph": soil_ph,
        "soil_n": soil_n,
        "applied_n": applied_n,
        "temp_max": temp_max,
        "rainfall_mm": rainfall_mm,
        "weather_scenario": weather_scenario
    }

    res = predictor.predict(sample)

    mean_q_acre = res["yield_mean"]
    lower_80_q_acre = res["yield_lower_80"]
    upper_80_q_acre = res["yield_upper_80"]

    # Tonnes per hectare conversions
    mean_t_ha = round(mean_q_acre * Q_PER_ACRE_TO_TONNES_PER_HA, 2)
    lower_80_t_ha = round(lower_80_q_acre * Q_PER_ACRE_TO_TONNES_PER_HA, 2)
    upper_80_t_ha = round(upper_80_q_acre * Q_PER_ACRE_TO_TONNES_PER_HA, 2)

    return {
        "crop": crop,
        "yield_q_acre": mean_q_acre,
        "yield_lower_80_q_acre": lower_80_q_acre,
        "yield_upper_80_q_acre": upper_80_q_acre,
        "yield_tonnes_ha": mean_t_ha,
        "yield_lower_80_t_ha": lower_80_t_ha,
        "yield_upper_80_t_ha": upper_80_t_ha,
        "uncertainty_range_q_acre": round(upper_80_q_acre - lower_80_q_acre, 2),
        "drivers": res.get("drivers", []),
        "disclaimer": (
            "Yield estimate is calibrated to regional agronomic potential with an 80% prediction interval. "
            "Actual harvest varies with extreme weather anomalies, pest outbreaks, and timely field operations."
        )
    }

