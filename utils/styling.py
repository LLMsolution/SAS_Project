"""
Shared styling for SAS Material Supply Analysis Dashboard
Provides consistent branding across all pages
"""

import streamlit as st
from pathlib import Path
from PIL import Image


def apply_sas_styling():
    """Apply SAS branding CSS and sidebar logo to the current page"""

    # Custom CSS for SAS branding (supports both light and dark mode)
    st.markdown("""
    <style>
        /* SAS Blue primary color */
        .stButton>button {
            background-color: #2B3087;
            color: white;
        }

        /* Headers with SAS brand color - light mode */
        @media (prefers-color-scheme: light) {
            h1, h2, h3 {
                color: #2B3087;
            }
        }

        /* Headers - dark mode: keep readable */
        @media (prefers-color-scheme: dark) {
            h1, h2, h3 {
                color: #5B6BC0;
            }
        }

        /* Sidebar styling */
        [data-testid="stSidebar"][aria-expanded="true"] {
            background-color: #2B3087;
        }

        [data-testid="stSidebar"] {
            background-color: #2B3087;
        }

        /* Sidebar text should be white on dark blue background */
        [data-testid="stSidebar"] * {
            color: white !important;
        }

        /* Sidebar navigation links */
        [data-testid="stSidebar"] a {
            color: white !important;
        }

        [data-testid="stSidebar"] a:hover {
            color: #FFA500 !important;
        }

        /* Sidebar page links */
        [data-testid="stSidebarNav"] a span {
            color: white !important;
        }

        /* Active page in sidebar */
        [data-testid="stSidebarNav"] [aria-selected="true"] span {
            color: #FFA500 !important;
            font-weight: bold;
        }

        /* Metric styling */
        [data-testid="stMetricValue"] {
            color: #2B3087;
            font-weight: bold;
        }

        /* Sidebar input fields - make them readable */
        [data-testid="stSidebar"] input,
        [data-testid="stSidebar"] textarea {
            color: #333333 !important;
            background-color: white !important;
        }

        /* Sidebar selectbox container */
        [data-testid="stSidebar"] [data-baseweb="select"] {
            background-color: white !important;
        }

        [data-testid="stSidebar"] [data-baseweb="select"] span,
        [data-testid="stSidebar"] [data-baseweb="select"] div {
            color: #333333 !important;
        }

        /* Fix dropdown arrow color */
        [data-testid="stSidebar"] [data-baseweb="select"] svg {
            fill: #333333 !important;
        }

        /* Selectbox and multiselect inner elements */
        [data-testid="stSidebar"] .stSelectbox [data-baseweb="select"] > div,
        [data-testid="stSidebar"] .stMultiSelect [data-baseweb="select"] > div {
            background-color: white !important;
            border-color: #cccccc !important;
        }
    </style>
    """, unsafe_allow_html=True)
