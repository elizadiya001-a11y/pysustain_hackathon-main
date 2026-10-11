"""
src/crop_comparison.py
----------------------
Side-by-side comparison between the farmer's current crop and recommended alternatives.
Ensures valid unit parity (Quintals/Acre and Tonnes/Ha) and economic fairness.
Never equates raw physical crop weight with economic value.
"""

from typing import Dict, Any, Optional
from core.config import CROP_AGRONOMY


def build_crop_comparison(current_crop_res: Dict[str, Any], alt_crop_res: Dict[str, Any]) -> Dict[str, Any]:
    """
    Computes rigorous side-by-side comparison metrics between current crop and alternative.
    """
    curr_crop = current_crop_res.get("crop", "Wheat")
    alt_crop = alt_crop_res.get("crop", "Maize")

    # Yields
    curr_yield = float(current_crop_res.get("yield_q_acre", 0.0))
    alt_yield = float(alt_crop_res.get("yield_q_acre", 0.0))
    abs_yield_diff = round(alt_yield - curr_yield, 2)

    # Percentage yield difference
    # Note: Only calculate if current yield > 0
    if curr_yield > 0:
        pct_yield_diff = round(((alt_yield - curr_yield) / curr_yield) * 100.0, 1)
    else:
        pct_yield_diff = None

    # Economics
    curr_revenue = float(current_crop_res.get("gross_revenue", 0.0))
    alt_revenue = float(alt_crop_res.get("gross_revenue", 0.0))
    revenue_diff = round(alt_revenue - curr_revenue, 1)

    curr_cost = float(current_crop_res.get("total_cost", 0.0))
    alt_cost = float(alt_crop_res.get("total_cost", 0.0))
    cost_diff = round(alt_cost - curr_cost, 1)

    curr_profit = float(current_crop_res.get("net_profit", 0.0))
    alt_profit = float(alt_crop_res.get("net_profit", 0.0))
    profit_diff = round(alt_profit - curr_profit, 1)

    curr_profit_acre = float(current_crop_res.get("net_profit_acre", 0.0))
    alt_profit_acre = float(alt_crop_res.get("net_profit_acre", 0.0))
    if curr_profit_acre == 0.0 and curr_profit != 0.0:
        area = float(current_crop_res.get("area_acres", 2.0))
        curr_profit_acre = round(curr_profit / max(0.1, area), 1)
    if alt_profit_acre == 0.0 and alt_profit != 0.0:
        area = float(alt_crop_res.get("area_acres", 2.0))
        alt_profit_acre = round(alt_profit / max(0.1, area), 1)
    profit_acre_diff = round(alt_profit_acre - curr_profit_acre, 1)

    # Water
    curr_water = float(current_crop_res.get("water_liters", 1.0))
    alt_water = float(alt_crop_res.get("water_liters", 1.0))
    water_diff_liters = round(alt_water - curr_water, 0)
    water_saved_pct = round(((curr_water - alt_water) / max(1.0, curr_water)) * 100.0, 1)

    # Reasons & Drivers
    reasons = []
    if profit_diff > 0:
        reasons.append(f"Higher Net Profit Margin (+₹{profit_diff:,.0f} overall, +₹{profit_acre_diff:,.0f}/acre)")
    if water_saved_pct > 15:
        reasons.append(f"Conserves {water_saved_pct:.0f}% groundwater compared to {curr_crop}")
    if alt_crop_res.get("is_msp_staple") is False and alt_crop_res.get("category") == "Pulse / Legume":
        reasons.append("Fixes atmospheric nitrogen into the soil, lowering upcoming fertilizer expenses.")
    elif alt_crop_res.get("category") == "Cash Crop":
        reasons.append("Higher market realization per unit of land.")

    # Limitations
    limitations = [
        "Yields assume standard agronomic canopy management without severe pest infestation.",
        "Revenue projections use official MSP or benchmark wholesale market price.",
        "Raw physical harvest weights differ across crop types (e.g., sugarcane tonnage cannot be directly equated to pulse grain weight)."
    ]

    return {
        "current_crop": curr_crop,
        "recommended_crop": alt_crop,
        "yield": {
            "current_q_acre": curr_yield,
            "recommended_q_acre": alt_yield,
            "unit": "Quintals / Acre (1 q = 100 kg)",
            "abs_difference": abs_yield_diff,
            "pct_difference": pct_yield_diff,
            "current_tonnes_ha": round(curr_yield * 0.2471, 2),
            "recommended_tonnes_ha": round(alt_yield * 0.2471, 2)
        },
        "economics": {
            "current_gross_revenue": curr_revenue,
            "recommended_gross_revenue": alt_revenue,
            "revenue_difference": revenue_diff,
            "current_cultivation_cost": curr_cost,
            "recommended_cultivation_cost": alt_cost,
            "cost_difference": cost_diff,
            "current_net_profit": curr_profit,
            "recommended_net_profit": alt_profit,
            "profit_difference": profit_diff,
            "current_net_profit_acre": curr_profit_acre,
            "recommended_net_profit_acre": alt_profit_acre,
            "profit_acre_difference": profit_acre_diff
        },
        "water": {
            "current_water_liters": curr_water,
            "recommended_water_liters": alt_water,
            "water_diff_liters": water_diff_liters,
            "water_saved_pct": water_saved_pct,
            "cap_compliant": alt_crop_res.get("is_within_cap", True)
        },
        "key_reasons": reasons,
        "limitations": limitations
    }

