"""
views/farm_assessment.py
------------------------
Farm Assessment Screen for FASAL AI.
Comprehensive farmer survey questionnaire, field photograph visual analysis,
and satellite inspection with data cleaning and validation flags.
"""

import os
from pathlib import Path
import streamlit as st
from PIL import Image

from src.data_loader import get_unified_agricultural_dataset, get_farm_record_by_id
from src.data_cleaning import clean_and_validate_survey_inputs
from src.image_analysis import analyze_soil_image
from src.crop_recommendation import generate_crop_recommendations
from src.supabase_client import upload_field_image, save_recommendation_to_db
from core.config import CROP_AGRONOMY, IRRIGATION_METHODS


def render_farm_assessment():
    st.markdown('<div class="fasal-card-title">📋 Comprehensive Farm Assessment</div>', unsafe_allow_html=True)
    st.caption("Enter your field details, upload soil or field photographs, and generate an AI-backed crop plan.")

    farms_df, _, _ = get_unified_agricultural_dataset()
    current_farm = st.session_state.get("current_farm", farms_df.iloc[0].to_dict() if not farms_df.empty else {})

    # Preset autofill option
    st.markdown("##### ⚡ Quick Pre-Fill Option")
    preset_choice = st.selectbox(
        "Load data from an existing digitized farm or enter a new farm profile:",
        options=["[Create New Farm Assessment]"] + [
            f"{r['farm_id']} — {r['farmer_name']} ({r['current_crop']}, {r['district']})"
            for _, r in farms_df.iterrows()
        ]
    )

    if preset_choice != "[Create New Farm Assessment]":
        chosen_id = preset_choice.split(" — ")[0].strip()
        if chosen_id != current_farm.get("farm_id"):
            st.session_state["current_farm"] = get_farm_record_by_id(chosen_id)
            current_farm = st.session_state["current_farm"]
            st.rerun()

    # Form
    with st.form("farmer_survey_form"):
        # Section 1: Farmer & Location Details
        st.markdown("#### 1. Farmer & Location Demographics")
        c1, c2, c3 = st.columns(3)
        with c1:
            farmer_name = st.text_input("Farmer Name *", value=current_farm.get("farmer_name", "Rajesh Kumar"))
        with c2:
            farmer_id = st.text_input("Farmer ID / Aadhaar / KCC (Optional)", value=current_farm.get("farm_id", "FASAL-2026-001"))
        with c3:
            village = st.text_input("Village", value="Rampur")

        c4, c5, c6 = st.columns(3)
        with c4:
            state = st.selectbox(
                "State *",
                options=["Punjab", "Haryana", "Maharashtra", "Karnataka", "West Bengal", "Andhra Pradesh", "Rajasthan", "Uttar Pradesh"],
                index=["Punjab", "Haryana", "Maharashtra", "Karnataka", "West Bengal", "Andhra Pradesh", "Rajasthan", "Uttar Pradesh"].index(current_farm.get("state", "Punjab")) if current_farm.get("state") in ["Punjab", "Haryana", "Maharashtra", "Karnataka", "West Bengal", "Andhra Pradesh", "Rajasthan", "Uttar Pradesh"] else 0
            )
        with c5:
            district = st.text_input("District *", value=current_farm.get("district", "Ludhiana"))
        with c6:
            pass

        # Section 2: Landholding & Current Practice
        st.markdown("#### 2. Landholding & Current Crop Practice")
        col_a1, col_a2, col_a3 = st.columns(3)
        with col_a1:
            area_val = st.number_input("Field Area *", min_value=0.1, max_value=50.0, value=float(current_farm.get("area_acres", 2.0)), step=0.25)
        with col_a2:
            area_unit = st.selectbox("Measurement Unit *", options=["Acres", "Hectares", "Bigha (Standard)", "Guntha"])
        with col_a3:
            current_crop = st.selectbox(
                "Current Crop *",
                options=list(CROP_AGRONOMY.keys()),
                index=list(CROP_AGRONOMY.keys()).index(current_farm.get("current_crop", "Wheat")) if current_farm.get("current_crop") in CROP_AGRONOMY else 0
            )

        col_b1, col_b2, col_b3 = st.columns(3)
        with col_b1:
            hist_yield = st.number_input("Current Crop Historical Yield (q/acre, if known)", min_value=0.0, max_value=500.0, value=18.5, step=0.5)
        with col_b2:
            season = st.selectbox("Growing Season *", options=["Rabi (Winter)", "Kharif (Monsoon)", "Zaid (Summer)"])
        with col_b3:
            sowing_date = st.date_input("Target Sowing / Planting Date")

        # Section 3: Soil Test & Chemistry (Optional / Soil Card)
        st.markdown("#### 3. Soil Health & Testing (Optional)")
        st.info("ℹ️ If you have not tested your soil recently, leave fields blank. The system will use agro-climatic regional baselines and flag estimates transparently.")

        col_s1, col_s2, col_s3 = st.columns(3)
        with col_s1:
            soil_type = st.selectbox(
                "Soil Type (if known)",
                options=["Unknown / Need Assessment", "Alluvial", "Black / Regur", "Red", "Clay", "Laterite", "Sandy Loam", "Loam"]
            )
        with col_s2:
            soil_ph = st.number_input("Soil pH (3.5 - 10.5, if known)", min_value=0.0, max_value=12.0, value=float(current_farm.get("ph", 7.2)), step=0.1)
        with col_s3:
            org_carbon = st.number_input("Organic Carbon (% if known)", min_value=0.0, max_value=3.0, value=float(current_farm.get("organic_carbon", 0.55)), step=0.05)

        col_npk1, col_npk2, col_npk3 = st.columns(3)
        with col_npk1:
            soil_n = st.number_input("Available Nitrogen (kg/ha, optional)", min_value=0.0, max_value=500.0, value=float(current_farm.get("nitrogen_kg_ha", 95.0)), step=5.0)
        with col_npk2:
            soil_p = st.number_input("Available Phosphorus (kg/ha, optional)", min_value=0.0, max_value=200.0, value=float(current_farm.get("phosphorus_kg_ha", 28.0)), step=5.0)
        with col_npk3:
            soil_k = st.number_input("Available Potassium (kg/ha, optional)", min_value=0.0, max_value=600.0, value=float(current_farm.get("potassium_kg_ha", 150.0)), step=10.0)

        # Section 4: Water, Climate & Budget
        st.markdown("#### 4. Water, Climate & Economic Preferences")
        col_w1, col_w2, col_w3 = st.columns(3)
        with col_w1:
            irrigation_type = st.selectbox("Primary Irrigation System *", options=list(IRRIGATION_METHODS.keys()), index=0)
        with col_w2:
            annual_rain = st.number_input("Seasonal Rainfall (mm, optional)", min_value=0.0, max_value=3000.0, value=450.0, step=50.0)
        with col_w3:
            water_cap = st.slider("District / Aquifer Water Cap (mm)", min_value=200, max_value=1200, value=600, step=50)

        col_e1, col_e2 = st.columns(2)
        with col_e1:
            farming_budget = st.number_input("Expected Working Capital Budget (₹ INR)", min_value=5000, max_value=500000, value=45000, step=5000)
        with col_e2:
            crop_pref = st.multiselect(
                "Crop Preferences or Exclusions",
                options=list(CROP_AGRONOMY.keys()),
                default=[]
            )

        submit_btn = st.form_submit_button("🌾 Run Assessment & Generate Recommendations", use_container_width=True)

    # Section 5: Field Imagery & Satellite Review
    st.markdown("---")
    st.markdown("#### 📸 Field Photograph & Satellite Imagery")
    st.caption("Upload an image of your field or topsoil. FASAL's MobileNetV3 vision model will classify the visual soil type and texture.")

    col_img1, col_img2 = st.columns(2)
    uploaded_photo = None
    with col_img1:
        uploaded_file = st.file_uploader("Upload Field / Soil Photo (JPG, PNG, WEBP)", type=["jpg", "jpeg", "png", "webp"])
        if uploaded_file is not None:
            image_bytes = uploaded_file.read()
            st.image(image_bytes, caption=f"Uploaded: {uploaded_file.name}", use_container_width=True)
            with st.spinner("Analyzing soil visual characteristics..."):
                img_analysis = analyze_soil_image(image_bytes)
                if img_analysis.get("success"):
                    st.success(f"🌱 Visual Soil Group: **{img_analysis['predicted_soil_group']}** ({img_analysis['confidence_pct']}% confidence)")
                    st.caption(f"Estimated Drainage: {img_analysis['visual_features']['estimated_drainage']} · Workability: {img_analysis['visual_features']['physical_workability']}")
                    st.info(f"⚠️ {img_analysis['disclaimer']}")

                    # Try uploading to Supabase Storage
                    storage_url = upload_field_image(image_bytes, uploaded_file.name)
                    if storage_url:
                        st.caption(f"☁️ Backed up securely to Supabase Storage private bucket.")
                    uploaded_photo = uploaded_file.name
                else:
                    st.error(f"Image analysis error: {img_analysis.get('error')}")

    with col_img2:
        # Check if active farm has a real satellite chip locally
        farm_chip_path = Path(f"satellite_chips/{current_farm.get('farm_id', 'plot_001')}_rgb.png")
        if farm_chip_path.exists():
            st.image(str(farm_chip_path), caption=f"🛰️ Sentinel-2 MSI Chip ({current_farm.get('farm_id')})", use_container_width=True)
            if "ndvi_real" in current_farm and current_farm["ndvi_real"] is not None:
                st.markdown(f"""
                <div style="font-size: 12px; background: #f8fafc; border: 1px solid #e2e8f0; padding: 8px; border-radius: 6px;">
                    <div>🌿 <strong>Real Sentinel-2 NDVI:</strong> {current_farm.get('ndvi_real', 0.46):.3f}</div>
                    <div>💧 <strong>Real Moisture Index (NDMI):</strong> {current_farm.get('ndmi_real', -0.02):.3f}</div>
                    <div>🧱 <strong>SoilGrids Topsoil Texture:</strong> {current_farm.get('texture_usda', 'Clay Loam')} (Sand: {current_farm.get('sand_pct', 42):.1f}%, Clay: {current_farm.get('clay_pct', 32):.1f}%)</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="border: 2px dashed #cbd5e1; border-radius: 8px; padding: 25px; text-align: center; color: #64748b;">
                🛰️ <strong>No Satellite Chip Available</strong><br>
                <small>Select an existing digitized parcel (e.g. plot_001 to plot_250) to view Sentinel-2 multispectral imagery.</small>
            </div>
            """, unsafe_allow_html=True)

    # Process Form Submission
    if submit_btn:
        survey_dict = {
            "farmer_name": farmer_name,
            "farmer_id": farmer_id,
            "village": village,
            "district": district,
            "state": state,
            "area": area_val,
            "area_unit": area_unit,
            "current_crop": current_crop,
            "historical_yield": hist_yield,
            "season": season,
            "soil_type": soil_type,
            "soil_ph": soil_ph if soil_ph > 0 else None,
            "organic_carbon": org_carbon if org_carbon > 0 else None,
            "nitrogen": soil_n if soil_n > 0 else None,
            "phosphorus": soil_p if soil_p > 0 else None,
            "potassium": soil_k if soil_k > 0 else None,
            "irrigation_type": irrigation_type,
            "annual_rainfall_mm": annual_rain if annual_rain > 0 else None,
            "water_cap_mm": water_cap,
            "budget": farming_budget
        }

        # 1. Clean and validate inputs
        cleaned_farm = clean_and_validate_survey_inputs(survey_dict)
        st.session_state["current_farm"] = cleaned_farm

        # 2. Run recommendations
        rec_results = generate_crop_recommendations(
            farm_state=cleaned_farm,
            water_cap_mm=float(water_cap),
            preferred_irrigation=irrigation_type,
            use_msp=True
        )
        st.session_state["current_recommendations"] = rec_results

        # 3. Store assessment into Supabase recommendations_history
        top_alt = rec_results.get("top_recommendation_1", {})
        curr_cr = rec_results.get("current_crop", {})
        db_payload = {
            "farmer_name": farmer_name,
            "farmer_id": farmer_id,
            "state": state,
            "district": district,
            "village": village,
            "area_acres": cleaned_farm["area_acres"],
            "current_crop": current_crop,
            "current_yield_q_acre": curr_cr.get("yield_q_acre"),
            "soil_type": cleaned_farm.get("texture"),
            "soil_ph": cleaned_farm.get("ph"),
            "soil_n": cleaned_farm.get("nitrogen_kg_ha"),
            "soil_p": cleaned_farm.get("phosphorus_kg_ha"),
            "soil_k": cleaned_farm.get("potassium_kg_ha"),
            "irrigation_type": irrigation_type,
            "rainfall_mm": cleaned_farm.get("rainfall_mm"),
            "budget_inr": farming_budget,
            "top_recommendation": top_alt.get("crop", "Maize"),
            "expected_yield_q_acre": top_alt.get("yield_q_acre"),
            "estimated_profit_inr": top_alt.get("net_profit"),
            "yield_delta_pct": round(((top_alt.get("yield_q_acre", 0) - curr_cr.get("yield_q_acre", 1)) / max(0.1, curr_cr.get("yield_q_acre", 1))) * 100.0, 1),
            "image_storage_path": uploaded_photo or "none"
        }
        saved_db = save_recommendation_to_db(db_payload)

        st.success("✅ Farm Assessment successfully analyzed and recommendation plan generated!")
        if saved_db:
            st.info("☁️ Record saved to Supabase recommendations_history.")
        else:
            st.caption("ℹ️ Cloud table pending migration; record cached in local session state.")

        # Switch tab
        st.session_state["nav_radio"] = "Crop Recommendations"
        st.session_state["current_tab"] = "Crop Recommendations"
        st.rerun()

