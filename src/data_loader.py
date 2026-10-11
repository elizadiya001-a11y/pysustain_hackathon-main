"""
src/data_loader.py
------------------
Data retrieval and aggregation engine for FASAL AI.
Joins farms, soil chemistry, satellite indices, and weather streams.
Includes robust offline fallback.
"""

import os
import logging
from typing import Dict, Tuple, Optional, Any
import numpy as np
import pandas as pd

from src.supabase_client import fetch_table
from core.db import _generate_fallback_dataset
from core.config import CROP_AGRONOMY

logger = logging.getLogger("FasalDataLoader")

# In-memory cache
_CACHED_UNIFIED_DF: Optional[pd.DataFrame] = None
_CACHED_MARKET_DF: Optional[pd.DataFrame] = None
_CACHED_SOURCE: str = "Uninitialized"


def load_all_raw_datasets() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, str]:
    """
    Retrieves all agricultural tables from Supabase or fallback.
    Returns (farms_df, soil_df, weather_df, market_df, sat_df, soil_types_df, data_source).
    """
    farms_df, s1 = fetch_table("farms", order_col="farm_id")
    soil_df, s2 = fetch_table("soil", order_col="farm_id")
    weather_df, s3 = fetch_table("weather", order_col="date")
    market_df, s4 = fetch_table("market_prices", order_col="crop_name")
    sat_df, s5 = fetch_table("satellite_data", order_col="farm_id")
    soil_types_df, s6 = fetch_table("soil_types", order_col="soil_type")

    if s1 and not farms_df.empty and s2 and not soil_df.empty:
        source_name = "Live Supabase Cloud (bwlopgkkaasgmkdkoayb)"
        logger.info(f"Loaded datasets from Supabase Cloud: {len(farms_df)} farms, {len(soil_df)} soil records.")
        return farms_df, soil_df, weather_df, market_df, sat_df, soil_types_df, source_name

    logger.warning("Supabase tables unavailable or empty. Loading high-fidelity local twin.")
    # Fallback dataset
    farms_df, soil_df = _generate_fallback_dataset()
    market_rows = [
        {
            "crop_name": c,
            "msp_per_quintal": data["msp"],
            "market_price_per_quintal": data["market_price"],
            "water_req_liters_per_acre": data["water_req_liters_acre"]
        }
        for c, data in CROP_AGRONOMY.items()
    ]
    market_df = pd.DataFrame(market_rows)
    weather_df = pd.DataFrame()
    sat_df = pd.DataFrame()
    soil_types_df = pd.DataFrame()
    source_name = "Local High-Fidelity Twin (Offline Safe)"
    return farms_df, soil_df, weather_df, market_df, sat_df, soil_types_df, source_name


def get_unified_agricultural_dataset(force_reload: bool = False) -> Tuple[pd.DataFrame, pd.DataFrame, str]:
    """
    Produces a unified dataset containing farm attributes, soil tests,
    satellite indices, and weather summaries.
    """
    global _CACHED_UNIFIED_DF, _CACHED_MARKET_DF, _CACHED_SOURCE
    if not force_reload and _CACHED_UNIFIED_DF is not None:
        return _CACHED_UNIFIED_DF.copy(), _CACHED_MARKET_DF.copy(), _CACHED_SOURCE

    farms_df, soil_df, weather_df, market_df, sat_df, soil_types_df, source = load_all_raw_datasets()

    # Base merge: farms + soil
    unified = pd.merge(farms_df, soil_df, on="farm_id", how="left", suffixes=("", "_soil"))

    # Aggregate weather per farm if available
    if not weather_df.empty and "farm_id" in weather_df.columns:
        w_agg = weather_df.groupby("farm_id").agg(
            mean_temp_max=("temp_max_c", "mean"),
            mean_temp_min=("temp_min_c", "mean"),
            total_rainfall_7d=("rainfall_mm", "sum"),
            mean_humidity=("humidity_pct", "mean")
        ).reset_index()
        unified = pd.merge(unified, w_agg, on="farm_id", how="left")
    else:
        unified["mean_temp_max"] = 30.5
        unified["mean_temp_min"] = 18.2
        unified["total_rainfall_7d"] = 15.0
        unified["mean_humidity"] = 62.0

    # Merge satellite data if available
    if not sat_df.empty and "farm_id" in sat_df.columns:
        sat_cols = [c for c in sat_df.columns if c in ["farm_id", "ndvi_real", "ndmi_real", "bsi_real", "sand_pct", "clay_pct", "silt_pct", "ph_soilgrids", "soc_g_per_kg", "texture_usda", "image_path", "image_url"]]
        unified = pd.merge(unified, sat_df[sat_cols], on="farm_id", how="left")

    unified["data_source"] = source

    _CACHED_UNIFIED_DF = unified
    _CACHED_MARKET_DF = market_df
    _CACHED_SOURCE = source

    return unified.copy(), market_df.copy(), source


def get_farm_record_by_id(farm_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetches full unified record for a specific farm_id.
    """
    df, _, _ = get_unified_agricultural_dataset()
    match = df[df["farm_id"] == farm_id]
    if not match.empty:
        return match.iloc[0].to_dict()
    return None


def get_market_prices_catalog() -> Dict[str, Dict[str, float]]:
    """
    Returns dictionary of crop prices and water requirements from market_prices table.
    """
    _, market_df, _ = get_unified_agricultural_dataset()
    prices = {}
    if not market_df.empty and "crop_name" in market_df.columns:
        for _, row in market_df.iterrows():
            prices[row["crop_name"]] = {
                "msp": float(row.get("msp_per_quintal", 0.0)),
                "market_price": float(row.get("market_price_per_quintal", 0.0)),
                "water_req_liters_acre": float(row.get("water_req_liters_per_acre", 1500000.0))
            }
    else:
        # Fallback to CROP_AGRONOMY
        for c, data in CROP_AGRONOMY.items():
            prices[c] = {
                "msp": data["msp"],
                "market_price": data["market_price"],
                "water_req_liters_acre": data["water_req_liters_acre"]
            }
    return prices

