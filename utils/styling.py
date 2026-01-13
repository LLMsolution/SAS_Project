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

        /* Sidebar radio buttons - reduce spacing */
        [data-testid="stSidebar"] .stRadio [role="radiogroup"] {
            gap: 0 !important;
        }

        [data-testid="stSidebar"] .stRadio [role="radiogroup"] label {
            background-color: transparent !important;
            padding: 0.15rem 0 !important;
            margin: 0 !important;
        }

        [data-testid="stSidebar"] .stRadio [role="radiogroup"] label p {
            color: white !important;
        }

        /* Radio circle - unselected: white border, transparent inside */
        [data-testid="stSidebar"] .stRadio [role="radiogroup"] label > div:first-child > div {
            border: 2px solid white !important;
            background-color: transparent !important;
        }

        /* Radio circle - selected: orange fill with white border */
        [data-testid="stSidebar"] .stRadio [role="radiogroup"] label[data-checked="true"] > div:first-child > div {
            background-color: #FFA500 !important;
            border: 2px solid white !important;
        }

        /* Sidebar buttons - make them clearly visible as buttons */
        [data-testid="stSidebar"] .stButton > button {
            background-color: #FFA500 !important;
            color: #2B3087 !important;
            border: 2px solid #FFA500 !important;
            border-radius: 8px !important;
            padding: 0.5rem 1rem !important;
            font-weight: bold !important;
            width: 100% !important;
            margin-top: 0.5rem !important;
            transition: all 0.3s ease !important;
        }

        [data-testid="stSidebar"] .stButton > button:hover {
            background-color: white !important;
            color: #2B3087 !important;
            border-color: white !important;
        }

        /* Sidebar checkbox styling */
        [data-testid="stSidebar"] .stCheckbox label {
            background-color: transparent !important;
        }

        [data-testid="stSidebar"] .stCheckbox label p {
            color: white !important;
        }

        [data-testid="stSidebar"] .stCheckbox label > div:first-child > div {
            border-color: white !important;
            background-color: transparent !important;
        }

        [data-testid="stSidebar"] .stCheckbox label[data-checked="true"] > div:first-child > div {
            background-color: #FFA500 !important;
            border-color: #FFA500 !important;
        }
    </style>
    """, unsafe_allow_html=True)
