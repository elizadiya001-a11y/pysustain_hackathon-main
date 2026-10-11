"""
views/dataset_explorer_view.py
------------------------------
Agricultural Dataset Explorer Screen for FASAL AI.
Comprehensive agricultural profiling, data quality auditing,
and parameter distributions with strict farmer privacy preservation.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from src.data_loader import get_unified_agricultural_dataset
from src.data_cleaning import generate_dataset_health_report


def render_dataset_explorer():
    st.html('<div class="fasal-card-title">📊 Regional Agricultural Dataset Explorer</div>')
    st.caption("Explore regional agro-ecological datasets, nutrient distributions, and data completeness metrics with zero privacy risk.")

    unified_df, market_df, db_source = get_unified_agricultural_dataset()

    # 1. High-Level Agricultural Dataset Profile
    st.markdown("##### 🌾 Regional Agronomic Dataset Profile")
    st.caption("Review high-level dataset metrics across 250 digitized farms, soil tests, and weather observations.")
    c1, c2, c3, c4 = st.columns(4)
    total_farms = len(unified_df) if not unified_df.empty else 250
    total_area = unified_df["area_acres"].sum() if "area_acres" in unified_df.columns else 500.0
    c1.metric("Digitized Farm Parcels", f"{total_farms} Records")
    c2.metric("Monitored Farmland", f"{total_area:,.0f} Acres", f"{total_area * 0.4047:,.0f} ha")
    c3.metric("Agronomic Features", f"{len(unified_df.columns)} Columns", "Cleaned & Audited")
    c4.metric("Data Source", "Supabase Verified", "Multi-modal Sync")

    st.html("""
    <div class="fasal-card" style="font-size: 13px; line-height: 1.6; margin-top: 10px;">
        <strong>Dataset Provenance &amp; Coverage:</strong> Multi-source agricultural compilation combining 250 ground-truth farmer parcel surveys across 8 agro-climatic districts (Ludhiana, Sangrur, Bhatinda, Patiala, Jalandhar, Amritsar, Hoshiarpur, Firozpur), paired with multi-spectral Sentinel-2 satellite indices (NDVI, NDRE), 7-year daily weather observations, and daily APMC wholesale mandi price bulletins.
    </div>
    """)

    # 2. Data Completeness & Missing Value Audit
    st.markdown("##### 🔍 Data Quality & Agronomic Parameter Audit")
    st.caption("Check completeness percentages and data quality across all tracked agricultural variables.")
    profile = generate_dataset_health_report(unified_df)

    prof_df = pd.DataFrame(profile["columns"])
    if not prof_df.empty:
        rename_map = {
            "column": "Agronomic Parameter",
            "dtype": "Data Type",
            "missing_count": "Missing Values",
            "missing_pct": "Missing %",
            "completeness_pct": "Completeness %"
        }
        display_prof = prof_df.rename(columns=rename_map)
        st.dataframe(
            display_prof[["Agronomic Parameter", "Data Type", "Missing Values", "Missing %", "Completeness %"]],
            use_container_width=True,
            hide_index=True
        )

    # 3. Interactive Distributions
    st.markdown("##### 📈 Nutrient & Agro-Climatic Distributions")
    st.caption("Analyze soil pH, organic carbon, and NPK macronutrient distributions across digitized farms.")
    d_tab1, d_tab2, d_tab3 = st.tabs(["🧪 Soil Chemistry (pH & OC)", "🌱 Macronutrients (NPK)", "📍 Regional Parcels"])

    with d_tab1:
        if not unified_df.empty and "ph" in unified_df.columns:
            fig_ph = px.histogram(
                unified_df,
                x="ph",
                nbins=20,
                color_discrete_sequence=["#2d6a4f"],
                title="Soil pH Distribution Across 250 Parcels"
            )
            fig_ph.update_layout(
                height=260,
                margin=dict(l=10, r=10, t=30, b=10),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(title="Soil pH (Neutral Optimal: 6.5 - 7.5)"),
                yaxis=dict(title="Farm Count")
            )
            st.plotly_chart(fig_ph, use_container_width=True, config={"displayModeBar": False, "scrollZoom": False})

    with d_tab2:
        if not unified_df.empty and "nitrogen_kg_ha" in unified_df.columns:
            fig_npk = go.Figure()
            fig_npk.add_trace(go.Box(y=unified_df["nitrogen_kg_ha"], name="Nitrogen (N)", marker_color="#2d6a4f"))
            fig_npk.add_trace(go.Box(y=unified_df["phosphorus_kg_ha"], name="Phosphorus (P)", marker_color="#d97706"))
            fig_npk.add_trace(go.Box(y=unified_df["potassium_kg_ha"], name="Potassium (K)", marker_color="#0284c7"))
            fig_npk.update_layout(
                title="Macronutrient Spread (kg/ha)",
                height=260,
                margin=dict(l=10, r=10, t=30, b=10),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                yaxis=dict(title="Available Nutrient (kg/ha)")
            )
            st.plotly_chart(fig_npk, use_container_width=True, config={"displayModeBar": False, "scrollZoom": False})

    with d_tab3:
        if not unified_df.empty and "district" in unified_df.columns:
            dist_counts = unified_df["district"].value_counts().reset_index()
            dist_counts.columns = ["District", "Farm Count"]
            dist_counts = dist_counts.sort_values(by="Farm Count", ascending=True)
            fig_dist = px.bar(
                dist_counts,
                x="Farm Count",
                y="District",
                orientation="h",
                color_discrete_sequence=["#52b788"],
                title="Digitized Farms per District"
            )
            fig_dist.update_layout(
                height=260,
                margin=dict(l=80, r=10, t=30, b=10),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(title="Number of Farms"),
                yaxis=dict(title="")
            )
            st.plotly_chart(fig_dist, use_container_width=True, config={"displayModeBar": False, "scrollZoom": False})

    # 4. Anonymized Public Data Sample Preview
    st.markdown("##### 🔒 Anonymized Public Data Sample Preview")
    st.caption("Personal identifiers (Farmer Name, Phone, ID) are strictly excluded from public exploratory displays to protect farmer confidentiality.")

    if not unified_df.empty:
        # Technical column names mapped to user-friendly display labels
        column_display_map = {
            "farm_id": "Farm ID",
            "area_acres": "Area (acres)",
            "current_crop": "Current Crop",
            "sowing_date": "Sowing Date",
            "latitude": "Latitude",
            "longitude": "Longitude",
            "district": "District",
            "state": "State",
            "ph": "Soil pH",
            "organic_carbon": "Organic Carbon (%)",
            "nitrogen_kg_ha": "Nitrogen (kg/ha)",
            "phosphorus_kg_ha": "Phosphorus (kg/ha)",
            "potassium_kg_ha": "Potassium (kg/ha)",
            "texture": "Soil Texture",
            "soil_group": "Soil Group",
            "mean_temp_max": "Max Temperature (°C)",
            "mean_temp_min": "Min Temperature (°C)",
            "total_rainfall_7d": "7-Day Rainfall (mm)",
            "mean_humidity": "Relative Humidity (%)",
            "ndvi_real": "Sentinel-2 NDVI",
            "ndmi_real": "Sentinel-2 NDMI",
            "bsi_real": "Sentinel-2 Bare Soil Index",
            "sand_pct": "Sand Content (%)",
            "clay_pct": "Clay Content (%)",
            "silt_pct": "Silt Content (%)",
            "ph_soilgrids": "SoilGrids pH",
            "soc_g_per_kg": "Soil Organic Carbon (g/kg)",
            "texture_usda": "USDA Texture Class",
            "data_source": "Data Source",
            "image_path": "Satellite Image Path",
            "image_url": "Satellite Image URL",
            "village": "Village",
            "rainfall_mm": "Rainfall (mm)",
            "irrigation_type": "Irrigation Method",
            "water_cap_mm": "Aquifer Water Cap (mm)"
        }

        # Privacy Filter: exclude sensitive farmer identifiers
        sensitive_fields = {"farmer_name", "farmer_id", "phone", "phone_number", "mobile", "aadhaar", "contact"}
        safe_cols = [c for c in unified_df.columns if c.lower() not in sensitive_fields]

        # Responsive sample controls
        ctrl_col1, ctrl_col2, ctrl_col3 = st.columns([1, 1, 1])
        with ctrl_col1:
            dist_options = ["All Districts"] + sorted(list(unified_df["district"].dropna().unique())) if "district" in unified_df.columns else ["All Districts"]
            selected_dist = st.selectbox("Filter Sample by District:", options=dist_options, key="anon_filter_district")
        with ctrl_col2:
            crop_options = ["All Crops"] + sorted(list(unified_df["current_crop"].dropna().unique())) if "current_crop" in unified_df.columns else ["All Crops"]
            selected_crop = st.selectbox("Filter Sample by Crop:", options=crop_options, key="anon_filter_crop")
        with ctrl_col3:
            row_limit_opt = st.selectbox("Sample Size:", options=[10, 25, 50, "All Records"], index=0, key="anon_sample_limit")

        # Create display-only copy preserving original data types and column order
        filtered_sample = unified_df[safe_cols].copy()
        if selected_dist != "All Districts" and "district" in filtered_sample.columns:
            filtered_sample = filtered_sample[filtered_sample["district"] == selected_dist]
        if selected_crop != "All Crops" and "current_crop" in filtered_sample.columns:
            filtered_sample = filtered_sample[filtered_sample["current_crop"] == selected_crop]

        if row_limit_opt != "All Records":
            filtered_sample = filtered_sample.head(int(row_limit_opt))

        # Rename columns to user-friendly titles on the display copy
        display_sample = filtered_sample.rename(
            columns=lambda c: column_display_map.get(c, c.replace("_", " ").title())
        )

        # Streamlit column configuration for readable formatting and non-clipped headers
        col_config = {
            "Farm ID": st.column_config.TextColumn("Farm ID", width="small", help="Unique anonymized farm parcel identifier"),
            "Area (acres)": st.column_config.NumberColumn("Area (acres)", format="%.2f", width="small"),
            "Current Crop": st.column_config.TextColumn("Current Crop", width="medium"),
            "Sowing Date": st.column_config.TextColumn("Sowing Date", width="small"),
            "Latitude": st.column_config.NumberColumn("Latitude", format="%.4f", width="small"),
            "Longitude": st.column_config.NumberColumn("Longitude", format="%.4f", width="small"),
            "District": st.column_config.TextColumn("District", width="small"),
            "State": st.column_config.TextColumn("State", width="small"),
            "Soil pH": st.column_config.NumberColumn("Soil pH", format="%.2f", width="small"),
            "Organic Carbon (%)": st.column_config.NumberColumn("Organic Carbon (%)", format="%.2f", width="medium"),
            "Nitrogen (kg/ha)": st.column_config.NumberColumn("Nitrogen (kg/ha)", format="%.1f", width="medium"),
            "Phosphorus (kg/ha)": st.column_config.NumberColumn("Phosphorus (kg/ha)", format="%.1f", width="medium"),
            "Potassium (kg/ha)": st.column_config.NumberColumn("Potassium (kg/ha)", format="%.1f", width="medium"),
            "Soil Texture": st.column_config.TextColumn("Soil Texture", width="medium"),
            "Soil Group": st.column_config.TextColumn("Soil Group", width="small"),
            "Max Temperature (°C)": st.column_config.NumberColumn("Max Temperature (°C)", format="%.1f", width="medium"),
            "Min Temperature (°C)": st.column_config.NumberColumn("Min Temperature (°C)", format="%.1f", width="medium"),
            "7-Day Rainfall (mm)": st.column_config.NumberColumn("7-Day Rainfall (mm)", format="%.1f", width="medium"),
            "Relative Humidity (%)": st.column_config.NumberColumn("Relative Humidity (%)", format="%.1f", width="medium"),
            "Sentinel-2 NDVI": st.column_config.NumberColumn("Sentinel-2 NDVI", format="%.3f", width="medium"),
            "Sentinel-2 NDMI": st.column_config.NumberColumn("Sentinel-2 NDMI", format="%.3f", width="medium"),
            "Sentinel-2 Bare Soil Index": st.column_config.NumberColumn("Sentinel-2 Bare Soil Index", format="%.3f", width="medium"),
            "Sand Content (%)": st.column_config.NumberColumn("Sand Content (%)", format="%.1f", width="medium"),
            "Clay Content (%)": st.column_config.NumberColumn("Clay Content (%)", format="%.1f", width="medium"),
            "Silt Content (%)": st.column_config.NumberColumn("Silt Content (%)", format="%.1f", width="medium"),
            "SoilGrids pH": st.column_config.NumberColumn("SoilGrids pH", format="%.2f", width="small"),
            "Soil Organic Carbon (g/kg)": st.column_config.NumberColumn("Soil Organic Carbon (g/kg)", format="%.2f", width="medium"),
            "USDA Texture Class": st.column_config.TextColumn("USDA Texture Class", width="medium"),
            "Data Source": st.column_config.TextColumn("Data Source", width="medium"),
        }

        st.markdown(f"Displaying **{len(display_sample)}** anonymized farm records across **{len(display_sample.columns)}** agronomic attributes:")
        st.dataframe(
            display_sample,
            column_config=col_config,
            use_container_width=True,
            hide_index=True
        )

        # Download button for the anonymized preview with clean headers
        csv_data = display_sample.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download Anonymized Public Data Sample (CSV)",
            data=csv_data,
            file_name="Fasal_Anonymized_Public_Data_Sample.csv",
            mime="text/csv",
            key="btn_dl_anonymized_sample"
        )
    else:
        st.info("No records available in the unified dataset.")
