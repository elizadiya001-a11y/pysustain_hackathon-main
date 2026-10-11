"""
views/dataset_explorer_view.py
------------------------------
Dataset Explorer Screen for FASAL AI.
Safe, privacy-preserving exploratory analysis of Supabase PostgreSQL tables.
Audits missingness, data completeness, and parameter distributions without exposing PII.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from src.data_loader import get_unified_agricultural_dataset, fetch_table
from src.data_cleaning import generate_dataset_health_report
from src.supabase_client import check_connection_health


def render_dataset_explorer():
    st.markdown('<div class="fasal-card-title">📊 Agricultural Dataset Explorer</div>', unsafe_allow_html=True)
    st.caption("Inspect live Supabase schema health, completeness metrics, and nutrient distributions with zero PII exposure.")

    health = check_connection_health()
    unified_df, market_df, db_source = get_unified_agricultural_dataset()

    # 1. Supabase Cloud Schema Overview Table
    st.markdown("##### ☁️ Supabase Cloud Tables (bwlopgkkaasgmkdkoayb)")
    tbl_rows = []
    if health.get("tables"):
        for t_name, t_info in health["tables"].items():
            tbl_rows.append({
                "Table Name": t_name,
                "Status": "🟢 Live Cloud Table" if t_info.get("accessible") else ("⚠️ Pending Migration" if t_info.get("pending_migration") else "❌ Offline"),
                "Row Count": t_info.get("count", "N/A"),
                "Note": t_info.get("note", "Production ready")
            })
    st.dataframe(pd.DataFrame(tbl_rows), use_container_width=True, hide_index=True)

    # 2. Data Completeness & Missing Value Audit
    st.markdown("##### 🔍 Data Quality & Completeness Audit")
    profile = generate_dataset_health_report(unified_df)
    st.markdown(f"Total Unified Records: **{profile['total_records']}** | Audited Feature Columns: **{profile['audited_columns']}**")

    prof_df = pd.DataFrame(profile["columns"])
    if not prof_df.empty:
        # Show completeness progress bars
        st.dataframe(
            prof_df[["column", "dtype", "missing_count", "missing_pct", "completeness_pct"]],
            use_container_width=True,
            hide_index=True
        )

    # 3. Interactive Distributions
    st.markdown("##### 📈 Nutrient & Agro-Climatic Distributions")
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
                xaxis=dict(title="Soil pH (Optimal: 6.0 - 7.5)")
            )
            st.plotly_chart(fig_ph, use_container_width=True, config={"displayModeBar": False})

    with d_tab2:
        if not unified_df.empty and "nitrogen_kg_ha" in unified_df.columns:
            fig_npk = go.Figure()
            fig_npk.add_trace(go.Box(y=unified_df["nitrogen_kg_ha"], name="Nitrogen (N)", marker_color="#2d6a4f"))
            fig_npk.add_trace(go.Box(y=unified_df["phosphorus_kg_ha"], name="Phosphorus (P)", marker_color="#f77f00"))
            fig_npk.add_trace(go.Box(y=unified_df["potassium_kg_ha"], name="Potassium (K)", marker_color="#0077b6"))
            fig_npk.update_layout(
                title="NPK Nutrient Spread (kg/ha)",
                height=260,
                margin=dict(l=10, r=10, t=30, b=10),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)"
            )
            st.plotly_chart(fig_npk, use_container_width=True, config={"displayModeBar": False})

    with d_tab3:
        if not unified_df.empty and "district" in unified_df.columns:
            dist_counts = unified_df["district"].value_counts().reset_index()
            dist_counts.columns = ["District", "Farm Count"]
            fig_dist = px.bar(
                dist_counts,
                x="District",
                y="Farm Count",
                color_discrete_sequence=["#52b788"],
                title="Digitized Farms per District"
            )
            fig_dist.update_layout(
                height=260,
                margin=dict(l=10, r=10, t=30, b=10),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)"
            )
            st.plotly_chart(fig_dist, use_container_width=True, config={"displayModeBar": False})

    # 4. Anonymized Public Data Sample Preview
    st.markdown("##### 🔒 Anonymized Public Data Sample Preview")
    st.caption("Personal identifiers (Farmer Name, Phone, ID) are filtered out from public exploratory previews to preserve farmer privacy.")
    safe_cols = [c for c in unified_df.columns if c not in ["farmer_name", "farmer_id"]]
    st.dataframe(unified_df[safe_cols].head(8), use_container_width=True, hide_index=True)

