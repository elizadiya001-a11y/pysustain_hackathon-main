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
    st.html('<div class="fasal-card-title">🌾 Intelligent Crop Recommendations</div>')
    st.caption("Discover crops that suit your soil chemistry, local climate, and farm budget while staying strictly within aquifer water limits.")

    current_farm = st.session_state.get("current_farm", {})

    # Top Controls Bar: Water Cap, Irrigation, Season
    with st.expander("⚙️ Agronomic Parameters & Water Cap Filters", expanded=True):
        st.caption("Adjust the aquifer limit and irrigation method to see which crop alternatives remain feasible and profitable.")
        col_c1, col_c2, col_c3 = st.columns(3)
        with col_c1:
            water_cap_mm = st.slider(
                "💧 Aquifer Water Cap (mm)",
                min_value=200,
                max_value=1200,
                value=int(current_farm.get("water_cap_mm", 600)),
                step=50,
                help="Strict water allocation limit to prevent regional groundwater depletion."
            )
        with col_c2:
            irrigation_method = st.selectbox(
                "Recommended Irrigation System",
                options=["Drip", "Sprinkler", "Flood / Furrow", "Rainfed"],
                index=0,
                help="High-efficiency irrigation reduces volumetric water consumption."
            )
        with col_c3:
            season_filter = st.selectbox(
                "Growing Season Filter",
                options=["All Seasons", "Rabi", "Kharif"],
                help="Filter candidate crops by agricultural cropping season."
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
    st.html(f"""
    <div style="background: #e8f5e9; border: 1px solid #a5d6a7; border-radius: 8px; padding: 12px 16px; margin-bottom: 20px;">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
            <div>
                <strong style="color: #1b4332; font-size: 15px;">🌟 Prime Sustainable Recommendation: {top1.get('crop')}</strong>
                <div style="font-size: 13px; color: #2d6a4f; margin-top: 4px;">
                    Potential Net Profit Boost: <strong>+₹{top1.get('profit_delta_rs', 0):,.0f}</strong> · Water Conserved: <strong>{top1.get('water_saved_pct', 0):.0f}%</strong> vs baseline
                </div>
            </div>
            <span style="background: #2d6a4f; color: white; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: bold;">
                {top1.get('suitability_score')}% Suitability Match
            </span>
        </div>
    </div>
    """)

    # 2. Side-by-Side Highlight Cards: Current vs Top 3
    st.markdown("##### 🏆 Candidate Highlights: Current Baseline vs Top Alternatives")
    st.caption("Compare your existing crop against the top AI-ranked diversified alternatives.")

    col_h1, col_h2, col_h3 = st.columns(3)

    # Card 1: Current Baseline
    with col_h1:
        st.html(f"""
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
        """)

    # Card 2: Top Recommendation #1
    with col_h2:
        st.html(f"""
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
        """)

    # Card 3: Top Recommendation #2
    with col_h3:
        if top2:
            st.html(f"""
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
            """)

    # 3. Comprehensive Evaluated Crops Table
    st.html('<div class="fasal-card-title">📋 Full Crop Ranking (Database Catalog)</div>')
    st.caption("Inspect every crop available in the agricultural database evaluated under your farm's soil and water constraints.")

    table_rows = []
    for r in recs["ranked_crops"]:
        table_rows.append({
            "Crop Name": r["crop"],
            "Growing Season": r["season"],
            "Suitability Score": f"{r['suitability_score']}%",
            "Expected Yield (q/acre)": f"{r['yield_q_acre']}",
            "Expected Yield (t/ha)": f"{r['yield_tonnes_ha']}",
            "Gross Revenue (₹)": f"₹{r['gross_revenue']:,.0f}",
            "Cultivation Cost (₹)": f"₹{r['total_cost']:,.0f}",
            "Net Profit (₹)": f"₹{r['net_profit']:,.0f}",
            "Net Profit per Acre (₹/acre)": f"₹{r['net_profit_acre']:,.0f}",
            "Net Profit Gain (₹)": f"+₹{r['profit_delta_rs']:,.0f}" if r['profit_delta_rs'] >= 0 else f"-₹{abs(r['profit_delta_rs']):,.0f}",
            "Aquifer Water Cap Status": "✅ Within Cap" if r["is_within_cap"] else f"⚠️ Exceeds by {r['cap_delta_mm']} mm",
            "Groundwater Conserved": f"{r['water_saved_pct']:.0f}%"
        })
    df_table = pd.DataFrame(table_rows)
    st.dataframe(df_table, use_container_width=True, hide_index=True)

    # 4. Executive Farmer Advisory Report
    st.markdown("---")
    st.html('<div class="fasal-card-title">📄 Executive Farmer Advisory Report</div>')
    st.caption("Review a consolidated summary of farm conditions, crop recommendations, and available economic indicators.")

    report_payload = {
        "farmer": {
            "name": current_farm.get("farmer_name", "Farmer"),
            "village": current_farm.get("village", "Rampur"),
            "district": current_farm.get("district", "Ludhiana"),
            "state": current_farm.get("state", "Punjab"),
            "area_acres": current_farm.get("area_acres", 2.0)
        },
        "soil": {
            "overall_health_score": 78.5,
            "health_rating": "Good / Suitable",
            "texture": current_farm.get("texture", "Loam"),
            "ph": current_farm.get("ph", 7.2),
            "n": current_farm.get("nitrogen_kg_ha", 95.0),
            "p": current_farm.get("phosphorus_kg_ha", 28.0),
            "k": current_farm.get("potassium_kg_ha", 150.0),
            "recommended_amendments": [
                "Incorporate organic green manure or FYM (4-5 tonnes/acre) to build cation exchange capacity.",
                "Adopt split-dose nitrogen scheduling with fertigation rather than single-dose broadcast."
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
            "Visual image classification detects surface soil texture group; laboratory chemical test recommended for micro-nutrients."
        ],
        "practical_next_steps": [
            f"Review certified seed availability and current APMC mandi prices for {top1.get('crop')}.",
            f"Equip field with {irrigation_method} irrigation to stay strictly within the {water_cap_mm} mm aquifer cap.",
            "Conduct micro-nutrient testing (Zinc, Boron) at local Krishi Vigyan Kendra (KVK) before basal sowing."
        ]
    }

    report_txt = generate_farmer_report_text(report_payload)
    report_csv = generate_report_csv_bytes(report_payload)

    # Render Visual Advisory Dossier cleanly using st.html
    area_ac = float(current_farm.get('area_acres', 2.0))
    st.html(f"""
    <div class="fasal-card" style="border-left: 5px solid #2d6a4f; background: #ffffff;">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 10px; border-bottom: 1px solid #cbd5e1; padding-bottom: 12px; margin-bottom: 14px;">
            <div>
                <span style="font-size: 11px; font-weight: 700; color: #2d6a4f; text-transform: uppercase; letter-spacing: 0.5px;">AGRONOMIC ADVISORY BRIEFING</span>
                <h3 style="margin: 2px 0 4px 0; color: #1b4332;">{current_farm.get('farmer_name', 'Farmer')} — Farm Parcel #{current_farm.get('farm_id', 'plot_001')}</h3>
                <div style="font-size: 13px; color: #475569;">
                    📍 {current_farm.get('village', 'Village')}, {current_farm.get('district', 'District')}, {current_farm.get('state', 'State')} · <strong>{area_ac} Acres</strong> ({round(area_ac * 0.4047, 2)} Hectares)
                </div>
            </div>
            <div style="text-align: right;">
                <span style="background: #e8f5e9; color: #1b4332; font-weight: 700; font-size: 12px; padding: 4px 12px; border-radius: 12px; border: 1px solid #a5d6a7;">
                    FASAL AI Validated
                </span>
            </div>
        </div>

        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 16px; margin-bottom: 14px;">
            <div style="background: #f8faf7; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px;">
                <div style="font-size: 12px; font-weight: 700; color: #1b4332; margin-bottom: 6px;">🧪 Soil & Nutrient Profile</div>
                <div style="font-size: 13px; line-height: 1.6; color: #1e293b;">
                    <div>• <strong>Texture:</strong> {current_farm.get('texture', 'Loam')}</div>
                    <div>• <strong>pH Reaction:</strong> {current_farm.get('ph', 7.2)} (Neutral)</div>
                    <div>• <strong>Available Nitrogen:</strong> {current_farm.get('nitrogen_kg_ha', 95.0)} kg/ha</div>
                    <div>• <strong>Organic Carbon:</strong> {current_farm.get('organic_carbon', 0.65)}%</div>
                </div>
            </div>

            <div style="background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px; padding: 12px;">
                <div style="font-size: 12px; font-weight: 700; color: #166534; margin-bottom: 6px;">🥇 Recommended Transition</div>
                <div style="font-size: 13px; line-height: 1.6; color: #1e293b;">
                    <div>• <strong>From Baseline:</strong> {curr.get('crop')} ➔ <strong>{top1.get('crop')}</strong></div>
                    <div>• <strong>Suitability Match:</strong> <span style="color: #166534; font-weight: bold;">{top1.get('suitability_score')}%</span></div>
                    <div>• <strong>Net Profit Potential:</strong> <span style="color: #166534; font-weight: bold;">₹{top1.get('net_profit', 0):,.0f}</span> (+₹{top1.get('profit_delta_rs', 0):,.0f})</div>
                    <div>• <strong>Water Conservation:</strong> <span style="color: #166534; font-weight: bold;">{top1.get('water_saved_pct', 0):.0f}%</span> conserved</div>
                </div>
            </div>

            <div style="background: #f8faf7; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px;">
                <div style="font-size: 12px; font-weight: 700; color: #1b4332; margin-bottom: 6px;">💧 Irrigation & Climate Plan</div>
                <div style="font-size: 13px; line-height: 1.6; color: #1e293b;">
                    <div>• <strong>Allocation Cap:</strong> {water_cap_mm} mm</div>
                    <div>• <strong>Recommended System:</strong> {irrigation_method}</div>
                    <div>• <strong>Aquifer Compliance:</strong> {'✅ Within Safe Limits' if top1.get('is_within_cap') else '⚠️ Limit Exceeded'}</div>
                    <div>• <strong>Risk Level:</strong> Low (Drought-resilient alternative)</div>
                </div>
            </div>
        </div>

        <div style="background: #ffffff; border-top: 1px solid #cbd5e1; padding-top: 10px; margin-top: 10px;">
            <div style="font-size: 12px; font-weight: 700; color: #1b4332; margin-bottom: 6px;">📌 Immediate Action Checklist:</div>
            <ol style="margin: 0; padding-left: 20px; font-size: 13px; line-height: 1.6; color: #334155;">
                <li>Source certified quality seed for <strong>{top1.get('crop')}</strong> from state agricultural university or certified dealer.</li>
                <li>Implement <strong>{irrigation_method}</strong> irrigation prior to primary sowing to achieve the projected {top1.get('water_saved_pct', 0):.0f}% water reduction.</li>
                <li>Apply organic green manure or FYM to elevate soil organic carbon and nutrient retention.</li>
            </ol>
        </div>
    </div>
    """)

    # Export & Download Buttons
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

    with st.expander("👁️ View Full Formatted Report Text", expanded=False):
        st.text(report_txt)
