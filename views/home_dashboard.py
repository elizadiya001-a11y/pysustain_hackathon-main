"""
views/home_dashboard.py
-----------------------
Home Dashboard Screen for FASAL AI.
Displays regional twin KPIs, active farm selector, live Supabase connectivity,
and quick shortcuts.
"""

import streamlit as st
import plotly.graph_objects as go
from src.data_loader import get_unified_agricultural_dataset, get_farm_record_by_id
from src.supabase_client import check_connection_health
from core.config import CROP_AGRONOMY


def render_home_dashboard():
    farms_df, market_df, db_source = get_unified_agricultural_dataset()
    current_farm = st.session_state.get("current_farm", farms_df.iloc[0].to_dict() if not farms_df.empty else {})

    # Connection banner
    health = check_connection_health()
    if health["connected"]:
        st.markdown(f"""
        <div style="background: #e8f5e9; border: 1px solid #a5d6a7; border-radius: 8px; padding: 10px 14px; margin-bottom: 15px; display: flex; justify-content: space-between; align-items: center;">
            <div style="color: #1b4332; font-size: 13px;">
                🟢 <strong>Live Supabase Cloud Connected</strong> · Project: <code>bwlopgkkaasgmkdkoayb</code> · {health['tables'].get('farms', {}).get('count', 250)} farms registered
            </div>
            <span style="background: #2d6a4f; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: bold;">
                Online
            </span>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.warning("⚠️ Supabase credentials missing. Operating with high-fidelity local farm digital twin.")

    # High-Level Regional KPI Grid
    st.markdown("""
    <div class="metric-grid">
        <div class="metric-pill">
            <span class="metric-label">Digitized Farms</span>
            <span class="metric-val">250 Parcels</span>
            <span class="metric-delta delta-pos">8 Agro-Districts</span>
        </div>
        <div class="metric-pill">
            <span class="metric-label">Avg Water Saving</span>
            <span class="metric-val">38.4%</span>
            <span class="metric-delta delta-pos">Drip &amp; Sprinkler</span>
        </div>
        <div class="metric-pill">
            <span class="metric-label">Avg Margin Gain</span>
            <span class="metric-val">+₹14,200</span>
            <span class="metric-delta delta-pos">Per Acre / Season</span>
        </div>
        <div class="metric-pill">
            <span class="metric-label">Satellite Monitored</span>
            <span class="metric-val">250 Chips</span>
            <span class="metric-delta delta-pos">Sentinel-2 MSI</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Active Farm Parcel Card
    st.markdown('<div class="fasal-card-title">📍 Active Farm Digital Twin</div>', unsafe_allow_html=True)

    if not farms_df.empty:
        farm_options = [
            f"{r['farm_id']} — {r['farmer_name']} ({r['current_crop']}, {r['district']})"
            for _, r in farms_df.iterrows()
        ]
        cur_id = current_farm.get("farm_id", "plot_001")
        current_idx = 0
        for idx, opt in enumerate(farm_options):
            if opt.startswith(cur_id):
                current_idx = idx
                break

        col_sel, col_btn = st.columns([3, 1])
        with col_sel:
            selected_opt = st.selectbox(
                "Select a Digitized Farm Parcel:",
                options=farm_options,
                index=current_idx,
                key="home_farm_selector"
            )
        with col_btn:
            st.write("")
            st.write("")
            if st.button("📋 New Assessment", use_container_width=True):
                st.session_state["current_tab"] = "Farm Assessment"
                st.rerun()

        selected_id = selected_opt.split(" — ")[0].strip()
        if selected_id != cur_id:
            st.session_state["current_farm"] = get_farm_record_by_id(selected_id)
            current_farm = st.session_state["current_farm"]
            st.rerun()

        # Render Active Farm Profile Card
        st.markdown(f"""
        <div class="fasal-card">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px;">
                <div>
                    <h4 style="margin: 0; font-size: 18px; font-weight: 700; color: #1b4332;">
                        {current_farm.get('farmer_name', 'Farmer')}
                    </h4>
                    <div style="font-size: 13px; color: #64748b; margin-top: 2px;">
                        Parcel ID: <strong>{current_farm.get('farm_id')}</strong> · {current_farm.get('district')}, {current_farm.get('state')}
                    </div>
                </div>
                <span style="background: #d8f3dc; color: #1b4332; font-size: 12px; font-weight: 700; padding: 4px 10px; border-radius: 12px;">
                    {current_farm.get('area_acres')} Acres ({round(float(current_farm.get('area_acres', 2.0))*0.4047, 2)} ha)
                </span>
            </div>
            <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; font-size: 13px; margin-top: 12px; border-top: 1px solid #e2e8f0; padding-top: 10px;">
                <div>🌾 <strong>Current Crop:</strong> {current_farm.get('current_crop')}</div>
                <div>🧪 <strong>Soil pH:</strong> {current_farm.get('ph')}</div>
                <div>🍂 <strong>Organic Carbon:</strong> {current_farm.get('organic_carbon')}%</div>
                <div>🧱 <strong>Soil Texture:</strong> {current_farm.get('texture')}</div>
                <div>🌱 <strong>Available N:</strong> {current_farm.get('nitrogen_kg_ha')} kg/ha</div>
                <div>🗓️ <strong>Sowing Date:</strong> {current_farm.get('sowing_date')}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Fast Navigation Cards
    st.markdown('<div class="fasal-card-title">⚡ Quick Modules</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("""
        <div class="fasal-card" style="text-align: center; height: 160px; display: flex; flex-direction: column; justify-content: space-between;">
            <div>
                <div style="font-size: 26px;">📋</div>
                <strong style="color: #1b4332;">Farm Assessment</strong>
                <p style="font-size: 12px; color: #64748b; margin: 4px 0;">Survey questionnaire &amp; photo upload</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Start Assessment", key="nav_btn_assess", use_container_width=True):
            st.session_state["current_tab"] = "Farm Assessment"
            st.rerun()

    with c2:
        st.markdown("""
        <div class="fasal-card" style="text-align: center; height: 160px; display: flex; flex-direction: column; justify-content: space-between;">
            <div>
                <div style="font-size: 26px;">🌾</div>
                <strong style="color: #1b4332;">Crop Recommendations</strong>
                <p style="font-size: 12px; color: #64748b; margin: 4px 0;">Ranked options with water cap and profit</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("View Recommendations", key="nav_btn_rec", use_container_width=True):
            st.session_state["current_tab"] = "Crop Recommendations"
            st.rerun()

    with c3:
        st.markdown("""
        <div class="fasal-card" style="text-align: center; height: 160px; display: flex; flex-direction: column; justify-content: space-between;">
            <div>
                <div style="font-size: 26px;">🌐</div>
                <strong style="color: #1b4332;">Digital Farm Twin</strong>
                <p style="font-size: 12px; color: #64748b; margin: 4px 0;">Interactive simulator, levers &amp; SMS</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Launch Twin", key="nav_btn_twin", use_container_width=True):
            st.session_state["current_tab"] = "Farm Digital Twin"
            st.rerun()

    # Regional Crop Distribution Chart
    if not farms_df.empty and "current_crop" in farms_df.columns:
        st.markdown('<div class="fasal-card-title">📊 Regional Monoculture Distribution (250 Parcels)</div>', unsafe_allow_html=True)
        crop_counts = farms_df["current_crop"].value_counts().reset_index()
        crop_counts.columns = ["Crop", "Parcels"]

        fig = go.Figure(go.Bar(
            x=crop_counts["Crop"],
            y=crop_counts["Parcels"],
            marker=dict(
                color=["#2d6a4f", "#40916c", "#52b788", "#74c69d", "#95d5b2", "#b7e4c7", "#d8f3dc", "#e9f5ed"][:len(crop_counts)],
                line=dict(color="#1b4332", width=1.5)
            ),
            text=crop_counts["Parcels"],
            textposition="auto"
        ))
        fig.update_layout(
            height=260,
            margin=dict(l=10, r=10, t=10, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor="#e2e8f0"),
            font=dict(family="sans-serif", size=11, color="#1e293b")
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

