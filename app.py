"""
FASAL AI — Intelligent Crop Recommendation & Farm Digital Twin.
Enterprise Agricultural Intelligence & Farm Digital Twin Platform.
"""

import os
import streamlit as st

# Configure Streamlit page layout
st.set_page_config(
    page_title="FASAL AI — Intelligent Crop Recommendation & Digital Twin",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load Mobile-First & Desktop CSS Stylesheet
css_path = os.path.join(os.path.dirname(__file__), "static", "style.css")
if os.path.exists(css_path):
    with open(css_path, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Imports from data loaders, core and views
from src.data_loader import get_unified_agricultural_dataset, get_farm_record_by_id
from src.supabase_client import check_connection_health

from views.home_dashboard import render_home_dashboard
from views.farm_assessment import render_farm_assessment
from views.soil_analysis_view import render_soil_analysis
from views.crop_recommendations_view import render_crop_recommendations
from views.current_crop_comparison_view import render_current_crop_comparison
from views.digital_twin_view import render_digital_twin
from views.dataset_explorer_view import render_dataset_explorer
from views.model_performance_view import render_model_performance
from views.recommendation_history_view import render_recommendation_history

# Initialize Session State
if "current_farm" not in st.session_state:
    unified_df, _, _ = get_unified_agricultural_dataset()
    default_record = unified_df.iloc[0].to_dict() if not unified_df.empty else {}
    st.session_state["current_farm"] = default_record

if "current_tab" not in st.session_state:
    st.session_state["current_tab"] = "Home Dashboard"

if "nav_radio" not in st.session_state:
    st.session_state["nav_radio"] = st.session_state["current_tab"]

current_farm = st.session_state["current_farm"]

# Render Consistent FASAL Header
st.markdown(f"""
<div class="fasal-header">
    <div class="fasal-brand">
        <div class="fasal-icon">🌾</div>
        <div>
            <h1 class="fasal-title">FASAL AI</h1>
            <p class="fasal-tagline">Intelligent Crop Recommendation &amp; Farm Digital Twin</p>
        </div>
    </div>
    <div class="fasal-badge">
        {current_farm.get('farm_id', 'plot_001')} • {current_farm.get('area_acres', 2.0)} ac ({current_farm.get('district', 'District')})
    </div>
</div>
""", unsafe_allow_html=True)

# 9 Core Pages Definition
PAGES = [
    "Home Dashboard",
    "Farm Assessment",
    "Soil Analysis",
    "Crop Recommendations",
    "Current Crop Comparison",
    "Farm Digital Twin",
    "Dataset Explorer",
    "Model Performance",
    "Recommendation History"
]

# Navigation Synchronizer
def sync_nav():
    st.session_state["current_tab"] = st.session_state["nav_radio"]

# Primary Navigation Bar (Pill selector)
# Ensure nav_radio is valid
if st.session_state.get("nav_radio") not in PAGES:
    st.session_state["nav_radio"] = PAGES[0]

selected_page = st.radio(
    "Navigation",
    options=PAGES,
    key="nav_radio",
    horizontal=True,
    label_visibility="collapsed",
    on_change=sync_nav
)

st.session_state["current_tab"] = st.session_state["nav_radio"]
current_tab = st.session_state["current_tab"]

# Render the Selected View
if current_tab == "Home Dashboard":
    render_home_dashboard()
elif current_tab == "Farm Assessment":
    render_farm_assessment()
elif current_tab == "Soil Analysis":
    render_soil_analysis()
elif current_tab == "Crop Recommendations":
    render_crop_recommendations()
elif current_tab == "Current Crop Comparison":
    render_current_crop_comparison()
elif current_tab == "Farm Digital Twin":
    render_digital_twin()
elif current_tab == "Dataset Explorer":
    render_dataset_explorer()
elif current_tab == "Model Performance":
    render_model_performance()
elif current_tab == "Recommendation History":
    render_recommendation_history()

# Sidebar: Quick Info, Cloud Twin Status & Remote Access
with st.sidebar:
    st.markdown("### 🌾 FASAL AI Control")
    st.caption("Intelligent Crop Recommendation & Farm Digital Twin")

    # Cloud Connectivity Status
    health = check_connection_health()
    if health.get("connected"):
        st.success(f"🟢 Cloud Connected (`bwlopgkkaasgmkdkoayb`)")
    else:
        st.warning("🟠 Local High-Fidelity Twin Active")

    st.markdown(f"""
    **Active Farm:** `{current_farm.get('farm_id')}`  
    **Farmer:** {current_farm.get('farmer_name', 'Farmer')}  
    **District:** {current_farm.get('district')}, {current_farm.get('state')}  
    **Landholding:** {current_farm.get('area_acres')} Acres  
    **Current Crop:** {current_farm.get('current_crop')}  
    **Soil pH:** {current_farm.get('ph')}  
    **Soil Texture:** {current_farm.get('texture')}  
    """)

    st.divider()
    st.markdown("##### 📱 Field Device & Mobile Access")
    st.caption("To open on mobile devices or tablets over local Wi-Fi, run:")
    st.code("python -m streamlit run app.py --server.address 0.0.0.0", language="bash")
    st.divider()
    st.caption("FASAL AI Enterprise Edition · v2.4 Production")
