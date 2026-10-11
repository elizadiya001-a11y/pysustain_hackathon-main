"""
src/crop_recommendation.py
--------------------------
Evaluates every crop in the database against agronomic constraints,
water availability, and economic profitability.
Uses Random Forest suitability model and physics-based economics.
"""

import os
import joblib
from pathlib import Path
from typing import Dict, List, Any, Optional

import numpy as np
import pandas as pd

from core.config import CROP_AGRONOMY, IRRIGATION_METHODS
from core.simulation import simulate_scenario, get_bau_baseline
from core.sustainability import calculate_sustainability_score
from src.data_loader import get_market_prices_catalog

MODELS_DIR = Path("models")
RF_MODEL_PATH = MODELS_DIR / "crop_suitability_rf.joblib"

_rf_pipeline = None


def get_rf_suitability_model():
    """Loads and caches the Random Forest crop suitability pipeline."""
    global _rf_pipeline
    if _rf_pipeline is not None:
        return _rf_pipeline
    if RF_MODEL_PATH.exists():
        try:
            _rf_pipeline = joblib.load(RF_MODEL_PATH)
            return _rf_pipeline
        except Exception:
            return None
    return None


def calculate_crop_suitability_score(crop_name: str, farm_state: dict) -> float:
    """
    Computes an agronomic suitability score (0-100%) for a crop on the given farm
    using the Random Forest model and soil/weather envelopes.
    """
    ph = float(farm_state.get("ph", 7.0))
    n = float(farm_state.get("nitrogen_kg_ha", 90.0))
    p = float(farm_state.get("phosphorus_kg_ha", 30.0))
    k = float(farm_state.get("potassium_kg_ha", 140.0))
    rain = float(farm_state.get("rainfall_mm", 600.0))
    temp = float(farm_state.get("mean_temp_max", 30.0))

    model = get_rf_suitability_model()
    if model is not None:
        try:
            X = pd.DataFrame([{
                "nitrogen": n,
                "phosphorus": p,
                "potassium": k,
                "ph": ph,
                "rainfall_mm": rain,
                "temp_c": temp
            }])
            probs = model.predict_proba(X)[0]
            classes = list(model.classes_)
            if crop_name in classes:
                prob = float(probs[classes.index(crop_name)])
                # Scale relative to max class probability for calibrated 0-100 score
                max_p = float(np.max(probs))
                return round(min(98.0, max(25.0, (prob / max(0.01, max_p)) * 95.0)), 1)
        except Exception:
            pass

    # Agronomic envelope fallback
    agro = CROP_AGRONOMY.get(crop_name, CROP_AGRONOMY["Wheat"])
    score = 80.0
    # pH penalty
    if ph < agro["pH"][0]: score -= (agro["pH"][0] - ph) * 15.0
    elif ph > agro["pH"][1]: score -= (ph - agro["pH"][1]) * 15.0

    return round(float(np.clip(score, 30.0, 95.0)), 1)


def generate_crop_recommendations(
    farm_state: dict,
    water_cap_mm: float = 600.0,
    preferred_irrigation: str = "Drip",
    weather_scenario: str = "Normal",
    use_msp: bool = True,
    season_filter: Optional[str] = None
) -> Dict[str, Any]:
    """
    Evaluates every available crop in the database, ranks them by net margin
    subject to water cap compliance, and returns top alternatives.
    """
    baseline_bau = get_bau_baseline(farm_state)
    current_crop = baseline_bau["crop"]
    market_catalog = get_market_prices_catalog()

    results = []

    for crop_name in market_catalog.keys():
        agro = CROP_AGRONOMY.get(crop_name)
        if not agro:
            continue

        # Optional seasonal filtering
        if season_filter and season_filter != "All Seasons":
            if season_filter not in agro["season"] and "Kharif / Rabi" not in agro["season"]:
                continue

        # Appropriate irrigation method
        method = preferred_irrigation
        if crop_name in ["Moong Dal", "Pearl Millet (Bajra)"] and preferred_irrigation == "Flood / Furrow":
            method = "Sprinkler"

        target_irrig_mm = (agro["irrig_mm"][0] + agro["irrig_mm"][1]) / 2.0
        eff = IRRIGATION_METHODS.get(method, IRRIGATION_METHODS["Drip"])["efficiency"]
        applied_mm = round(target_irrig_mm * (0.65 / eff), 1)

        applied_n = (agro["N"][0] + agro["N"][1]) / 2.0
        applied_p = (agro["P"][0] + agro["P"][1]) / 2.0
        applied_k = (agro["K"][0] + agro["K"][1]) / 2.0

        sim = simulate_scenario(
            farm_state=farm_state,
            crop=crop_name,
            irrigation_method=method,
            irrigation_mm=applied_mm,
            applied_n=applied_n,
            applied_p=applied_p,
            applied_k=applied_k,
            weather_scenario=weather_scenario,
            use_msp=use_msp
        )

        sust = calculate_sustainability_score(sim, farm_state)
        suitability_score = calculate_crop_suitability_score(crop_name, farm_state)

        is_within_cap = applied_mm <= water_cap_mm
        cap_delta_mm = applied_mm - water_cap_mm

        results.append({
            "crop": crop_name,
            "display_name": agro["display_name"],
            "season": agro["season"],
            "category": agro["category"],
            "is_msp_staple": agro["is_msp_staple"],
            "is_current": (crop_name == current_crop),
            "irrigation_method": method,
            "applied_mm": applied_mm,
            "is_within_cap": is_within_cap,
            "cap_delta_mm": round(cap_delta_mm, 1),
            "yield_q_acre": sim["yield_q_acre"],
            "yield_tonnes_ha": round(sim["yield_q_acre"] * 0.2471, 2),
            "gross_revenue": sim["gross_revenue"],
            "total_cost": sim["total_cost"],
            "net_profit": sim["net_profit"],
            "net_profit_acre": sim["net_profit_acre"],
            "profit_delta_rs": sim["profit_delta_rs"],
            "water_liters": sim["water_liters"],
            "water_saved_pct": sim["water_saved_pct"],
            "suitability_score": suitability_score,
            "sustainability_score": sust["composite_score"],
            "sustainability_rating": sust["rating"],
            "risk_level": sim["risk_level"]
        })

    # Sort crops: within water cap first, then by net profit per acre descending
    within_cap = [r for r in results if r["is_within_cap"]]
    exceeds_cap = [r for r in results if not r["is_within_cap"]]

    within_cap.sort(key=lambda x: x["net_profit_acre"], reverse=True)
    exceeds_cap.sort(key=lambda x: x["net_profit_acre"], reverse=True)

    ranked_all = within_cap + exceeds_cap

    # Filter alternatives
    alternatives = [r for r in within_cap if r["crop"] != current_crop]
    top_1 = alternatives[0] if len(alternatives) > 0 else (within_cap[0] if within_cap else ranked_all[0])
    top_2 = alternatives[1] if len(alternatives) > 1 else (within_cap[1] if len(within_cap) > 1 else (ranked_all[1] if len(ranked_all) > 1 else None))
    top_3 = alternatives[2] if len(alternatives) > 2 else (within_cap[2] if len(within_cap) > 2 else (ranked_all[2] if len(ranked_all) > 2 else None))

    current_crop_res = next((r for r in ranked_all if r["crop"] == current_crop), ranked_all[0])

    return {
        "water_cap_mm": water_cap_mm,
        "current_crop": current_crop_res,
        "top_recommendation_1": top_1,
        "top_recommendation_2": top_2,
        "top_recommendation_3": top_3,
        "ranked_crops": ranked_all,
        "bau_baseline": baseline_bau
    }

