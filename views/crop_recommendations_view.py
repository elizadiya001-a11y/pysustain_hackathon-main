"""
views/crop_recommendations_view.py
----------------------------------
Crop Recommendations Screen for FASAL AI.
Displays ranked crop alternatives, enforces water cap feasibility,
distinguishes Yield vs Profit vs Suitability, and generates downloadable reports.
"""

import streamlit as st
import pandas as pd
from src.crop_recommendation import generate_crop_recommendations
from src.reporting import generate_farmer_report_text, generate_report_csv_bytes


def render_crop_recommendations():
    st.markdown('<div class="fasal-card-title">🌾 Intelligent Crop Recommendations</div>', unsafe_allow_html=True)
    st.caption("AI-ranked crop alternatives evaluated under local soil conditions, groundwater limits, and market economics.")

    current_farm = st.session_state.get("current_farm", {})

    # Top Controls Bar: Water Cap, Irrigation, Season
    col_c1, col_c2, col_c3 = st.columns(3)
    with col_c1:
        water_cap_mm = st.slider(
            "💧 Aquifer Water Cap (mm)",
            min_value=200,
            max_value=1200,
            value=int(current_farm.get("water_cap_mm", 600)),
            step=50,
            help="Strict water allocation limit to prevent aquifer depletion."
        )
    with col_c2:
        irrigation_method = st.selectbox(
            "Recommended Irrigation System",
            options=["Drip", "Sprinkler", "Flood / Furrow", "Rainfed"],
            index=0
        )
    with col_c3:
        season_filter = st.selectbox(
            "Season Filter",
            options=["All Seasons", "Rabi", "Kharif"]
        )

    # Compute Recommendations
    recs = generate_crop_recommendations(
        farm_state=current_farm,
        water_cap_mm=float(water_cap_mm),
        preferred_irrigation=irrigation_method,
        season_filter=season_filter if season_filter != "All Seasons" else None
    )

    curr = recs["current_crop"]
    top1 = recs["top_recommendation_1"]
    top2 = recs["top_recommendation_2"]
    top3 = recs["top_recommendation_3"]

    # 1. Executive Summary Pill
    st.markdown(f"""
    <div style="background: #e8f5e9; border: 1px solid #a5d6a7; border-radius: 8px; padding: 12px 16px; margin-bottom: 20px;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <strong style="color: #1b4332; font-size: 15px;">🌟 Prime Sustainable Recommendation: {top1.get('crop')}</strong>
                <div style="font-size: 13px; color: #2d6a4f; margin-top: 4px;">
                    Potential Net Profit Boost: <strong>+₹{top1.get('profit_delta_rs', 0):,.0f}</strong> · Water Conserved: <strong>{top1.get('water_saved_pct', 0):.0f}%</strong> vs baseline
                </div>
            </div>
            <span style="background: #2d6a4f; color: white; padding: 4px 10px; border-radius: 12px; font-size: 12px; font-weight: bold;">
                {top1.get('suitability_score')}% Suitability
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 2. Side-by-Side Highlight Cards: Current vs Top 3
    col_h1, col_h2, col_h3 = st.columns(3)

    # Card 1: Current Baseline
    with col_h1:
        st.markdown(f"""
        <div class="fasal-card" style="border-top: 4px solid #64748b; height: 320px; display: flex; flex-direction: column; justify-content: space-between;">
            <div>
                <span style="font-size: 11px; font-weight: 700; color: #64748b;">CURRENT BASELINE</span>
                <h3 style="margin: 4px 0; color: #1e293b;">{curr.get('crop')}</h3>
                <span style="font-size: 11px; background: #e2e8f0; padding: 2px 6px; border-radius: 4px; color: #475569;">
                    {curr.get('season')} · {curr.get('category')}
                </span>
                <div style="margin-top: 12px; font-size: 13px; line-height: 1.6;">
                    <div>🌾 <strong>Yield:</strong> {curr.get('yield_q_acre')} q/ac ({curr.get('yield_tonnes_ha')} t/ha)</div>
                    <div>💰 <strong>Net Profit:</strong> ₹{curr.get('net_profit'):,.0f}</div>
                    <div>🏷️ <strong>Margin/Acre:</strong> ₹{curr.get('net_profit_acre'):,.0f}</div>
                    <div>💧 <strong>Water Used:</strong> {curr.get('water_liters'):,.0f} L</div>
                </div>
            </div>
            <div>
                <span style="font-size: 11px; font-weight: bold; color: {'#2d6a4f' if curr.get('is_within_cap') else '#d90429'};">
                    {'✅ Within Water Cap' if curr.get('is_within_cap') else '⚠️ Exceeds Water Cap'}
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Card 2: Top Recommendation #1
    with col_h2:
        st.markdown(f"""
        <div class="fasal-card" style="border-top: 4px solid #2d6a4f; height: 320px; display: flex; flex-direction: column; justify-content: space-between; background: #f0fdf4;">
            <div>
                <div style="display: flex; justify-content: space-between;">
                    <span style="font-size: 11px; font-weight: 700; color: #2d6a4f;">🥇 TOP RECOMMENDATION</span>
                    <span style="font-size: 11px; font-weight: 700; color: #2d6a4f;">{top1.get('suitability_score')}% Match</span>
                </div>
                <h3 style="margin: 4px 0; color: #1b4332;">{top1.get('crop')}</h3>
                <span style="font-size: 11px; background: #dcfce7; padding: 2px 6px; border-radius: 4px; color: #166534;">
                    {top1.get('season')} · {top1.get('category')}
                </span>
                <div style="margin-top: 12px; font-size: 13px; line-height: 1.6;">
                    <div>🌾 <strong>Yield:</strong> {top1.get('yield_q_acre')} q/ac ({top1.get('yield_tonnes_ha')} t/ha)</div>
                    <div>💰 <strong>Net Profit:</strong> <span style="color: #1b4332; font-weight: bold;">₹{top1.get('net_profit'):,.0f}</span></div>
                    <div>📈 <strong>Profit Delta:</strong> <span style="color: #2d6a4f; font-weight: bold;">+₹{top1.get('profit_delta_rs'):,.0f}</span></div>
                    <div>💧 <strong>Water Conserved:</strong> <span style="color: #2d6a4f; font-weight: bold;">{top1.get('water_saved_pct'):.0f}%</span></div>
                </div>
            </div>
            <div>
                <span style="font-size: 11px; font-weight: bold; color: {'#2d6a4f' if top1.get('is_within_cap') else '#d90429'};">
                    {'✅ Within Water Cap' if top1.get('is_within_cap') else '⚠️ Exceeds Water Cap'}
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Card 3: Top Recommendation #2
    with col_h3:
        if top2:
            st.markdown(f"""
            <div class="fasal-card" style="border-top: 4px solid #40916c; height: 320px; display: flex; flex-direction: column; justify-content: space-between;">
                <div>
                    <div style="display: flex; justify-content: space-between;">
                        <span style="font-size: 11px; font-weight: 700; color: #40916c;">🥈 ALTERNATIVE #2</span>
                        <span style="font-size: 11px; font-weight: 700; color: #40916c;">{top2.get('suitability_score')}% Match</span>
                    </div>
                    <h3 style="margin: 4px 0; color: #1b4332;">{top2.get('crop')}</h3>
                    <span style="font-size: 11px; background: #e2e8f0; padding: 2px 6px; border-radius: 4px; color: #475569;">
                        {top2.get('season')} · {top2.get('category')}
                    </span>
                    <div style="margin-top: 12px; font-size: 13px; line-height: 1.6;">
                        <div>🌾 <strong>Yield:</strong> {top2.get('yield_q_acre')} q/ac ({top2.get('yield_tonnes_ha')} t/ha)</div>
                        <div>💰 <strong>Net Profit:</strong> ₹{top2.get('net_profit'):,.0f}</div>
                        <div>📈 <strong>Profit Delta:</strong> +₹{top2.get('profit_delta_rs'):,.0f}</div>
                        <div>💧 <strong>Water Conserved:</strong> {top2.get('water_saved_pct'):.0f}%</div>
                    </div>
                </div>
                <div>
                    <span style="font-size: 11px; font-weight: bold; color: {'#2d6a4f' if top2.get('is_within_cap') else '#d90429'};">
                        {'✅ Within Water Cap' if top2.get('is_within_cap') else '⚠️ Exceeds Water Cap'}
                    </span>
                </div>
            </div>
            """, unsafe_allow_html=True)

    # 3. Comprehensive Evaluated Crops Table
    st.markdown('<div class="fasal-card-title">📋 Full Crop Ranking (Database Catalog)</div>', unsafe_allow_html=True)
    table_rows = []
    for r in recs["ranked_crops"]:
        table_rows.append({
            "Crop": r["crop"],
            "Season": r["season"],
            "Suitability": f"{r['suitability_score']}%",
            "Yield (q/ac)": f"{r['yield_q_acre']}",
            "Gross Revenue (₹)": f"₹{r['gross_revenue']:,.0f}",
            "Total Cost (₹)": f"₹{r['total_cost']:,.0f}",
            "Net Profit (₹)": f"₹{r['net_profit']:,.0f}",
            "Net Profit/Ac (₹)": f"₹{r['net_profit_acre']:,.0f}",
            "Profit Delta (₹)": f"+₹{r['profit_delta_rs']:,.0f}" if r['profit_delta_rs'] >= 0 else f"-₹{abs(r['profit_delta_rs']):,.0f}",
            "Water Cap Status": "✅ Pass" if r["is_within_cap"] else f"⚠️ +{r['cap_delta_mm']} mm",
            "Water Saved": f"{r['water_saved_pct']:.0f}%"
        })
    df_table = pd.DataFrame(table_rows)
    st.dataframe(df_table, use_container_width=True, hide_index=True)

    # 4. Report Download Section
    st.markdown("---")
    st.markdown('<div class="fasal-card-title">📄 Executive Farmer Advisory Report</div>', unsafe_allow_html=True)

    report_payload = {
        "farmer": {
            "name": current_farm.get("farmer_name", "Farmer"),
            "village": current_farm.get("village", "Rampur"),
            "district": current_farm.get("district", "Ludhiana"),
            "state": current_farm.get("state", "Punjab"),
            "area_acres": current_farm.get("area_acres", 2.0)
        },
        "soil": {
            "overall_health_score": 75.0,
            "health_rating": "Moderate",
            "texture": current_farm.get("texture", "Loam"),
            "ph": current_farm.get("ph", 7.2),
            "n": current_farm.get("nitrogen_kg_ha", 95.0),
            "p": current_farm.get("phosphorus_kg_ha", 28.0),
            "k": current_farm.get("potassium_kg_ha", 150.0),
            "recommended_amendments": [
                "Maintain organic matter additions via farmyard manure (FYM).",
                "Ensure balanced nitrogen application according to crop canopy requirements."
            ]
        },
        "current_crop": curr,
        "top_alternatives": [top1, top2] + ([top3] if top3 else []),
        "water_and_climate": {
            "water_cap_mm": water_cap_mm,
            "recommended_irrigation": irrigation_method,
            "weather_scenario": "Normal"
        },
        "missing_info_and_uncertainty": [
            "Yield estimate is calibrated to regional agronomic potential with an 80% prediction interval.",
            "Visual image classification detects surface soil texture group, not chemical NPK."
        ],
        "practical_next_steps": [
            f"Review seed availability and local mandi prices for {top1.get('crop')}.",
            f"Adopt {irrigation_method} irrigation to maximize water efficiency and lower pumping electricity costs.",
            "Conduct an accredited soil lab test prior to next basal fertilizer application."
        ]
    }

    report_txt = generate_farmer_report_text(report_payload)
    report_csv = generate_report_csv_bytes(report_payload)

    with st.expander("👁️ View Formatted Advisory Report Preview", expanded=False):
        st.text(report_txt)

    col_dl1, col_dl2 = st.columns(2)
    with col_dl1:
        st.download_button(
            label="📥 Download Advisory Report (Text / Markdown)",
            data=report_txt,
            file_name=f"Fasal_Advisory_Report_{current_farm.get('farmer_name', 'farmer')}.txt",
            mime="text/plain",
            use_container_width=True
        )
    with col_dl2:
        st.download_button(
            label="📊 Download Recommendations Data (CSV)",
            data=report_csv,
            file_name=f"Fasal_Recommendations_{current_farm.get('farmer_name', 'farmer')}.csv",
            mime="text/csv",
            use_container_width=True
        )

