"""
SAS Material Supply Analysis Dashboard
Main Streamlit Application
"""

# Set environment variable BEFORE any imports
import os
os.environ["PYTHONWARNINGS"] = "ignore::DeprecationWarning"
os.environ["PYTHONWARNINGS"] = "ignore"

import streamlit as st
from pathlib import Path
from PIL import Image
import warnings
import sys

# Suppress warnings at multiple levels
if not sys.warnoptions:
    warnings.simplefilter("ignore")
warnings.filterwarnings('ignore')

# Page configuration with SAS branding (must be first Streamlit call)
st.set_page_config(
    page_title="SAS Material Supply Analysis",
    page_icon="✈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for SAS branding
st.markdown("""
<style>
    /* SAS Blue primary color */
    .stButton>button {
        background-color: #2B3087;
        color: white;
    }

    /* Headers with SAS brand color */
    h1, h2, h3 {
        color: #2B3087;
    }

    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #F0F2F6;
    }

    /* Metric styling */
    [data-testid="stMetricValue"] {
        color: #2B3087;
        font-weight: bold;
    }

    /* Hide Plotly deprecation warnings */
    div[data-testid="stAlert"] div[role="alert"] {
        display: none !important;
    }

    /* Alternative: hide all alerts */
    .element-container div[data-testid="stAlert"] {
        display: none !important;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar with SAS logo
logo_path = Path(__file__).parent / 'assets' / 'Scandinavian_Airlines_logo.svg.png'
if logo_path.exists():
    logo = Image.open(logo_path)
    st.sidebar.image(logo, width='stretch')

st.sidebar.markdown("---")

# Main app
st.title("SAS Material Supply Analysis")
st.markdown("### C-Check Material Preload Dashboard")

st.markdown("""
Welcome to the SAS Material Supply Analysis Dashboard. This tool helps analyze and predict
material preload requirements for aircraft C-checks.

**Navigation:**
Use the sidebar to navigate between different analysis pages:
- **Overview**: High-level KPIs and summary statistics
- **C-Check Analysis**: Detailed analysis of individual C-checks
- **Material Prediction**: Predict material needs for future C-checks
- **Trend Analysis**: Analyze trends over time
- **Aircraft Insights**: Aircraft type-specific analysis

**Data Overview:**
""")

# Load and display data summary
from utils.data_loader import get_data_completeness, get_consumption_by_category

completeness = get_data_completeness()

if completeness:
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Workpacks", completeness['total_workpacks'])

    with col2:
        st.metric("C-Checks", completeness['c_checks'])

    with col3:
        st.metric("With Consumption Data", f"{completeness['c_checks_with_consumption']}")

    with col4:
        st.metric("With Planned Data", f"{completeness['c_checks_with_planned']}")

    st.markdown(f"""
    **Data Completeness:**
    - Aircraft utilization: {completeness['with_utilization']:.1f}%
    - Material consumption: {completeness['with_consumption']:.1f}%
    - Planned material: {completeness['with_planned']:.1f}%
    """)

# Display consumption category breakdown
cat_stats = get_consumption_by_category()

if cat_stats:
    st.markdown("---")
    st.markdown("### Material Consumption Breakdown")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Material Records", f"{cat_stats['total_records']:,}")

    with col2:
        consumable_pct = cat_stats['consumable_records'] / cat_stats['total_records'] * 100
        st.metric("Consumables", f"{cat_stats['consumable_records']:,}",
                  delta=f"{consumable_pct:.1f}%")

    with col3:
        rotable_pct = cat_stats['rotable_records'] / cat_stats['total_records'] * 100
        st.metric("Rotables", f"{cat_stats['rotable_records']:,}",
                  delta=f"{rotable_pct:.1f}%")

    with col4:
        wpno_pct = cat_stats['records_with_wpno_i'] / cat_stats['total_records'] * 100
        st.metric("Direct Matches", f"{cat_stats['records_with_wpno_i']:,}",
                  delta=f"{wpno_pct:.1f}%")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"""
        **Consumables (AA, EA, AS, ES):**
        - AA (to aircraft): {cat_stats['voucher_mode_counts'].get('AA', 0):,} records
        - EA (from aircraft): {cat_stats['voucher_mode_counts'].get('EA', 0):,} records
        - AS (to store): {cat_stats['voucher_mode_counts'].get('AS', 0):,} records
        - ES (from store): {cat_stats['voucher_mode_counts'].get('ES', 0):,} records
        - **Total cost:** €{cat_stats['consumable_cost']:,.0f}
        """)

    with col2:
        st.markdown(f"""
        **Rotables (YA, YE):**
        - YA (install): {cat_stats['voucher_mode_counts'].get('YA', 0):,} records
        - YE (removal): {cat_stats['voucher_mode_counts'].get('YE', 0):,} records
        - **Total cost:** €{cat_stats['rotable_cost']:,.0f}
        """)

    st.markdown(f"""
    **Matching Strategy:**
    - {cat_stats['records_with_wpno_i']:,} records matched directly via workpack ID (wpno_i)
    - {cat_stats['records_without_wpno_i']:,} records matched via date/station/receiver
    """)

st.markdown("---")
st.markdown("*Dashboard developed for Amsterdam University of Applied Sciences*")
st.markdown("*Project: Analysis of Material Supply Processes for Heavy Aircraft Maintenance*")
