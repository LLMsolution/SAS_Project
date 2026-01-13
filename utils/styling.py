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
    </style>
    """, unsafe_allow_html=True)

    # Sidebar with SAS logo (white version for blue background)
    # Find the project root (parent of utils folder)
    utils_dir = Path(__file__).parent
    project_root = utils_dir.parent
    logo_path = project_root / 'assets' / 'sas_logo_white.png'

    if logo_path.exists():
        logo = Image.open(logo_path)
        st.sidebar.image(logo, width=200)

    st.sidebar.markdown("---")
