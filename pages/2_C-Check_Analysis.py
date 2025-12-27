"""
SAS Material Supply Analysis - C-Check Analysis Page
Detailed analysis of individual C-checks
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import warnings
import sys

# Suppress ALL warnings completely
if not sys.warnoptions:
    warnings.simplefilter("ignore")
warnings.filterwarnings('ignore')

# Import data loaders
from utils.data_loader import get_master_view, load_consumption_detailed, load_planned_material_detailed
from utils.plotly_utils import hide_warnings_css

# Hide warnings with CSS
hide_warnings_css()

# Page config
st.title("C-Check Analysis")
st.markdown("Detailed analysis of individual C-checks")

# Load data
with st.spinner("Loading data..."):
    master_df = get_master_view()
    consumption_detail = load_consumption_detailed()
    planned_detail = load_planned_material_detailed()

if master_df is None:
    st.error("Could not load data")
    st.stop()

# Filter to C-checks only
c_checks = master_df[master_df['is_c_check'] == 1].copy()

if len(c_checks) == 0:
    st.warning("No C-checks found in the dataset")
    st.stop()

# C-Check Selector
st.sidebar.markdown("## Select C-Check")

# Create selector options
c_checks['display_name'] = c_checks.apply(
    lambda row: f"{row['wpno']} - {row['ac_registr']} ({row['ac_typ']}) - {pd.to_datetime(row['start_date']).strftime('%Y-%m-%d') if pd.notna(row['start_date']) else 'N/A'}",
    axis=1
)

selected_display = st.sidebar.selectbox(
    "Choose C-Check",
    c_checks['display_name'].tolist()
)

# Get selected C-check
selected_idx = c_checks[c_checks['display_name'] == selected_display].index[0]
selected_check = c_checks.loc[selected_idx]

st.markdown("---")

# C-Check Details Section
st.markdown("### C-Check Details")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("**Aircraft Information**")
    st.markdown(f"**Registration:** {selected_check['ac_registr']}")
    st.markdown(f"**Type:** {selected_check['ac_typ']}")
    if pd.notna(selected_check['aircraft_hours']):
        st.markdown(f"**Hours:** {selected_check['aircraft_hours']:,.0f}")
    if pd.notna(selected_check['aircraft_cycles']):
        st.markdown(f"**Cycles:** {selected_check['aircraft_cycles']:,.0f}")

with col2:
    st.markdown("**Check Information**")
    st.markdown(f"**Workpack:** {selected_check['wpno']}")
    st.markdown(f"**Station:** {selected_check['station']}")
    if pd.notna(selected_check['duration_days']):
        st.markdown(f"**Duration:** {selected_check['duration_days']:.1f} days")

with col3:
    st.markdown("**Dates & Status**")
    if pd.notna(selected_check['start_date']):
        st.markdown(f"**Start:** {pd.to_datetime(selected_check['start_date']).strftime('%Y-%m-%d')}")
    if pd.notna(selected_check['end_date']):
        st.markdown(f"**End:** {pd.to_datetime(selected_check['end_date']).strftime('%Y-%m-%d')}")
    st.markdown(f"**EOL:** {'Yes' if selected_check['is_eol'] == 1 else 'No'}")
    st.markdown(f"**Bridging:** {'Yes' if selected_check['is_bridging_task'] == 1 else 'No'}")

st.markdown("---")

# Material Analysis Section
has_consumption = pd.notna(selected_check['consumed_parts_count'])
has_planned = pd.notna(selected_check['planned_parts_count'])

if has_consumption and has_planned:
    st.markdown("### Material Analysis: Planned vs Consumed")

    # KPI cards
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Planned Parts",
            f"{int(selected_check['planned_parts_count'])}"
        )

    with col2:
        st.metric(
            "Consumed Parts",
            f"{int(selected_check['consumed_parts_count'])}",
            delta=f"{int(selected_check['parts_variance'])}" if pd.notna(selected_check['parts_variance']) else None
        )

    with col3:
        st.metric(
            "Planned Cost",
            f"€{selected_check['planned_cost']:,.0f}"
        )

    with col4:
        st.metric(
            "Consumed Cost",
            f"€{selected_check['consumed_cost']:,.0f}",
            delta=f"€{selected_check['cost_variance']:,.0f}" if pd.notna(selected_check['cost_variance']) else None
        )

    # Accuracy metrics
    col1, col2 = st.columns(2)

    with col1:
        if pd.notna(selected_check['planning_accuracy']):
            accuracy = selected_check['planning_accuracy']
            accuracy_color = "green" if accuracy >= 80 else "orange" if accuracy >= 60 else "red"
            st.markdown(f"**Planning Accuracy:** <span style='color:{accuracy_color}; font-size:24px;'>{accuracy:.1f}%</span>", unsafe_allow_html=True)

    with col2:
        if pd.notna(selected_check['cost_variance']):
            variance_pct = (selected_check['cost_variance'] / selected_check['planned_cost'] * 100) if selected_check['planned_cost'] > 0 else 0
            variance_color = "green" if abs(variance_pct) < 10 else "orange" if abs(variance_pct) < 20 else "red"
            st.markdown(f"**Cost Variance:** <span style='color:{variance_color}; font-size:24px;'>{variance_pct:.1f}%</span>", unsafe_allow_html=True)

    st.markdown("---")

    # Comparison chart
    st.markdown("#### Planned vs Consumed Comparison")

    comparison_data = pd.DataFrame({
        'Category': ['Parts Count', 'Parts Count', 'Total Cost', 'Total Cost'],
        'Type': ['Planned', 'Consumed', 'Planned', 'Consumed'],
        'Value': [
            selected_check['planned_parts_count'],
            selected_check['consumed_parts_count'],
            selected_check['planned_cost'],
            selected_check['consumed_cost']
        ]
    })

    fig_comparison = px.bar(
        comparison_data,
        x='Category',
        y='Value',
        color='Type',
        barmode='group',
        title="Planned vs Consumed",
        color_discrete_map={'Planned': '#2B3087', 'Consumed': '#FFA500'}
    )

    fig_comparison.update_layout(
        yaxis_title="Value",
        xaxis_title=""
    )

    st.plotly_chart(fig_comparison, width='stretch')

elif has_planned:
    st.markdown("### Planned Material")
    st.info("Consumption data not available for this C-check")

    col1, col2 = st.columns(2)

    with col1:
        st.metric("Planned Parts", f"{int(selected_check['planned_parts_count'])}")

    with col2:
        st.metric("Planned Cost", f"€{selected_check['planned_cost']:,.0f}")

elif has_consumption:
    st.markdown("### Consumed Material")
    st.info("Planned material data not available for this C-check")

    col1, col2 = st.columns(2)

    with col1:
        st.metric("Consumed Parts", f"{int(selected_check['consumed_parts_count'])}")

    with col2:
        st.metric("Consumed Cost", f"€{selected_check['consumed_cost']:,.0f}")

else:
    st.warning("No material data (planned or consumed) available for this C-check")

st.markdown("---")

# Detailed Material Lists
st.markdown("### Detailed Material Lists")

tab1, tab2 = st.tabs(["Planned Material", "Consumed Material"])

with tab1:
    if planned_detail is not None and has_planned:
        # Filter planned material for this workpack
        planned_parts = planned_detail[planned_detail['wpno_i'] == selected_check['wpno_i']].copy()

        if len(planned_parts) > 0:
            st.markdown(f"**Total: {len(planned_parts)} planned parts**")

            # Display table
            display_cols = ['partno', 'description', 'qty', 'confirmed_qty', 'average_price']
            planned_display = planned_parts[display_cols].copy()
            planned_display.columns = ['Part Number', 'Description', 'Quantity', 'Confirmed Qty', 'Avg Price']
            planned_display['Avg Price'] = planned_display['Avg Price'].apply(lambda x: f"€{x:,.2f}" if pd.notna(x) else "N/A")

            # Sort by price descending
            planned_display = planned_display.sort_values('Avg Price', ascending=False)

            st.dataframe(
                planned_display,
                width='stretch',
                hide_index=True
            )

            # Top 10 by cost
            st.markdown("#### Top 10 Parts by Cost")
            top_planned = planned_parts.nlargest(10, 'average_price')[['partno', 'description', 'average_price']]
            top_planned.columns = ['Part Number', 'Description', 'Cost']
            top_planned['Cost'] = top_planned['Cost'].apply(lambda x: f"€{x:,.2f}")

            st.dataframe(
                top_planned,
                width='stretch',
                hide_index=True
            )
        else:
            st.info("No planned material details found for this C-check")
    else:
        st.info("Planned material data not available")

with tab2:
    if consumption_detail is not None and has_consumption:
        # Filter consumption for this workpack (only negative qty = consumed/used)
        consumed_parts = consumption_detail[
            (consumption_detail['wpno_i'] == selected_check['wpno_i']) &
            (consumption_detail['qty'] < 0)
        ].copy()

        if len(consumed_parts) > 0:
            # Calculate actual consumed quantity
            consumed_parts['consumed_qty'] = consumed_parts['qty'].abs()
            # average_price is already the total price
            consumed_parts['consumed_cost'] = consumed_parts['average_price']

            st.markdown(f"**Total: {len(consumed_parts)} consumed parts**")

            # Display table (consumption has no 'description' column)
            display_cols = ['partno', 'consumed_qty', 'consumed_cost', 'del_date', 'ata_chapter']
            consumed_display = consumed_parts[display_cols].copy()
            consumed_display.columns = ['Part Number', 'Quantity', 'Cost', 'Delivery Date', 'ATA Chapter']
            consumed_display['Cost'] = consumed_display['Cost'].apply(lambda x: f"€{x:,.2f}" if pd.notna(x) else "N/A")
            consumed_display['Delivery Date'] = pd.to_datetime(consumed_display['Delivery Date']).dt.strftime('%Y-%m-%d')
            consumed_display['ATA Chapter'] = consumed_display['ATA Chapter'].fillna('N/A')

            # Sort by cost descending
            consumed_display = consumed_display.sort_values('Cost', ascending=False)

            st.dataframe(
                consumed_display,
                width='stretch',
                hide_index=True
            )

            # Top 10 by cost
            st.markdown("#### Top 10 Parts by Cost")
            top_consumed = consumed_parts.nlargest(10, 'consumed_cost')[['partno', 'consumed_cost', 'ata_chapter']]
            top_consumed.columns = ['Part Number', 'Cost', 'ATA Chapter']
            top_consumed['Cost'] = top_consumed['Cost'].apply(lambda x: f"€{x:,.2f}")
            top_consumed['ATA Chapter'] = top_consumed['ATA Chapter'].fillna('N/A')

            st.dataframe(
                top_consumed,
                width='stretch',
                hide_index=True
            )
        else:
            st.info("No consumed material details found for this C-check")
    else:
        st.info("Consumption data not available")

st.markdown("---")
st.markdown("*Use the sidebar to select different C-checks or navigate to other pages*")
