"""
Utility functions for Plotly charts to suppress deprecation warnings
"""

import streamlit as st


def hide_warnings_css():
    """
    Add CSS to hide all Streamlit alert/warning boxes
    Call this once at the start of each page
    """
    st.markdown("""
    <style>
        /* Hide all Plotly/Streamlit deprecation warnings */
        div[data-testid="stAlert"] {
            display: none !important;
        }
        div[role="alert"] {
            display: none !important;
        }
    </style>
    """, unsafe_allow_html=True)
