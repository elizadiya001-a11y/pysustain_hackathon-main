"""
views/current_crop_comparison_view.py
-------------------------------------
Current Crop Comparison Screen for FASAL AI.
Side-by-side yield, revenue, cost, profit, and groundwater trade-off analysis.
Enforces unit parity and explains why physical biomass differs from economic profit.
"""

import streamlit as st
import plotly.graph_objects as go
from src.crop_recommendation import generate_crop_recommendations
from src.crop_comparison import build_crop_comparison
from core.config import CROP_AGRONOMY


def render_current_crop_comparison():
    st.markdown('<div class="fasal-card-title">⚖️ Current Crop vs Alternative Comparison</div>', unsafe_allow_html=True)
    st.caption("Side-by-side yield, financial margin, and water balance comparison under equivalent agro-climatic conditions.")

    current_farm = st.session_state.get("current_farm", {})
    recs = generate_crop_recommendations(farm_state=current_farm, water_cap_mm=600.0)

    curr_res = recs["current_crop"]
    top1_res = recs["top_recommendation_1"]
    ranked_crops = recs["ranked_crops"]

    # Candidate Alternative Selector
    alt_options = [r["crop"] for r in ranked_crops if r["crop"] != curr_res["crop"]]
    selected_alt_crop = st.selectbox(
        "Choose an Alternative Crop to Compare:",
        options=alt_options,
        index=0 if alt_options else 0
    )

    alt_res = next((r for r in ranked_crops if r["crop"] == selected_alt_crop), top1_res)
    comp = build_crop_comparison(curr_res, alt_res)

    # 1. Headline Metric Cards
    col_m1, col_m2, col_m3 = st.columns(3)
    with col_m1:
        profit_delta = comp["economics"]["profit_difference"]
        st.markdown(f"""
        <div class="fasal-card" style="text-align: center;">
            <div style="font-size: 11px; font-weight: 700; color: #64748b;">NET PROFIT DELTA</div>
            <div style="font-size: 24px; font-weight: 800; color: {'#2d6a4f' if profit_delta >= 0 else '#d90429'}; margin: 4px 0;">
                {'+₹' if profit_delta >= 0 else '-₹'}{abs(profit_delta):,.0f}
            </div>
            <span style="font-size: 12px; color: #64748b;">
                ₹{comp['economics']['current_net_profit']:,.0f} ➔ ₹{comp['economics']['recommended_net_profit']:,.0f}
            </span>
        </div>
        """, unsafe_allow_html=True)

    with col_m2:
        water_saved = comp["water"]["water_saved_pct"]
        st.markdown(f"""
        <div class="fasal-card" style="text-align: center;">
            <div style="font-size: 11px; font-weight: 700; color: #64748b;">GROUNDWATER SAVING</div>
            <div style="font-size: 24px; font-weight: 800; color: #2d6a4f; margin: 4px 0;">
                {water_saved:+.0f}%
            </div>
            <span style="font-size: 12px; color: #64748b;">
                {comp['water']['current_water_liters']:,.0f}L ➔ {comp['water']['recommended_water_liters']:,.0f}L
            </span>
        </div>
        """, unsafe_allow_html=True)

    with col_m3:
        yield_diff = comp["yield"]["abs_difference"]
        st.markdown(f"""
        <div class="fasal-card" style="text-align: center;">
            <div style="font-size: 11px; font-weight: 700; color: #64748b;">YIELD PARITY (Q/ACRE)</div>
            <div style="font-size: 24px; font-weight: 800; color: #1e293b; margin: 4px 0;">
                {yield_diff:+.1f} q/ac
            </div>
            <span style="font-size: 12px; color: #64748b;">
                {comp['yield']['current_q_acre']} ➔ {comp['yield']['recommended_q_acre']} q/acre
            </span>
        </div>
        """, unsafe_allow_html=True)

    # 2. Side-by-Side Detailed Breakdown Table
    st.markdown("##### 📊 Detailed Economic & Agronomic Balance")
    data_rows = [
        {"Attribute": "Crop Type & Season", "Current Crop": f"{comp['current_crop']} ({curr_res.get('season')})", "Alternative Crop": f"{comp['recommended_crop']} ({alt_res.get('season')})", "Difference / Gain": "Seasonal Match"},
        {"Attribute": "Yield (Quintals / Acre)", "Current Crop": f"{comp['yield']['current_q_acre']} q/ac", "Alternative Crop": f"{comp['yield']['recommended_q_acre']} q/ac", "Difference / Gain": f"{comp['yield']['abs_difference']:+.2f} q/ac ({comp['yield']['pct_difference']:+.1f}%)" if comp['yield']['pct_difference'] is not None else "N/A"},
        {"Attribute": "Yield (Tonnes / Hectare)", "Current Crop": f"{comp['yield']['current_tonnes_ha']} t/ha", "Alternative Crop": f"{comp['yield']['recommended_tonnes_ha']} t/ha", "Difference / Gain": f"{(comp['yield']['recommended_tonnes_ha'] - comp['yield']['current_tonnes_ha']):+.2f} t/ha"},
        {"Attribute": "Gross Revenue", "Current Crop": f"₹{comp['economics']['current_gross_revenue']:,.0f}", "Alternative Crop": f"₹{comp['economics']['recommended_gross_revenue']:,.0f}", "Difference / Gain": f"+₹{comp['economics']['revenue_difference']:,.0f}" if comp['economics']['revenue_difference'] >= 0 else f"-₹{abs(comp['economics']['revenue_difference']):,.0f}"},
        {"Attribute": "Estimated Cultivation Cost", "Current Crop": f"₹{comp['economics']['current_cultivation_cost']:,.0f}", "Alternative Crop": f"₹{comp['economics']['recommended_cultivation_cost']:,.0f}", "Difference / Gain": f"₹{comp['economics']['cost_difference']:+,.0f}"},
        {"Attribute": "Net Profit Margin", "Current Crop": f"₹{comp['economics']['current_net_profit']:,.0f}", "Alternative Crop": f"₹{comp['economics']['recommended_net_profit']:,.0f}", "Difference / Gain": f"+₹{comp['economics']['profit_difference']:,.0f}" if comp['economics']['profit_difference'] >= 0 else f"-₹{abs(comp['economics']['profit_difference']):,.0f}"},
        {"Attribute": "Irrigation Water (Liters)", "Current Crop": f"{comp['water']['current_water_liters']:,.0f} L", "Alternative Crop": f"{comp['water']['recommended_water_liters']:,.0f} L", "Difference / Gain": f"{comp['water']['water_saved_pct']:.0f}% Conserved"},
        {"Attribute": "Aquifer Water Cap", "Current Crop": "Compliant" if curr_res.get("is_within_cap") else "Exceeded", "Alternative Crop": "Compliant" if alt_res.get("is_within_cap") else "Exceeded", "Difference / Gain": "✅ Within Cap" if alt_res.get("is_within_cap") else "⚠️ Exceeds Cap"}
    ]
    st.table(data_rows)

    # 3. Interactive Plotly Visual Comparison
    st.markdown("##### 📈 Financial & Resource Trade-Off Visuals")
    c_chart1, c_chart2 = st.columns(2)

    with c_chart1:
        # Profit vs Cost Bar Chart
        fig_bar = go.Figure(data=[
            go.Bar(
                name="Gross Revenue",
                x=[comp["current_crop"], comp["recommended_crop"]],
                y=[comp["economics"]["current_gross_revenue"], comp["economics"]["recommended_gross_revenue"]],
                marker_color="#2d6a4f"
            ),
            go.Bar(
                name="Cultivation Cost",
                x=[comp["current_crop"], comp["recommended_crop"]],
                y=[comp["economics"]["current_cultivation_cost"], comp["economics"]["recommended_cultivation_cost"]],
                marker_color="#e76f51"
            ),
            go.Bar(
                name="Net Profit",
                x=[comp["current_crop"], comp["recommended_crop"]],
                y=[comp["economics"]["current_net_profit"], comp["economics"]["recommended_net_profit"]],
                marker_color="#52b788"
            )
        ])
        fig_bar.update_layout(
            barmode="group",
            height=280,
            margin=dict(l=10, r=10, t=20, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            yaxis=dict(title="₹ INR", showgrid=True, gridcolor="#e2e8f0"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_bar, use_container_width=True, config={"displayModeBar": False})

    with c_chart2:
        # Water consumption comparison
        fig_water = go.Figure(data=[
            go.Bar(
                x=[comp["current_crop"], comp["recommended_crop"]],
                y=[comp["water"]["current_water_liters"] / 1000.0, comp["water"]["recommended_water_liters"] / 1000.0],
                marker_color=["#457b9d", "#a8dadc"],
                text=[f"{comp['water']['current_water_liters']/1000:.0f} kL", f"{comp['water']['recommended_water_liters']/1000:.0f} kL"],
                textposition="auto"
            )
        ])
        fig_water.update_layout(
            title="Total Water Demand (kL)",
            height=280,
            margin=dict(l=10, r=10, t=30, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            yaxis=dict(title="kL (m³)", showgrid=True, gridcolor="#e2e8f0")
        )
        st.plotly_chart(fig_water, use_container_width=True, config={"displayModeBar": False})

    # 4. Agronomic Rationale & Limitations
    st.markdown("##### 💡 Agronomic Rationale & Honest Limitations")
    c_r1, c_r2 = st.columns(2)
    with c_r1:
        st.markdown("""
        <div class="fasal-card" style="height: 180px;">
            <strong style="color: #1b4332;">Key Agronomic Reasons:</strong>
            <ul style="font-size: 13px; color: #1e293b; margin-top: 8px;">
        """, unsafe_allow_html=True)
        for r in comp["key_reasons"]:
            st.markdown(f"<li>{r}</li>", unsafe_allow_html=True)
        st.markdown("</ul></div>", unsafe_allow_html=True)

    with c_r2:
        st.markdown("""
        <div class="fasal-card" style="height: 180px;">
            <strong style="color: #64748b;">Limitations &amp; Data Caveats:</strong>
            <ul style="font-size: 12px; color: #475569; margin-top: 8px;">
        """, unsafe_allow_html=True)
        for l in comp["limitations"]:
            st.markdown(f"<li>{l}</li>", unsafe_allow_html=True)
        st.markdown("</ul></div>", unsafe_allow_html=True)

