"""
src/navigation.py
-----------------
Centralized navigation state manager for FASAL AI Streamlit application.
Avoids StreamlitWidgetAlreadyInstantiatedError by staging page changes
in 'pending_navigation' and resolving them before widget instantiation.
"""

import streamlit as st

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


def navigate_to(page_name: str) -> None:
    """
    Safely schedules a navigation change to be applied at the start of the next rerun.
    Never modifies 'nav_radio' directly while the widget is already instantiated.
    """
    if page_name in PAGES:
        st.session_state["pending_navigation"] = page_name
        st.rerun()


def initialize_navigation() -> str:
    """
    Resolves any pending navigation request BEFORE the navigation radio widget is rendered.
    Ensures safe, bidirectional state synchronization.
    Returns the active page name.
    """
    if "current_tab" not in st.session_state:
        st.session_state["current_tab"] = PAGES[0]

    # Apply pending navigation if requested
    if "pending_navigation" in st.session_state and st.session_state["pending_navigation"] in PAGES:
        target = st.session_state.pop("pending_navigation")
        st.session_state["nav_radio"] = target
        st.session_state["current_tab"] = target
    elif "nav_radio" not in st.session_state or st.session_state["nav_radio"] not in PAGES:
        st.session_state["nav_radio"] = st.session_state["current_tab"]

    return st.session_state["current_tab"]

