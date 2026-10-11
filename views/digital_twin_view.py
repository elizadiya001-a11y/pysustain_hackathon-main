"""
views/digital_twin_view.py
--------------------------
Digital Farm Twin Screen for FASAL AI.
Interactive physics-informed what-if simulator, groundwater pumping energy,
5-pillar sustainability scorecard, and bilingual SMS generator.
Strictly distinguishes real measured data from AI simulations.
"""

import streamlit as st
import plotly.graph_objects as go
from src.data_loader import get_unified_agricultural_dataset
from core.config import CROP_AGRONOMY, IRRIGATION_METHODS, WEATHER_SCENARIOS
from core.simulation import simulate_scenario, get_bau_baseline
from core.sustainability import calculate_sustainability_score
from core.advisory import generate_sms_advisory


def render_digital_twin():
    st.markdown('<div class="fasal-card-title">🌐 Farm Digital Twin Simulator</div>', unsafe_allow_html=True)
    st.caption("Precision simulation engine combining non-linear agronomy response surfaces, groundwater physics, and SDG sustainability metrics.")

    current_farm = st.session_state.get("current_farm", {})

    # Status Distinction Pill
    st.markdown("""
    <div style="display: flex; gap: 10px; margin-bottom: 15px;">
        <span style="background: #e8f5e9; color: #1b4332; font-size: 12px; font-weight: bold; padding: 4px 10px; border-radius: 6px; border: 1px solid #a5d6a7;">
            🟢 Real Measured Parcel: Soil pH, Texture, GPS Coordinates, Satellite Indices
        </span>
        <span style="background: #e0f2fe; color: #0369a1; font-size: 12px; font-weight: bold; padding: 4px 10px; border-radius: 6px; border: 1px solid #bae6fd;">
            🔵 AI &amp; Physics Simulation: Yield Interval, Pumping Energy, Water Mass Balance
        </span>
    </div>
    """, unsafe_allow_html=True)

    # 1. Simulator Control Levers
    with st.expander("🎛️ Digital Twin Simulation Levers", expanded=True):
        col_l1, col_l2, col_l3 = st.columns(3)
        with col_l1:
            sim_crop = st.selectbox(
                "Simulated Crop",
                options=list(CROP_AGRONOMY.keys()),
                index=list(CROP_AGRONOMY.keys()).index(current_farm.get("current_crop", "Wheat")) if current_farm.get("current_crop") in CROP_AGRONOMY else 0
            )
            sim_method = st.selectbox(
                "Irrigation Method",
                options=list(IRRIGATION_METHODS.keys()),
                index=0
            )
        with col_l2:
            agro = CROP_AGRONOMY[sim_crop]
            default_irrig = (agro["irrig_mm"][0] + agro["irrig_mm"][1]) / 2.0
            sim_irrig_mm = st.slider(
                "Irrigation Applied Depth (mm)",
                min_value=50.0,
                max_value=1500.0,
                value=float(default_irrig),
                step=25.0
            )
            sim_weather = st.selectbox(
                "Climate / Weather Stress Scenario",
                options=list(WEATHER_SCENARIOS.keys()),
                index=0
            )
        with col_l3:
            sim_n = st.slider("Applied Nitrogen (kg/ha)", min_value=10.0, max_value=250.0, value=float((agro["N"][0]+agro["N"][1])/2.0), step=5.0)
            use_msp = st.checkbox("Price at Guaranteed MSP (uncheck for Wholesale Market Price)", value=True)

    # Run Simulation
    sim = simulate_scenario(
        farm_state=current_farm,
        crop=sim_crop,
        irrigation_method=sim_method,
        irrigation_mm=sim_irrig_mm,
        applied_n=sim_n,
        weather_scenario=sim_weather,
        use_msp=use_msp
    )
    sust = calculate_sustainability_score(sim, current_farm)

    # 2. Key Output Metrics
    st.markdown("##### 📊 Scenario Simulation Results (<50ms execution)")
    c_m1, c_m2, c_m3, c_m4 = st.columns(4)
    with c_m1:
        st.markdown(f"""
        <div class="fasal-card" style="text-align: center;">
            <div style="font-size: 11px; font-weight: 700; color: #64748b;">PREDICTED YIELD (80% CI)</div>
            <div style="font-size: 22px; font-weight: 800; color: #1b4332; margin: 4px 0;">
                {sim['yield_q_acre']} q/ac
            </div>
            <span style="font-size: 11px; color: #64748b;">
                [{sim['yield_lower_80']} – {sim['yield_upper_80']} q/ac]
            </span>
        </div>
        """, unsafe_allow_html=True)

    with c_m2:
        st.markdown(f"""
        <div class="fasal-card" style="text-align: center;">
            <div style="font-size: 11px; font-weight: 700; color: #64748b;">NET PROFIT / SEASON</div>
            <div style="font-size: 22px; font-weight: 800; color: {'#2d6a4f' if sim['net_profit'] >= 0 else '#d90429'}; margin: 4px 0;">
                ₹{sim['net_profit']:,.0f}
            </div>
            <span style="font-size: 11px; color: #64748b;">
                ₹{sim['net_profit_acre']:,.0f} / acre
            </span>
        </div>
        """, unsafe_allow_html=True)

    with c_m3:
        st.markdown(f"""
        <div class="fasal-card" style="text-align: center;">
            <div style="font-size: 11px; font-weight: 700; color: #64748b;">WATER CONSUMPTION</div>
            <div style="font-size: 22px; font-weight: 800; color: #0284c7; margin: 4px 0;">
                {sim['water_liters']:,.0f} L
            </div>
            <span style="font-size: 11px; color: {'#2d6a4f' if sim['water_saved_pct'] >= 0 else '#d90429'};">
                {sim['water_saved_pct']:+.0f}% vs BAU Flood
            </span>
        </div>
        """, unsafe_allow_html=True)

    with c_m4:
        st.markdown(f"""
        <div class="fasal-card" style="text-align: center;">
            <div style="font-size: 11px; font-weight: 700; color: #64748b;">SUSTAINABILITY INDEX</div>
            <div style="font-size: 22px; font-weight: 800; color: #2d6a4f; margin: 4px 0;">
                {sust['composite_score']}/100
            </div>
            <span style="font-size: 11px; color: #64748b;">
                {sust['rating']} (SDG Aligned)
            </span>
        </div>
        """, unsafe_allow_html=True)

    # 3. Physics Groundwater Pumping Energy & SHAP-style Drivers
    st.markdown("##### ⚡ Groundwater Pumping Energy Physics & Feature Drivers")
    c_p1, c_p2 = st.columns(2)
    with c_p1:
        pump_kwh = sim.get('pump_energy_kwh', sim.get('energy_kwh', 0.0))
        energy_cost = sim.get('energy_cost', 0.0)
        energy_saved_rs = sim.get('energy_saved_rs', sim.get('energy_saved_kwh', 0.0) * 6.5)
        st.markdown(f"""
        <div class="fasal-card" style="height: 190px;">
            <strong style="color: #1b4332;">Groundwater Pumping Physics:</strong>
            <div style="font-size: 12px; color: #475569; margin-top: 4px;">
                Formula: <code>E = (ρ × g × V × H) / (3.6 × 10⁶ × η)</code>
            </div>
            <div style="margin-top: 10px; font-size: 13px; line-height: 1.6;">
                <div>💧 Lift Head (Aquifer Depth): <strong>40.0 meters</strong></div>
                <div>⚡ Pumping Energy Consumed: <strong>{pump_kwh:.1f} kWh</strong></div>
                <div>🔌 Estimated Power Bill: <strong>₹{energy_cost:,.0f}</strong></div>
                <div>🌱 Energy Saved vs Baseline: <strong>₹{energy_saved_rs:,.0f}</strong></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with c_p2:
        st.markdown("""
        <div class="fasal-card" style="height: 190px;">
            <strong style="color: #1b4332;">Top Agronomic Drivers (SHAP Attribution):</strong>
        """, unsafe_allow_html=True)
        for drv in sim.get("drivers", [])[:3]:
            drv_color = "#2d6a4f" if drv["type"] == "positive" else ("#d90429" if drv["type"] == "negative" else "#64748b")
            st.markdown(f"""
            <div style="font-size: 12px; margin-top: 4px;">
                <strong>{drv['driver']}</strong>: <span style="color: {drv_color}; font-weight: bold;">{drv['impact']}</span>
                <span style="color: #64748b;">— {drv['detail'][:60]}...</span>
            </div>
            """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # 4. Feature Phone Bilingual SMS Generator (<= 160 Chars)
    st.markdown("##### 📱 Last-Mile SMS Advisory (<= 160 Characters)")
    st.caption("Generates instant, concise SMS texts in English and Hindi for extension officers sending alerts to basic feature phones.")

    sms_lang = st.radio("Language", options=["English", "Hindi (हिंदी)"], horizontal=True)
    lang_key = "English" if "English" in sms_lang else "Hindi"
    sms_res = generate_sms_advisory(current_farm, sim, language=lang_key)

    st.markdown(f"""
    <div style="background: #1e293b; color: #f8fafc; font-family: monospace; padding: 14px 18px; border-radius: 8px; font-size: 14px; margin-top: 6px;">
        {sms_res['sms_text']}
    </div>
    <div style="display: flex; justify-content: space-between; font-size: 12px; color: #64748b; margin-top: 4px;">
        <span>Character Count: <strong>{sms_res['char_count']}/160</strong></span>
        <span>Standard GSM Compliant: <strong>{'✅ Yes' if sms_res['is_valid_sms'] else '❌ Exceeded'}</strong></span>
    </div>
    """, unsafe_allow_html=True)

