"""
views/soil_analysis_view.py
---------------------------
Soil Analysis Screen for FASAL AI.
Displays chemical nutrient levels, ICAR benchmarks, visual photo classification,
and hand ribbon test guides.
"""

import os
from pathlib import Path
import streamlit as st
import plotly.graph_objects as go
from src.soil_analysis import comprehensive_soil_health_assessment
from src.image_analysis import analyze_soil_image
from src.data_loader import fetch_table


def render_soil_analysis():
    st.markdown('<div class="fasal-card-title">🧪 Comprehensive Soil Analysis</div>', unsafe_allow_html=True)
    st.caption("Inspect chemical nutrient bioavailability, visual soil attributes, and physical texture guidelines.")

    current_farm = st.session_state.get("current_farm", {})
    soil_assessment = comprehensive_soil_health_assessment(current_farm)

    # 1. Overall Soil Health Banner
    score = soil_assessment["overall_health_score"]
    rating = soil_assessment["health_rating"]
    score_color = "#2d6a4f" if score >= 80 else ("#f77f00" if score >= 60 else "#d90429")

    st.markdown(f"""
    <div class="fasal-card" style="border-left: 6px solid {score_color};">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <span style="font-size: 13px; color: #64748b; font-weight: 600;">COMPOSITE SOIL HEALTH SCORE</span>
                <h2 style="margin: 4px 0 0 0; color: {score_color}; font-size: 28px;">
                    {score} / 100 · {rating}
                </h2>
                <div style="font-size: 12px; color: #475569; margin-top: 4px;">
                    Evaluated for <strong>{current_farm.get('farmer_name', 'Active Farm')}</strong> ({current_farm.get('district', 'District')}, {current_farm.get('state', 'State')})
                </div>
            </div>
            <div style="text-align: right;">
                <span style="background: #e2e8f0; font-size: 12px; padding: 4px 8px; border-radius: 6px; font-weight: bold;">
                    Texture: {current_farm.get('texture', 'Loam')}
                </span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 2. Nutrient Cards Grid (ICAR Standards)
    st.markdown("##### 🌾 Chemical Nutrient Parameters (ICAR Standard)")
    params = soil_assessment["parameters"]

    cols = st.columns(len(params))
    for i, (param_name, p_data) in enumerate(params.items()):
        with cols[i]:
            val_display = f"{p_data['value']}"
            st.markdown(f"""
            <div class="fasal-card" style="padding: 10px; text-align: center; height: 140px; display: flex; flex-direction: column; justify-content: space-between;">
                <div style="font-size: 11px; font-weight: 700; color: #64748b;">{param_name}</div>
                <div style="font-size: 18px; font-weight: 800; color: #1e293b; margin: 4px 0;">{val_display}</div>
                <div>
                    <span style="background: {p_data['color']}22; color: {p_data['color']}; font-size: 11px; font-weight: 700; padding: 3px 6px; border-radius: 8px;">
                        {p_data['status']}
                    </span>
                </div>
            </div>
            """, unsafe_allow_html=True)

    # 3. Actionable Amendments Plan
    if soil_assessment["recommended_amendments"]:
        st.markdown("##### 🛠️ Agronomic Soil Amendment Recommendations")
        for rec in soil_assessment["recommended_amendments"]:
            st.markdown(f"""
            <div style="background: #f1f5f9; border-left: 4px solid #2d6a4f; padding: 8px 12px; border-radius: 4px; margin-bottom: 8px; font-size: 13px; color: #1e293b;">
                👉 {rec}
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")

    # 4. Visual Soil Classifier & Photo Upload
    st.markdown("##### 📸 Visual Soil Photo Classification (MobileNetV3)")
    st.caption("Upload a soil sample photo to estimate physical group and surface texture.")

    col_v1, col_v2 = st.columns([1, 1])
    with col_v1:
        # Pre-loaded reference image buttons
        st.write("Or test with reference soil samples:")
        sample_cols = st.columns(5)
        selected_sample_path = None
        for s_idx, s_name in enumerate(["alluvial", "black", "clay", "laterite", "red"]):
            s_file = Path(f"soil_images/{s_name}.jpg")
            if s_file.exists():
                with sample_cols[s_idx]:
                    if st.button(s_name.capitalize(), key=f"s_btn_{s_name}"):
                        selected_sample_path = str(s_file)

        v_file = st.file_uploader("Upload Soil Photograph (.jpg, .png)", type=["jpg", "jpeg", "png"], key="soil_analysis_uploader")
        test_path = v_file if v_file else selected_sample_path

        if test_path:
            with st.spinner("Processing visual features..."):
                if isinstance(test_path, str):
                    st.image(test_path, caption=f"Selected: {os.path.basename(test_path)}", width=240)
                    result = analyze_soil_image(test_path)
                else:
                    bytes_data = test_path.read()
                    st.image(bytes_data, caption=f"Uploaded: {test_path.name}", width=240)
                    result = analyze_soil_image(bytes_data)

                if result.get("success"):
                    st.session_state["last_soil_img_result"] = result
                else:
                    st.error(result.get("error"))

    with col_v2:
        last_res = st.session_state.get("last_soil_img_result")
        if last_res:
            st.markdown(f"""
            <div class="fasal-card">
                <div style="font-size: 12px; color: #64748b; font-weight: 700;">PREDICTED SOIL CLASS</div>
                <h3 style="margin: 4px 0; color: #1b4332;">{last_res['predicted_soil_group']}</h3>
                <div style="color: #2d6a4f; font-weight: 700; font-size: 14px; margin-bottom: 8px;">
                    Model Confidence: {last_res['confidence_pct']}%
                </div>
                <div style="font-size: 12px; color: #475569; line-height: 1.5;">
                    <div>💧 <strong>Estimated Drainage:</strong> {last_res['visual_features']['estimated_drainage']}</div>
                    <div>🚜 <strong>Field Workability:</strong> {last_res['visual_features']['physical_workability']}</div>
                    <div>🧱 <strong>Typical Texture:</strong> {last_res['visual_features']['typical_texture']}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Bar chart of probabilities
            probs = last_res["class_probabilities"]
            fig = go.Figure(go.Bar(
                x=[p[1] for p in probs],
                y=[p[0] for p in probs],
                orientation="h",
                marker=dict(color="#40916c")
            ))
            fig.update_layout(
                height=180,
                margin=dict(l=10, r=10, t=10, b=10),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(title="Probability (%)", showgrid=True, gridcolor="#e2e8f0"),
                yaxis=dict(autorange="reversed")
            )
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

            st.warning(f"⚠️ {last_res['disclaimer']}")
        else:
            st.info("Upload or select a soil photo above to view visual texture and class distribution.")

    st.markdown("---")

    # 5. Hand Ribbon Soil Texture Testing Guide (From Supabase soil_types table)
    st.markdown("##### 🖐️ Field Hand Ribbon Soil Testing Guide")
    st.caption("Perform this traditional zero-cost field test: moisten a walnut-sized soil ball and squeeze between thumb and forefinger to form a ribbon.")

    soil_types_df, ok = fetch_table("soil_types")
    if ok and not soil_types_df.empty:
        guide_cols = st.columns(min(len(soil_types_df), 4))
        for g_idx, (_, r) in enumerate(soil_types_df.iterrows()):
            with guide_cols[g_idx % 4]:
                st.markdown(f"""
                <div class="fasal-card" style="font-size: 12px; height: 180px;">
                    <strong style="color: #1b4332; font-size: 14px;">{r['soil_type']}</strong>
                    <div style="color: #64748b; margin: 4px 0 6px 0; font-size: 11px;">{r.get('description', '')[:70]}...</div>
                    <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 4px; padding: 6px; font-size: 11px;">
                        <strong>Hand Test:</strong> {r.get('hand_test', '')}
                    </div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.caption("Hand ribbon test reference cards loaded from core agronomy catalog.")

