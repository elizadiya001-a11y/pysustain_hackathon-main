"""
views/recommendation_history_view.py
------------------------------------
Recommendation History Screen for FASAL AI.
Securely retrieves previous farm assessments and recommendations from Supabase PostgreSQL.
Provides filtering, details inspection, and historical CSV export.
"""

import streamlit as st
import pandas as pd
from src.supabase_client import fetch_recommendation_history


def render_recommendation_history():
    st.markdown('<div class="fasal-card-title">📜 Recommendation History</div>', unsafe_allow_html=True)
    st.caption("Securely inspect and audit previous farmer assessments, crop decisions, and generated advisory reports.")

    # Fetch from Supabase
    df_history = fetch_recommendation_history(limit=100)

    if df_history.empty:
        st.markdown("""
        <div class="fasal-card" style="border: 1px dashed #cbd5e1; text-align: center; padding: 30px;">
            <div style="font-size: 32px; margin-bottom: 10px;">📋</div>
            <h4 style="color: #1b4332; margin: 0 0 6px 0;">No Cloud Assessments Logged Yet</h4>
            <p style="font-size: 13px; color: #64748b; margin-bottom: 14px;">
                Complete a new assessment in the <strong>Farm Assessment</strong> tab to record your first farm advisory report.
            </p>
        </div>
        """, unsafe_allow_html=True)

        with st.expander("🛠️ Supabase Database Migration Instructions", expanded=False):
            st.markdown("""
            To enable cloud persistence for farmer submissions and recommendation history:
            1. Open your **Supabase Dashboard** at `https://supabase.com/dashboard/project/bwlopgkkaasgmkdkoayb`.
            2. Go to the **SQL Editor**.
            3. Paste and run the reviewed migration from `sql/reviewed_migrations.sql`:
            ```sql
            CREATE TABLE IF NOT EXISTS public.recommendations_history (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                farmer_name VARCHAR(100) NOT NULL,
                farmer_id VARCHAR(50),
                state VARCHAR(50) NOT NULL,
                district VARCHAR(50) NOT NULL,
                village VARCHAR(100),
                area_acres DOUBLE PRECISION NOT NULL,
                current_crop VARCHAR(50) NOT NULL,
                current_yield_q_acre DOUBLE PRECISION,
                soil_type VARCHAR(50),
                soil_ph DOUBLE PRECISION,
                soil_n DOUBLE PRECISION,
                soil_p DOUBLE PRECISION,
                soil_k DOUBLE PRECISION,
                irrigation_type VARCHAR(50),
                rainfall_mm DOUBLE PRECISION,
                budget_inr DOUBLE PRECISION,
                top_recommendation VARCHAR(50) NOT NULL,
                expected_yield_q_acre DOUBLE PRECISION,
                estimated_profit_inr DOUBLE PRECISION,
                yield_delta_pct DOUBLE PRECISION,
                image_storage_path TEXT
            );
            ALTER TABLE public.recommendations_history ENABLE ROW LEVEL SECURITY;
            CREATE POLICY "Allow select on recommendations_history for all users" ON public.recommendations_history FOR SELECT USING (true);
            CREATE POLICY "Allow insert on recommendations_history for all users" ON public.recommendations_history FOR INSERT WITH CHECK (true);
            ```
            """)
        return

    # Filter Bar
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        districts = ["All Districts"] + sorted(list(df_history["district"].dropna().unique()))
        sel_dist = st.selectbox("Filter by District", options=districts)
    with col_f2:
        crops = ["All Crops"] + sorted(list(df_history["current_crop"].dropna().unique()))
        sel_crop = st.selectbox("Filter by Current Crop", options=crops)

    filtered_df = df_history.copy()
    if sel_dist != "All Districts":
        filtered_df = filtered_df[filtered_df["district"] == sel_dist]
    if sel_crop != "All Crops":
        filtered_df = filtered_df[filtered_df["current_crop"] == sel_crop]

    st.markdown(f"Displaying **{len(filtered_df)}** recorded assessment(s):")

    # Table preview
    display_cols = [c for c in ["created_at", "farmer_name", "district", "current_crop", "top_recommendation", "expected_yield_q_acre", "estimated_profit_inr", "yield_delta_pct"] if c in filtered_df.columns]
    st.dataframe(filtered_df[display_cols], use_container_width=True, hide_index=True)

    # Download History CSV
    csv_bytes = filtered_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Download Recommendation History (CSV)",
        data=csv_bytes,
        file_name="Fasal_Recommendation_History.csv",
        mime="text/csv"
    )

