"""
src/data_cleaning.py
--------------------
Data validation, cleaning, unit conversion, and quality profiling for FASAL AI.
Provides transparent missingness flags and safe imputations.
"""

import logging
from typing import Dict, Any, Tuple, Optional
import numpy as np
import pandas as pd

logger = logging.getLogger("FasalDataCleaning")

# Conversion factors to standard Acre
UNIT_CONVERSION_TO_ACRES = {
    "Acres": 1.0,
    "Acre": 1.0,
    "Hectares": 2.47105,
    "Hectare": 2.47105,
    "Bigha (Standard)": 0.625,  # 1 Bigha ~ 0.625 acre (common North India)
    "Guntha": 0.025,           # 40 Gunthas = 1 Acre
    "Square Meters": 0.000247105
}

# Regional median defaults for Indian agro-climatic zones
REGIONAL_DEFAULTS = {
    "Punjab": {"ph": 7.4, "n": 115.0, "p": 28.0, "k": 150.0, "oc": 0.55, "rainfall": 550.0},
    "Haryana": {"ph": 7.6, "n": 105.0, "p": 25.0, "k": 140.0, "oc": 0.50, "rainfall": 520.0},
    "Maharashtra": {"ph": 7.2, "n": 90.0, "p": 22.0, "k": 180.0, "oc": 0.60, "rainfall": 850.0},
    "Karnataka": {"ph": 6.8, "n": 85.0, "p": 30.0, "k": 120.0, "oc": 0.65, "rainfall": 920.0},
    "West Bengal": {"ph": 6.2, "n": 95.0, "p": 35.0, "k": 110.0, "oc": 0.70, "rainfall": 1400.0},
    "Andhra Pradesh": {"ph": 7.5, "n": 110.0, "p": 32.0, "k": 160.0, "oc": 0.52, "rainfall": 890.0},
    "Rajasthan": {"ph": 7.9, "n": 65.0, "p": 18.0, "k": 130.0, "oc": 0.35, "rainfall": 420.0},
    "Uttar Pradesh": {"ph": 7.3, "n": 100.0, "p": 26.0, "k": 145.0, "oc": 0.58, "rainfall": 800.0},
    "Default": {"ph": 7.0, "n": 90.0, "p": 25.0, "k": 140.0, "oc": 0.50, "rainfall": 750.0}
}


def convert_area_to_acres(value: float, unit: str) -> float:
    """Converts landholding to standard acres."""
    factor = UNIT_CONVERSION_TO_ACRES.get(unit, 1.0)
    return max(0.1, round(float(value) * factor, 2))


def clean_and_validate_survey_inputs(survey: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validates farmer survey inputs, performs unit normalization,
    and returns a clean dictionary along with explicit 'data_quality_flags'.
    """
    cleaned = survey.copy()
    flags = {}

    # 1. Area normalization
    raw_area = float(survey.get("area", 2.0) or 2.0)
    unit = survey.get("area_unit", "Acres")
    cleaned["area_acres"] = convert_area_to_acres(raw_area, unit)

    state = survey.get("state", "Punjab")
    defaults = REGIONAL_DEFAULTS.get(state, REGIONAL_DEFAULTS["Default"])

    # 2. Soil pH
    raw_ph = survey.get("soil_ph")
    if raw_ph is not None and str(raw_ph).strip() != "" and float(raw_ph) > 0:
        val = float(raw_ph)
        if 3.5 <= val <= 10.5:
            cleaned["ph"] = round(val, 2)
            flags["ph_source"] = "Farmer Reported (Soil Card)"
        else:
            cleaned["ph"] = defaults["ph"]
            flags["ph_source"] = "Estimated (Out-of-range reported)"
    else:
        cleaned["ph"] = defaults["ph"]
        flags["ph_source"] = "Estimated from Agro-climatic District Median"

    # 3. Nitrogen (N)
    raw_n = survey.get("nitrogen")
    if raw_n is not None and str(raw_n).strip() != "" and float(raw_n) > 0:
        cleaned["nitrogen_kg_ha"] = round(float(raw_n), 1)
        flags["n_source"] = "Farmer Reported"
    else:
        cleaned["nitrogen_kg_ha"] = defaults["n"]
        flags["n_source"] = "Estimated from Regional Baseline"

    # 4. Phosphorus (P)
    raw_p = survey.get("phosphorus")
    if raw_p is not None and str(raw_p).strip() != "" and float(raw_p) > 0:
        cleaned["phosphorus_kg_ha"] = round(float(raw_p), 1)
        flags["p_source"] = "Farmer Reported"
    else:
        cleaned["phosphorus_kg_ha"] = defaults["p"]
        flags["p_source"] = "Estimated from Regional Baseline"

    # 5. Potassium (K)
    raw_k = survey.get("potassium")
    if raw_k is not None and str(raw_k).strip() != "" and float(raw_k) > 0:
        cleaned["potassium_kg_ha"] = round(float(raw_k), 1)
        flags["k_source"] = "Farmer Reported"
    else:
        cleaned["potassium_kg_ha"] = defaults["k"]
        flags["k_source"] = "Estimated from Regional Baseline"

    # 6. Rainfall
    raw_rain = survey.get("annual_rainfall_mm")
    if raw_rain is not None and str(raw_rain).strip() != "" and float(raw_rain) > 0:
        cleaned["rainfall_mm"] = round(float(raw_rain), 1)
        flags["rainfall_source"] = "Farmer Reported"
    else:
        cleaned["rainfall_mm"] = defaults["rainfall"]
        flags["rainfall_source"] = "Estimated from IMD Regional Normal"

    # 7. Soil Texture / Type
    raw_soil_type = survey.get("soil_type")
    if raw_soil_type and raw_soil_type != "Unknown / Need Assessment":
        cleaned["texture"] = raw_soil_type
        flags["soil_type_source"] = "Farmer Reported"
    else:
        cleaned["texture"] = "Loam"  # neutral generic texture
        flags["soil_type_source"] = "Pending Field Image or Hand Ribbon Test"

    cleaned["data_quality_flags"] = flags
    return cleaned


def generate_dataset_health_report(unified_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Computes data quality statistics, missing value percentages,
    and schema profiling without exposing private farmer identities.
    """
    if unified_df.empty:
        return {"total_records": 0, "columns": []}

    total_records = len(unified_df)
    col_profiles = []

    # Safe columns to audit (exclude personal names in public view)
    audited_cols = [c for c in unified_df.columns if c not in ["farmer_name"]]

    for col in audited_cols:
        missing_count = int(unified_df[col].isna().sum())
        missing_pct = round((missing_count / total_records) * 100.0, 1)
        dtype = str(unified_df[col].dtype)
        
        info = {
            "column": col,
            "dtype": dtype,
            "missing_count": missing_count,
            "missing_pct": missing_pct,
            "completeness_pct": round(100.0 - missing_pct, 1)
        }

        if pd.api.types.is_numeric_dtype(unified_df[col]):
            non_null = unified_df[col].dropna()
            if not non_null.empty:
                info["min"] = round(float(non_null.min()), 2)
                info["mean"] = round(float(non_null.mean()), 2)
                info["max"] = round(float(non_null.max()), 2)
        else:
            unique_count = int(unified_df[col].nunique())
            info["unique_categories"] = unique_count

        col_profiles.append(info)

    return {
        "total_records": total_records,
        "audited_columns": len(col_profiles),
        "columns": col_profiles
    }

