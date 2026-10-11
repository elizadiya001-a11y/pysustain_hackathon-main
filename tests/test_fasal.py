"""
tests/test_fasal.py
-------------------
Comprehensive test suite for FASAL AI:
1. Supabase client & connectivity
2. Data loading & pagination
3. Survey input cleaning & missingness handling
4. Soil visual classifier inference
5. Crop suitability Random Forest inference
6. Yield prediction intervals & physics
7. Crop comparison metrics & unit parity
8. Executive advisory report & CSV generation
"""

import unittest
import numpy as np
import pandas as pd
from PIL import Image

from src.supabase_client import check_connection_health, fetch_table
from src.data_loader import get_unified_agricultural_dataset, get_farm_record_by_id
from src.data_cleaning import clean_and_validate_survey_inputs, convert_area_to_acres
from src.image_analysis import analyze_soil_image
from src.soil_analysis import comprehensive_soil_health_assessment
from src.crop_recommendation import generate_crop_recommendations
from src.yield_prediction import predict_crop_yield
from src.crop_comparison import build_crop_comparison
from src.reporting import generate_farmer_report_text, generate_report_csv_bytes


class TestFasalAI(unittest.TestCase):

    def test_01_supabase_health_and_tables(self):
        health = check_connection_health()
        self.assertTrue(health["connected"], "Supabase client should connect with valid credentials")
        self.assertIn("farms", health["tables"])
        self.assertTrue(health["tables"]["farms"]["accessible"])
        self.assertGreaterEqual(health["tables"]["farms"]["count"], 250)

    def test_02_unified_data_loader(self):
        unified_df, market_df, source = get_unified_agricultural_dataset()
        self.assertFalse(unified_df.empty, "Unified dataframe should not be empty")
        self.assertIn("farm_id", unified_df.columns)
        self.assertIn("ph", unified_df.columns)
        self.assertIn("current_crop", unified_df.columns)
        self.assertFalse(market_df.empty, "Market prices table should contain crop entries")

    def test_03_survey_cleaning_and_unit_conversion(self):
        # 1. Test hectare conversion
        acres = convert_area_to_acres(2.0, "Hectares")
        self.assertAlmostEqual(acres, 4.94, places=1)

        # 2. Test missing values & outlier handling
        raw_survey = {
            "farmer_name": "Test Farmer",
            "state": "Punjab",
            "area": 5.0,
            "area_unit": "Acres",
            "soil_ph": 15.0,  # invalid pH
            "nitrogen": None,  # missing N
            "annual_rainfall_mm": -50.0  # invalid rainfall
        }
        cleaned = clean_and_validate_survey_inputs(raw_survey)
        self.assertIn("data_quality_flags", cleaned)
        # Should fallback to regional defaults safely
        self.assertLessEqual(cleaned["ph"], 8.5)
        self.assertGreater(cleaned["nitrogen_kg_ha"], 0)
        self.assertIn("Estimated", cleaned["data_quality_flags"]["ph_source"])

    def test_04_image_analysis_inference(self):
        # Create a synthetic 100x100 RGB image
        img = Image.new("RGB", (100, 100), color=(140, 70, 50))
        result = analyze_soil_image(img)
        self.assertTrue(result["success"], "Visual soil classifier should succeed on RGB image")
        self.assertIn("predicted_soil_group", result)
        self.assertIn("confidence_pct", result)
        self.assertGreater(len(result["class_probabilities"]), 0)
        self.assertIn("disclaimer", result)

    def test_05_comprehensive_soil_assessment(self):
        soil_sample = {"ph": 5.2, "organic_carbon": 0.35, "nitrogen_kg_ha": 55.0, "phosphorus_kg_ha": 15.0, "potassium_kg_ha": 85.0}
        assessment = comprehensive_soil_health_assessment(soil_sample)
        self.assertLess(assessment["overall_health_score"], 80.0)
        self.assertGreater(len(assessment["recommended_amendments"]), 0)

    def test_06_yield_prediction_intervals(self):
        pred = predict_crop_yield(crop="Wheat", irrigation_method="Drip", irrigation_mm=380.0, soil_ph=7.1)
        self.assertGreater(pred["yield_q_acre"], 0.0)
        self.assertLessEqual(pred["yield_lower_80_q_acre"], pred["yield_q_acre"])
        self.assertGreaterEqual(pred["yield_upper_80_q_acre"], pred["yield_q_acre"])
        self.assertGreater(pred["yield_tonnes_ha"], 0.0)
        self.assertIn("drivers", pred)

    def test_07_crop_recommendations_and_water_cap(self):
        farm_state = {
            "farm_id": "test_farm",
            "farmer_name": "Test Farmer",
            "area_acres": 2.5,
            "current_crop": "Rice",
            "ph": 6.8,
            "nitrogen_kg_ha": 95.0,
            "phosphorus_kg_ha": 35.0,
            "potassium_kg_ha": 140.0,
            "district": "Ludhiana",
            "state": "Punjab"
        }
        recs = generate_crop_recommendations(farm_state, water_cap_mm=500.0)
        self.assertIsNotNone(recs["current_crop"])
        self.assertIsNotNone(recs["top_recommendation_1"])
        self.assertGreaterEqual(len(recs["ranked_crops"]), 8)

        # Check water cap flags
        for r in recs["ranked_crops"]:
            self.assertEqual(r["is_within_cap"], r["applied_mm"] <= 500.0)

    def test_08_crop_comparison_parity(self):
        curr = {"crop": "Rice", "yield_q_acre": 24.0, "gross_revenue": 54000.0, "total_cost": 28000.0, "net_profit": 26000.0, "water_liters": 7000000.0}
        alt = {"crop": "Maize", "yield_q_acre": 28.0, "gross_revenue": 60200.0, "total_cost": 22000.0, "net_profit": 38200.0, "water_liters": 2400000.0}
        comp = build_crop_comparison(curr, alt)

        self.assertEqual(comp["current_crop"], "Rice")
        self.assertEqual(comp["recommended_crop"], "Maize")
        self.assertEqual(comp["yield"]["abs_difference"], 4.0)
        self.assertAlmostEqual(comp["yield"]["pct_difference"], 16.7, places=1)
        self.assertEqual(comp["economics"]["profit_difference"], 12200.0)
        self.assertGreater(comp["water"]["water_saved_pct"], 50.0)

    def test_09_reporting_and_csv_generation(self):
        sample_report = {
            "farmer": {"name": "Test Farmer", "district": "Ludhiana", "state": "Punjab", "area_acres": 2.0},
            "soil": {"overall_health_score": 75.0, "health_rating": "Moderate", "ph": 7.2},
            "current_crop": {"crop": "Wheat", "yield_q_acre": 20.0, "net_profit": 30000.0, "water_liters": 3600000.0},
            "top_alternatives": [{"crop": "Maize", "yield_q_acre": 26.0, "net_profit": 42000.0, "profit_delta_rs": 12000.0, "water_saved_pct": 33.0, "is_within_cap": True}],
            "water_and_climate": {"water_cap_mm": 600.0, "recommended_irrigation": "Drip"}
        }
        report_text = generate_farmer_report_text(sample_report)
        self.assertIn("FASAL AI — FARM ADVISORY REPORT", report_text)
        self.assertIn("Test Farmer", report_text)

        csv_bytes = generate_report_csv_bytes(sample_report)
        self.assertGreater(len(csv_bytes), 0)
        df_csv = pd.read_csv(pd.io.common.BytesIO(csv_bytes))
        self.assertEqual(len(df_csv), 2)  # Current crop + 1 recommendation


if __name__ == "__main__":
    unittest.main()

