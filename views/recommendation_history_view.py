"""
views/recommendation_history_view.py
------------------------------------
Historical Farm Records & Assessment Audit Log for FASAL AI.
Displays the comprehensive portfolio of 250 digitized farms, regional baselines,
and verified farmer assessment audits.
"""

import streamlit as st
import pandas as pd
from src.data_loader import get_unified_agricultural_dataset
from src.supabase_client import fetch_recommendation_history


def render_recommendation_history():
    st.html('<div class="fasal-card-title">📜 Historical Farm Records & Assessment Audit</div>')
    st.caption("Audit and explore the regional digitized farm registry alongside verified field assessment reports.")

    farms_df, _, _ = get_unified_agricultural_dataset()
    df_history = fetch_recommendation_history(limit=100)

    # Check for assessments submitted in the current session
    session_assessments = st.session_state.get("submitted_assessments", [])
    if session_assessments:
        df_sess = pd.DataFrame(session_assessments)
        if not df_history.empty:
            df_history = pd.concat([df_sess, df_history], ignore_index=True).drop_duplicates(subset=["farmer_name", "district", "current_crop"])
        else:
            df_history = df_sess

    tab_registry, tab_audits = st.tabs(["📁 Digitized Farm Portfolio (250 Parcels)", "📋 Field Assessment Audit Log"])

    # TAB 1: Digitized Farm Portfolio
    with tab_registry:
        st.caption("Comprehensive registry of all 250 geo-referenced farm parcels with soil chemistry and baseline cropping history.")
        if not farms_df.empty:
            # Registry KPIs
            c1, c2, c3, c4 = st.columns(4)
            total_acres = farms_df["area_acres"].sum() if "area_acres" in farms_df.columns else 500.0
            num_districts = farms_df["district"].nunique() if "district" in farms_df.columns else 8
            mean_ph = farms_df["ph"].mean() if "ph" in farms_df.columns else 7.2

            c1.metric("Registered Parcels", f"{len(farms_df)} Farms")
            c2.metric("Total Monitored Area", f"{total_acres:,.0f} Acres", f"{total_acres * 0.4047:,.0f} ha")
            c3.metric("Agro-Districts", f"{num_districts} Zones")
            c4.metric("Mean Soil pH", f"{mean_ph:.2f}", "Neutral / Arable")

            # Filters
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                districts = ["All Districts"] + sorted(list(farms_df["district"].dropna().unique()))
                sel_dist = st.selectbox("Filter Portfolio by District", options=districts, key="reg_filter_dist")
            with col_f2:
                crops = ["All Crops"] + sorted(list(farms_df["current_crop"].dropna().unique()))
                sel_crop = st.selectbox("Filter Portfolio by Crop", options=crops, key="reg_filter_crop")

            filtered_reg = farms_df.copy()
            if sel_dist != "All Districts":
                filtered_reg = filtered_reg[filtered_reg["district"] == sel_dist]
            if sel_crop != "All Crops":
                filtered_reg = filtered_reg[filtered_reg["current_crop"] == sel_crop]

            st.markdown(f"Displaying **{len(filtered_reg)}** farm parcel records:")
            cols_to_show = [c for c in ["farm_id", "farmer_name", "state", "district", "village", "area_acres", "current_crop", "texture", "ph", "nitrogen_kg_ha", "sowing_date"] if c in filtered_reg.columns]
            
            # Map column names to human-readable labels
            reg_column_map = {
                "farm_id": "Farm Parcel ID",
                "farmer_name": "Farmer Name",
                "state": "State",
                "district": "District",
                "village": "Village",
                "area_acres": "Parcel Area (Acres)",
                "current_crop": "Current Baseline Crop",
                "texture": "Soil Texture Group",
                "ph": "Soil Reaction (pH)",
                "nitrogen_kg_ha": "Available Nitrogen (kg/ha)",
                "sowing_date": "Sowing Date"
            }
            display_reg = filtered_reg[cols_to_show].rename(columns=reg_column_map)
            st.dataframe(display_reg, use_container_width=True, hide_index=True)

            csv_reg = display_reg.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 Download Digitized Farm Registry (CSV)",
                data=csv_reg,
                file_name="Fasal_Farm_Registry_Portfolio.csv",
                mime="text/csv",
                key="btn_dl_registry"
            )
        else:
            st.info("Loading digitized farm portfolio...")

    # TAB 2: Field Assessment Audit Log
    with tab_audits:
        st.caption("Immutable audit log of all completed farmer assessments, baseline yield comparisons, and recommendations.")
        if df_history.empty:
            st.html("""
            <div class="fasal-card" style="border: 1px dashed #cbd5e1; text-align: center; padding: 30px;">
                <div style="font-size: 32px; margin-bottom: 10px;">📋</div>
                <h4 style="color: #1b4332; margin: 0 0 6px 0;">No New Field Assessments Logged Yet</h4>
                <p style="font-size: 13px; color: #475569; margin-bottom: 14px;">
                    Assessments submitted via the <strong>Farm Assessment</strong> tab are automatically audited and logged here with yield differentials, economic balance, and field photo records.
                </p>
            </div>
            """)
        else:
            col_a1, col_a2 = st.columns(2)
            with col_a1:
                hist_districts = ["All Districts"] + sorted(list(df_history["district"].dropna().unique())) if "district" in df_history.columns else ["All Districts"]
                sel_hist_dist = st.selectbox("Filter Audits by District", options=hist_districts, key="hist_filter_dist")
            with col_a2:
                hist_crops = ["All Crops"] + sorted(list(df_history["current_crop"].dropna().unique())) if "current_crop" in df_history.columns else ["All Crops"]
                sel_hist_crop = st.selectbox("Filter Audits by Baseline Crop", options=hist_crops, key="hist_filter_crop")

            filtered_hist = df_history.copy()
            if sel_hist_dist != "All Districts" and "district" in filtered_hist.columns:
                filtered_hist = filtered_hist[filtered_hist["district"] == sel_hist_dist]
            if sel_hist_crop != "All Crops" and "current_crop" in filtered_hist.columns:
                filtered_hist = filtered_hist[filtered_hist["current_crop"] == sel_hist_crop]

            st.markdown(f"Displaying **{len(filtered_hist)}** audited farmer assessment(s):")
            display_cols = [c for c in ["created_at", "farmer_name", "district", "current_crop", "top_recommendation", "expected_yield_q_acre", "estimated_profit_inr", "yield_delta_pct"] if c in filtered_hist.columns]
            
            audit_column_map = {
                "created_at": "Assessment Timestamp",
                "farmer_name": "Farmer Name",
                "district": "District",
                "current_crop": "Baseline Crop",
                "top_recommendation": "Top Recommended Crop",
                "expected_yield_q_acre": "Expected Yield (q/acre)",
                "estimated_profit_inr": "Estimated Net Profit (₹)",
                "yield_delta_pct": "Yield Delta (%)"
            }
            display_hist = filtered_hist[display_cols].rename(columns=audit_column_map)
            st.dataframe(display_hist, use_container_width=True, hide_index=True)

            csv_bytes = display_hist.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 Download Field Assessment Audits (CSV)",
                data=csv_bytes,
                file_name="Fasal_Assessment_Audits.csv",
                mime="text/csv",
                key="btn_dl_audits"
            )
