"""
SAS Material Supply Analysis - Aircraft Insights Page
Aircraft type-specific analysis and comparison
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import numpy as np
from scipy import stats
import warnings
import sys

# Suppress ALL warnings completely
if not sys.warnoptions:
    warnings.simplefilter("ignore")
warnings.filterwarnings('ignore')

# Import data loader
from utils.data_loader import get_master_view, load_consumption_detailed, is_data_uploaded, show_upload_required
from utils.plotly_utils import hide_warnings_css
from utils import format_currency

# Hide warnings with CSS
hide_warnings_css()

# Page config
st.title("Aircraft Insights")
st.markdown("Aircraft type-specific material analysis")

# Check if data is uploaded
if not is_data_uploaded():
    show_upload_required()

# Load data
with st.spinner("Loading data..."):
    master_df = get_master_view()
    consumption_detail = load_consumption_detailed()

if master_df is None:
    st.error("Could not load data")
    st.stop()

# Filter to C-checks only
c_checks = master_df[master_df['is_c_check'] == 1].copy()

# Aircraft type selector
st.sidebar.markdown("## Select Aircraft Type")

aircraft_types = sorted(c_checks['ac_typ'].unique().tolist())
selected_ac_type = st.sidebar.selectbox("Aircraft Type", aircraft_types)

# Filter to selected aircraft type
ac_data = c_checks[c_checks['ac_typ'] == selected_ac_type].copy()

# Aircraft Type Summary
st.markdown(f"### {selected_ac_type} Summary")

with st.container(border=True):
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total C-Checks", len(ac_data))

    with col2:
        with_consumption = ac_data['consumed_parts_count'].notna().sum()
        st.metric(
            "With Consumption Data",
            with_consumption,
            delta=f"{with_consumption/len(ac_data)*100:.1f}%"
        )

    with col3:
        avg_util = ac_data['aircraft_hours'].mean()
        if pd.notna(avg_util):
            st.metric("Avg Aircraft Hours", f"{avg_util:,.0f}")
        else:
            st.metric("Avg Aircraft Hours", "N/A")

    with col4:
        avg_cycles = ac_data['aircraft_cycles'].mean()
        if pd.notna(avg_cycles):
            st.metric("Avg Aircraft Cycles", f"{avg_cycles:,.0f}")
        else:
            st.metric("Avg Aircraft Cycles", "N/A")

    st.divider()

    # Additional metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        avg_cost = ac_data['consumed_cost'].mean()
        if pd.notna(avg_cost):
            st.metric("Avg Material Cost", format_currency(avg_cost))
        else:
            st.metric("Avg Material Cost", "N/A")

    with col2:
        avg_parts = ac_data['consumed_parts_count'].mean()
        if pd.notna(avg_parts):
            st.metric("Avg Parts per C-Check", f"{avg_parts:.0f}")
        else:
            st.metric("Avg Parts per C-Check", "N/A")

    with col3:
        avg_duration = ac_data['duration_days'].mean()
        if pd.notna(avg_duration):
            st.metric("Avg Duration", f"{avg_duration:.1f} days")
        else:
            st.metric("Avg Duration", "N/A")

    with col4:
        avg_accuracy = ac_data['planning_accuracy'].mean()
        if pd.notna(avg_accuracy):
            st.metric("Avg Planning Accuracy", f"{avg_accuracy:.1f}%")
        else:
            st.metric("Avg Planning Accuracy", "N/A")

st.markdown("---")

# Utilization Correlation Analysis
st.markdown("### Utilization Correlation Analysis")
st.markdown("Examine the relationship between aircraft utilization and material consumption")

util_data = ac_data[
    (ac_data['aircraft_hours'].notna()) &
    (ac_data['consumed_parts_count'].notna())
].copy()

if len(util_data) > 5:
    col1, col2 = st.columns(2)

    with col1:
        # Aircraft hours vs parts consumed
        fig_hours = px.scatter(
            util_data,
            x='aircraft_hours',
            y='consumed_parts_count',
            title=f"Aircraft Hours vs Parts Consumed ({selected_ac_type})",
            labels={
                'aircraft_hours': 'Aircraft Hours',
                'consumed_parts_count': 'Parts Consumed'
            },
            trendline="ols",
            hover_data=['wpno', 'check_type']
        )

        fig_hours.update_traces(marker=dict(size=10, color='#2B3087'))
        st.plotly_chart(fig_hours, width='stretch')

        # Correlation coefficient
        corr_hours = util_data['aircraft_hours'].corr(util_data['consumed_parts_count'])
        if abs(corr_hours) > 0.5:
            st.success(f"Strong correlation: {corr_hours:.2f}")
        elif abs(corr_hours) > 0.3:
            st.info(f"Moderate correlation: {corr_hours:.2f}")
        else:
            st.warning(f"Weak correlation: {corr_hours:.2f}")

    with col2:
        # Aircraft cycles vs parts consumed
        if len(util_data) > 5:
            fig_cycles = px.scatter(
                util_data,
                x='aircraft_cycles',
                y='consumed_parts_count',
                title=f"Aircraft Cycles vs Parts Consumed ({selected_ac_type})",
                labels={
                    'aircraft_cycles': 'Aircraft Cycles',
                    'consumed_parts_count': 'Parts Consumed'
                },
                trendline="ols",
                hover_data=['wpno', 'check_type']
            )

            fig_cycles.update_traces(marker=dict(size=10, color='#FFA500'))
            st.plotly_chart(fig_cycles, width='stretch')

            # Correlation coefficient
            corr_cycles = util_data['aircraft_cycles'].corr(util_data['consumed_parts_count'])
            if abs(corr_cycles) > 0.5:
                st.success(f"Strong correlation: {corr_cycles:.2f}")
            elif abs(corr_cycles) > 0.3:
                st.info(f"Moderate correlation: {corr_cycles:.2f}")
            else:
                st.warning(f"Weak correlation: {corr_cycles:.2f}")
        else:
            st.info("Insufficient data for cycles vs parts analysis")
else:
    st.info("Insufficient data for utilization correlation analysis (need at least 5 C-checks with complete data)")

st.markdown("---")

# Parts Analysis by Aircraft Type
st.markdown("### Parts Analysis")

if consumption_detail is not None:
    # Get all parts for this aircraft type (only negative qty = consumed/used)
    ac_wpnos = ac_data['wpno_i'].unique()
    ac_parts = consumption_detail[
        (consumption_detail['wpno_i'].isin(ac_wpnos)) &
        (consumption_detail['qty'] < 0)
    ].copy()

    if len(ac_parts) > 0:
        # Calculate consumed quantity
        ac_parts['consumed_qty'] = ac_parts['qty'].abs()
        # average_price is already the total price
        ac_parts['consumed_cost'] = ac_parts['average_price']

        st.markdown(f"**Total parts consumed across all {selected_ac_type} C-checks:** {len(ac_parts)}")

        # Top 10 most used parts (consumption has no 'description' column)
        st.markdown("#### Top 10 Most Frequently Used Parts")

        top_parts = ac_parts.groupby(['partno', 'ata_chapter']).agg({
            'consumed_qty': 'sum',
            'consumed_cost': 'sum',
            'wpno_i': 'count'
        }).reset_index()

        top_parts.columns = ['Part Number', 'ATA Chapter', 'Total Qty', 'Total Cost', 'Frequency']
        top_parts = top_parts.sort_values('Frequency', ascending=False).head(10)

        top_parts['Total Cost'] = top_parts['Total Cost'].apply(lambda x: f"€{x:,.0f}" if pd.notna(x) else "N/A")
        top_parts['ATA Chapter'] = top_parts['ATA Chapter'].fillna('N/A')

        st.dataframe(
            top_parts,
            width='stretch',
            hide_index=True
        )
    else:
        st.info("No detailed parts data available for this aircraft type")
else:
    st.info("Detailed consumption data not loaded")

st.markdown("---")

# Comparison Across All Aircraft Types
st.markdown("### Aircraft Type Comparison")
st.markdown("Compare key metrics across all aircraft types")

# Create comparison dataframe
comparison_stats = c_checks.groupby('ac_typ').agg({
    'wpno_i': 'count',
    'consumed_parts_count': 'mean',
    'consumed_cost': 'mean',
    'duration_days': 'mean',
    'planning_accuracy': 'mean',
    'aircraft_hours': 'mean',
    'aircraft_cycles': 'mean'
}).reset_index()

comparison_stats.columns = [
    'Aircraft Type', 'C-Checks', 'Avg Parts', 'Avg Cost',
    'Avg Duration (days)', 'Avg Accuracy %', 'Avg Hours', 'Avg Cycles'
]

# Sort by number of C-checks
comparison_stats = comparison_stats.sort_values('C-Checks', ascending=False)

# Highlight selected aircraft
def highlight_selected(row):
    if row['Aircraft Type'] == selected_ac_type:
        return ['background-color: #E8F4F8'] * len(row)
    return [''] * len(row)

# Format table
display_comparison = comparison_stats.copy()
display_comparison['Avg Parts'] = display_comparison['Avg Parts'].apply(lambda x: f"{x:.0f}" if pd.notna(x) else "N/A")
display_comparison['Avg Cost'] = display_comparison['Avg Cost'].apply(lambda x: f"€{x:,.0f}" if pd.notna(x) else "N/A")
display_comparison['Avg Duration (days)'] = display_comparison['Avg Duration (days)'].apply(lambda x: f"{x:.1f}" if pd.notna(x) else "N/A")
display_comparison['Avg Accuracy %'] = display_comparison['Avg Accuracy %'].apply(lambda x: f"{x:.1f}%" if pd.notna(x) else "N/A")
display_comparison['Avg Hours'] = display_comparison['Avg Hours'].apply(lambda x: f"{x:,.0f}" if pd.notna(x) else "N/A")
display_comparison['Avg Cycles'] = display_comparison['Avg Cycles'].apply(lambda x: f"{x:,.0f}" if pd.notna(x) else "N/A")

st.dataframe(
    display_comparison,
    width='stretch',
    hide_index=True
)

# Visual comparison charts
col1, col2 = st.columns(2)

with col1:
    # Average cost by aircraft type
    cost_comparison = comparison_stats[comparison_stats['Avg Cost'].notna()].copy()

    if len(cost_comparison) > 0:
        fig_ac_cost = px.bar(
            cost_comparison,
            x='Aircraft Type',
            y='Avg Cost',
            title="Average Material Cost by Aircraft Type",
            color='Avg Cost',
            color_continuous_scale='Blues'
        )

        # Highlight selected aircraft
        fig_ac_cost.update_traces(
            marker_line_color=['#FF0000' if x == selected_ac_type else '#FFFFFF' for x in cost_comparison['Aircraft Type']],
            marker_line_width=3
        )

        st.plotly_chart(fig_ac_cost, width='stretch')

with col2:
    # Average parts by aircraft type
    parts_comparison = comparison_stats[comparison_stats['Avg Parts'].notna()].copy()

    if len(parts_comparison) > 0:
        # Convert back to numeric for plotting
        parts_comparison['Avg Parts Numeric'] = comparison_stats['Avg Parts']

        fig_ac_parts = px.bar(
            parts_comparison,
            x='Aircraft Type',
            y='Avg Parts Numeric',
            title="Average Parts Count by Aircraft Type",
            color='Avg Parts Numeric',
            color_continuous_scale='Oranges'
        )

        # Highlight selected aircraft
        fig_ac_parts.update_traces(
            marker_line_color=['#FF0000' if x == selected_ac_type else '#FFFFFF' for x in parts_comparison['Aircraft Type']],
            marker_line_width=3
        )

        fig_ac_parts.update_layout(yaxis_title="Average Parts Count")

        st.plotly_chart(fig_ac_parts, width='stretch')

st.markdown("---")
st.markdown("*Use the sidebar to select different aircraft types or navigate to other pages*")
