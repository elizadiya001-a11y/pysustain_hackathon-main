"""
views/current_crop_comparison_view.py
-------------------------------------
Current Crop Comparison Screen for FASAL AI.
Side-by-side yield, revenue, cost, profit, and groundwater trade-off analysis.
Enforces unit parity and explains why physical biomass differs from economic profit.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from src.crop_recommendation import generate_crop_recommendations
from src.crop_comparison import build_crop_comparison
from core.config import CROP_AGRONOMY


def render_current_crop_comparison():
    st.html('<div class="fasal-card-title">⚖️ Current Crop vs Alternative Comparison</div>')
    st.caption("Compare your existing crop with alternative crops using available agronomic and economic data.")

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
        index=0 if alt_options else 0,
        help="Select any alternative crop from the database catalog to perform an instant head-to-head economic comparison."
    )

    alt_res = next((r for r in ranked_crops if r["crop"] == selected_alt_crop), top1_res)
    comp = build_crop_comparison(curr_res, alt_res)

    # 1. Headline Metric Cards
    col_m1, col_m2, col_m3 = st.columns(3)
    with col_m1:
        profit_delta = comp["economics"].get("profit_difference", 0.0)
        profit_color = "#2d6a4f" if profit_delta >= 0 else "#d90429"
        st.html(f"""
        <div class="fasal-card" style="text-align: center;">
            <div style="font-size: 11px; font-weight: 700; color: #475569;">NET PROFIT GAIN</div>
            <div style="font-size: 24px; font-weight: 800; color: {profit_color}; margin: 4px 0;">
                {'+₹' if profit_delta >= 0 else '-₹'}{abs(profit_delta):,.0f}
            </div>
            <span style="font-size: 12px; color: #475569;">
                ₹{comp['economics'].get('current_net_profit', 0.0):,.0f} ➔ ₹{comp['economics'].get('recommended_net_profit', 0.0):,.0f}
            </span>
        </div>
        """)

    with col_m2:
        water_saved = comp["water"].get("water_saved_pct", 0.0)
        st.html(f"""
        <div class="fasal-card" style="text-align: center;">
            <div style="font-size: 11px; font-weight: 700; color: #475569;">GROUNDWATER CONSERVATION</div>
            <div style="font-size: 24px; font-weight: 800; color: #2d6a4f; margin: 4px 0;">
                {water_saved:+.0f}%
            </div>
            <span style="font-size: 12px; color: #475569;">
                {comp['water'].get('current_water_liters', 0.0):,.0f}L ➔ {comp['water'].get('recommended_water_liters', 0.0):,.0f}L
            </span>
        </div>
        """)

    with col_m3:
        yield_diff = comp["yield"].get("abs_difference", 0.0)
        st.html(f"""
        <div class="fasal-card" style="text-align: center;">
            <div style="font-size: 11px; font-weight: 700; color: #475569;">YIELD DIFFERENCE</div>
            <div style="font-size: 24px; font-weight: 800; color: #1e293b; margin: 4px 0;">
                {yield_diff:+.1f} q/ac
            </div>
            <span style="font-size: 12px; color: #475569;">
                {comp['yield'].get('current_q_acre', 0.0)} ➔ {comp['yield'].get('recommended_q_acre', 0.0)} q/acre
            </span>
        </div>
        """)

    # 2. Side-by-Side Detailed Breakdown
    st.markdown("##### 📊 Detailed Economic & Agronomic Balance")
    st.caption("Review side-by-side revenue, cost, profit margins, and water requirements under identical farm acreage.")

    col_comp_a, col_comp_b = st.columns(2)
    with col_comp_a:
        st.html(f"""
        <div class="fasal-card" style="border-top: 4px solid #64748b; background: #ffffff;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <span style="font-size: 11px; font-weight: 700; color: #64748b;">CURRENT BASELINE</span>
                <span style="background: #f1f5f9; color: #475569; font-size: 11px; font-weight: 600; padding: 2px 8px; border-radius: 10px;">
                    {curr_res.get('season', 'Rabi')}
                </span>
            </div>
            <h3 style="margin: 0 0 10px 0; color: #1e293b;">{comp.get('current_crop', 'Current Crop')}</h3>
            <div style="font-size: 13px; line-height: 1.8; color: #334155;">
                <div>🌾 <strong>Yield (q/ac):</strong> {comp['yield'].get('current_q_acre', 0.0)} q/ac ({comp['yield'].get('current_tonnes_ha', 0.0)} t/ha)</div>
                <div>💰 <strong>Gross Revenue:</strong> ₹{comp['economics'].get('current_gross_revenue', 0.0):,.0f}</div>
                <div>📉 <strong>Cultivation Cost:</strong> ₹{comp['economics'].get('current_cultivation_cost', 0.0):,.0f}</div>
                <div>🏷️ <strong>Net Profit:</strong> ₹{comp['economics'].get('current_net_profit', 0.0):,.0f} (₹{comp['economics'].get('current_net_profit_acre', 0.0):,.0f}/ac)</div>
                <div>💧 <strong>Water Used:</strong> {comp['water'].get('current_water_liters', 0.0):,.0f} L</div>
                <div>⚖️ <strong>Water Cap:</strong> {'✅ Compliant' if curr_res.get('is_within_cap') else '⚠️ Exceeded'}</div>
            </div>
        </div>
        """)

    with col_comp_b:
        st.html(f"""
        <div class="fasal-card" style="border-top: 4px solid #2d6a4f; background: #f0fdf4;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <span style="font-size: 11px; font-weight: 700; color: #166534;">RECOMMENDED ALTERNATIVE</span>
                <span style="background: #dcfce7; color: #166534; font-size: 11px; font-weight: 600; padding: 2px 8px; border-radius: 10px;">
                    {alt_res.get('season', 'Rabi')} · {alt_res.get('suitability_score', 85)}% Match
                </span>
            </div>
            <h3 style="margin: 0 0 10px 0; color: #1b4332;">{comp.get('recommended_crop', 'Alternative Crop')}</h3>
            <div style="font-size: 13px; line-height: 1.8; color: #1e293b;">
                <div>🌾 <strong>Yield (q/ac):</strong> {comp['yield'].get('recommended_q_acre', 0.0)} q/ac ({comp['yield'].get('recommended_tonnes_ha', 0.0)} t/ha)</div>
                <div>💰 <strong>Gross Revenue:</strong> ₹{comp['economics'].get('recommended_gross_revenue', 0.0):,.0f}</div>
                <div>📉 <strong>Cultivation Cost:</strong> ₹{comp['economics'].get('recommended_cultivation_cost', 0.0):,.0f}</div>
                <div>🏷️ <strong>Net Profit:</strong> <span style="color: #166534; font-weight: bold;">₹{comp['economics'].get('recommended_net_profit', 0.0):,.0f}</span> (₹{comp['economics'].get('recommended_net_profit_acre', 0.0):,.0f}/ac)</div>
                <div>💧 <strong>Water Used:</strong> {comp['water'].get('recommended_water_liters', 0.0):,.0f} L ({comp['water'].get('water_saved_pct', 0.0):.0f}% saved)</div>
                <div>⚖️ <strong>Water Cap:</strong> {'✅ Within Cap' if alt_res.get('is_within_cap') else '⚠️ Exceeds Cap'}</div>
            </div>
        </div>
        """)

    data_rows = [
        {"Agronomic & Economic Parameter": "Crop Name & Cropping Season", "Current Baseline Crop": f"{comp.get('current_crop')} ({curr_res.get('season')})", "Recommended Alternative": f"{comp.get('recommended_crop')} ({alt_res.get('season')})", "Net Difference / Benefit": "Crop Diversification Match"},
        {"Agronomic & Economic Parameter": "Yield in Quintals per Acre (q/ac)", "Current Baseline Crop": f"{comp['yield'].get('current_q_acre')} q/ac", "Recommended Alternative": f"{comp['yield'].get('recommended_q_acre')} q/ac", "Net Difference / Benefit": f"{comp['yield'].get('abs_difference', 0.0):+.2f} q/ac ({comp['yield'].get('pct_difference', 0.0):+.1f}%)" if comp['yield'].get('pct_difference') is not None else "N/A"},
        {"Agronomic & Economic Parameter": "Yield in Tonnes per Hectare (t/ha)", "Current Baseline Crop": f"{comp['yield'].get('current_tonnes_ha')} t/ha", "Recommended Alternative": f"{comp['yield'].get('recommended_tonnes_ha')} t/ha", "Net Difference / Benefit": f"{(comp['yield'].get('recommended_tonnes_ha', 0.0) - comp['yield'].get('current_tonnes_ha', 0.0)):+.2f} t/ha"},
        {"Agronomic & Economic Parameter": "Gross Revenue (₹)", "Current Baseline Crop": f"₹{comp['economics'].get('current_gross_revenue', 0.0):,.0f}", "Recommended Alternative": f"₹{comp['economics'].get('recommended_gross_revenue', 0.0):,.0f}", "Net Difference / Benefit": f"+₹{comp['economics'].get('revenue_difference', 0.0):,.0f}" if comp['economics'].get('revenue_difference', 0.0) >= 0 else f"-₹{abs(comp['economics'].get('revenue_difference', 0.0)):,.0f}"},
        {"Agronomic & Economic Parameter": "Estimated Cultivation Cost (₹)", "Current Baseline Crop": f"₹{comp['economics'].get('current_cultivation_cost', 0.0):,.0f}", "Recommended Alternative": f"₹{comp['economics'].get('recommended_cultivation_cost', 0.0):,.0f}", "Net Difference / Benefit": f"₹{comp['economics'].get('cost_difference', 0.0):+,.0f}"},
        {"Agronomic & Economic Parameter": "Net Profit Margin (₹)", "Current Baseline Crop": f"₹{comp['economics'].get('current_net_profit', 0.0):,.0f}", "Recommended Alternative": f"₹{comp['economics'].get('recommended_net_profit', 0.0):,.0f}", "Net Difference / Benefit": f"+₹{comp['economics'].get('profit_difference', 0.0):,.0f}" if comp['economics'].get('profit_difference', 0.0) >= 0 else f"-₹{abs(comp['economics'].get('profit_difference', 0.0)):,.0f}"},
        {"Agronomic & Economic Parameter": "Net Profit per Acre (₹/acre)", "Current Baseline Crop": f"₹{comp['economics'].get('current_net_profit_acre', 0.0):,.0f}/ac", "Recommended Alternative": f"₹{comp['economics'].get('recommended_net_profit_acre', 0.0):,.0f}/ac", "Net Difference / Benefit": f"₹{comp['economics'].get('profit_acre_difference', 0.0):+,.0f}/ac"},
        {"Agronomic & Economic Parameter": "Irrigation Water Demand (Liters)", "Current Baseline Crop": f"{comp['water'].get('current_water_liters', 0.0):,.0f} L", "Recommended Alternative": f"{comp['water'].get('recommended_water_liters', 0.0):,.0f} L", "Net Difference / Benefit": f"{comp['water'].get('water_saved_pct', 0.0):.0f}% Conserved"},
        {"Agronomic & Economic Parameter": "Aquifer Water Cap Feasibility", "Current Baseline Crop": "Compliant" if curr_res.get("is_within_cap") else "Exceeded", "Recommended Alternative": "Compliant" if alt_res.get("is_within_cap") else "Exceeded", "Net Difference / Benefit": "✅ Within Cap" if alt_res.get("is_within_cap") else "⚠️ Exceeds Cap"}
    ]
    st.dataframe(pd.DataFrame(data_rows), use_container_width=True, hide_index=True)

    # 3. Interactive Plotly Visual Comparison
    st.markdown("##### 📈 Financial & Resource Trade-Off Visuals")
    st.caption("Visualize financial returns and water consumption trade-offs side-by-side.")

    c_chart1, c_chart2 = st.columns(2)

    with c_chart1:
        # Profit vs Cost Bar Chart
        fig_bar = go.Figure(data=[
            go.Bar(
                name="Gross Revenue (₹)",
                x=[comp["current_crop"], comp["recommended_crop"]],
                y=[comp["economics"].get("current_gross_revenue", 0.0), comp["economics"].get("recommended_gross_revenue", 0.0)],
                marker_color="#2d6a4f"
            ),
            go.Bar(
                name="Cultivation Cost (₹)",
                x=[comp["current_crop"], comp["recommended_crop"]],
                y=[comp["economics"].get("current_cultivation_cost", 0.0), comp["economics"].get("recommended_cultivation_cost", 0.0)],
                marker_color="#d97706"
            ),
            go.Bar(
                name="Net Profit (₹)",
                x=[comp["current_crop"], comp["recommended_crop"]],
                y=[comp["economics"].get("current_net_profit", 0.0), comp["economics"].get("recommended_net_profit", 0.0)],
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
        st.plotly_chart(fig_bar, use_container_width=True, config={"displayModeBar": False, "scrollZoom": False})

    with c_chart2:
        # Water consumption comparison
        curr_kl = comp["water"].get("current_water_liters", 0.0) / 1000.0
        rec_kl = comp["water"].get("recommended_water_liters", 0.0) / 1000.0
        fig_water = go.Figure(data=[
            go.Bar(
                x=[comp["current_crop"], comp["recommended_crop"]],
                y=[curr_kl, rec_kl],
                marker_color=["#0284c7", "#38bdf8"],
                text=[f"{curr_kl:.0f} kL", f"{rec_kl:.0f} kL"],
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
        st.plotly_chart(fig_water, use_container_width=True, config={"displayModeBar": False, "scrollZoom": False})

    # 4. Agronomic Rationale & Limitations
    st.markdown("##### 💡 Agronomic Rationale & Scientific Limitations")
    st.caption("Understand why specific crop transitions are advantageous and what field factors must be considered.")

    c_r1, c_r2 = st.columns(2)
    with c_r1:
        st.html(f"""
        <div class="fasal-card" style="min-height: 180px;">
            <strong style="color: #1b4332;">Key Agronomic Reasons:</strong>
            <ul style="font-size: 13px; color: #1e293b; margin-top: 8px; padding-left: 18px;">
                {''.join([f"<li>{r}</li>" for r in comp.get('key_reasons', [])])}
            </ul>
        </div>
        """)

    with c_r2:
        st.html(f"""
        <div class="fasal-card" style="min-height: 180px;">
            <strong style="color: #475569;">Limitations &amp; Data Caveats:</strong>
            <ul style="font-size: 12px; color: #475569; margin-top: 8px; padding-left: 18px;">
                {''.join([f"<li>{l}</li>" for l in comp.get('limitations', [])])}
            </ul>
        </div>
        """)
