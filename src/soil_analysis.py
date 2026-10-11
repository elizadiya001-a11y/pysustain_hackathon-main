"""
src/soil_analysis.py
--------------------
Chemical nutrient assessment, fertility grading, and soil amendment recommendations.
Aligns with Indian Council of Agricultural Research (ICAR) soil test benchmarks.
"""

from typing import Dict, Any, List


def evaluate_ph_status(ph: float) -> Dict[str, str]:
    if ph < 5.5:
        return {"category": "Strongly Acidic", "status": "Poor", "color": "#d90429", "action": "Apply agricultural lime (calcium carbonate) or dolomite to raise pH."}
    elif ph < 6.5:
        return {"category": "Slightly Acidic", "status": "Fair", "color": "#f77f00", "action": "Tolerable for most cereals; apply organic compost to buffer pH."}
    elif ph <= 7.5:
        return {"category": "Neutral / Optimal", "status": "Ideal", "color": "#2d6a4f", "action": "Optimal nutrient bioavailability. Maintain with balanced NPK."}
    elif ph <= 8.5:
        return {"category": "Moderately Alkaline", "status": "Fair", "color": "#f77f00", "action": "Watch for micronutrient lock-in (Zinc, Iron); apply elemental sulphur or gypsum."}
    else:
        return {"category": "Strongly Alkaline / Sodic", "status": "Poor", "color": "#d90429", "action": "Apply gypsum and leaching to counter sodium saturation."}


def evaluate_nitrogen_status(n_kg_ha: float) -> Dict[str, str]:
    if n_kg_ha < 70:
        return {"category": "Low", "status": "Deficient", "color": "#d90429", "action": "Incorporate green manuring (dhaincha) or legume pulse rotations."}
    elif n_kg_ha <= 130:
        return {"category": "Medium", "status": "Adequate", "color": "#2d6a4f", "action": "Standard basal application recommended."}
    else:
        return {"category": "High", "status": "Surplus", "color": "#2a9d8f", "action": "Reduce top-dressing urea to avoid leaching and groundwater nitrate pollution."}


def evaluate_phosphorus_status(p_kg_ha: float) -> Dict[str, str]:
    if p_kg_ha < 25:
        return {"category": "Low", "status": "Deficient", "color": "#d90429", "action": "Apply single super phosphate (SSP) or rock phosphate near root zone."}
    elif p_kg_ha <= 55:
        return {"category": "Medium", "status": "Adequate", "color": "#2d6a4f", "action": "Adequate for root establishment."}
    else:
        return {"category": "High", "status": "Surplus", "color": "#2a9d8f", "action": "Skip basal phosphorus for upcoming season."}


def evaluate_potassium_status(k_kg_ha: float) -> Dict[str, str]:
    if k_kg_ha < 100:
        return {"category": "Low", "status": "Deficient", "color": "#d90429", "action": "Apply Muriate of Potash (MOP) to enhance stalk strength and drought tolerance."}
    elif k_kg_ha <= 180:
        return {"category": "Medium", "status": "Adequate", "color": "#2d6a4f", "action": "Sufficient potassium for grain and boll development."}
    else:
        return {"category": "High", "status": "Surplus", "color": "#2a9d8f", "action": "Excellent reserve; withhold additional K fertilizers."}


def evaluate_organic_carbon_status(oc: float) -> Dict[str, str]:
    if oc < 0.40:
        return {"category": "Very Low", "status": "Degraded", "color": "#d90429", "action": "Critical humus depletion. Add FYM (farmyard manure) 5-10 t/ha and avoid stubble burning."}
    elif oc <= 0.65:
        return {"category": "Medium", "status": "Moderate", "color": "#f77f00", "action": "Retain crop residues in situ to build microbial biomass."}
    else:
        return {"category": "High", "status": "Rich", "color": "#2d6a4f", "action": "Healthy soil biological activity and moisture retention capacity."}


def comprehensive_soil_health_assessment(soil_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Performs full multi-parameter soil health assessment.
    """
    ph = float(soil_data.get("ph", 7.0))
    oc = float(soil_data.get("organic_carbon", 0.50))
    n = float(soil_data.get("nitrogen_kg_ha", 90.0))
    p = float(soil_data.get("phosphorus_kg_ha", 30.0))
    k = float(soil_data.get("potassium_kg_ha", 140.0))
    texture = soil_data.get("texture", "Loam")

    ph_eval = evaluate_ph_status(ph)
    oc_eval = evaluate_organic_carbon_status(oc)
    n_eval = evaluate_nitrogen_status(n)
    p_eval = evaluate_phosphorus_status(p)
    k_eval = evaluate_potassium_status(k)

    # Compute overall soil health index (0 to 100)
    score = 100.0
    if ph_eval["status"] == "Poor": score -= 25.0
    elif ph_eval["status"] == "Fair": score -= 10.0

    if oc_eval["status"] == "Degraded": score -= 25.0
    elif oc_eval["status"] == "Moderate": score -= 10.0

    if n_eval["status"] == "Deficient": score -= 15.0
    if p_eval["status"] == "Deficient": score -= 15.0
    if k_eval["status"] == "Deficient": score -= 10.0

    overall_score = max(20.0, score)

    action_plan = []
    if ph_eval["status"] != "Ideal": action_plan.append(ph_eval["action"])
    if oc_eval["status"] != "Rich": action_plan.append(oc_eval["action"])
    if n_eval["status"] == "Deficient": action_plan.append(n_eval["action"])
    if p_eval["status"] == "Deficient": action_plan.append(p_eval["action"])
    if k_eval["status"] == "Deficient": action_plan.append(k_eval["action"])

    return {
        "overall_health_score": round(overall_score, 1),
        "health_rating": "Optimal" if overall_score >= 80 else ("Moderate" if overall_score >= 60 else "Constrained"),
        "parameters": {
            "pH": {"value": ph, **ph_eval},
            "Organic Carbon (%)": {"value": oc, **oc_eval},
            "Available Nitrogen (kg/ha)": {"value": n, **n_eval},
            "Available Phosphorus (kg/ha)": {"value": p, **p_eval},
            "Available Potassium (kg/ha)": {"value": k, **k_eval},
            "Physical Texture": {"value": texture, "category": texture, "status": "Observed", "color": "#2d6a4f", "action": "Ensure appropriate tillage timing based on moisture."}
        },
        "recommended_amendments": action_plan
    }

