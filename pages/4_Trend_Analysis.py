"""
SAS Material Supply Analysis - Trend Analysis Page
Analyze trends in material planning and consumption over time
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import numpy as np
import warnings
import sys

# Suppress ALL warnings completely
if not sys.warnoptions:
    warnings.simplefilter("ignore")
warnings.filterwarnings('ignore')

# Import data loader
from utils.data_loader import get_master_view, is_data_uploaded, show_upload_required
from utils.plotly_utils import hide_warnings_css
from utils import format_currency

# Hide warnings with CSS
hide_warnings_css()

# Apply shared SAS styling
from utils.styling import apply_sas_styling
apply_sas_styling()

# Page config
st.title("Trend Analysis")
st.markdown("Analyze material planning trends over time")

# Check if data is uploaded
if not is_data_uploaded():
    show_upload_required()

# Load data
with st.spinner("Loading data..."):
    master_df = get_master_view()

if master_df is None:
    st.error("Could not load data")
    st.stop()

# Filter to C-checks only
c_checks = master_df[master_df['is_c_check'] == 1].copy()

# Add period columns for grouping
c_checks['year_month'] = pd.to_datetime(c_checks['start_date']).dt.to_period('M').astype(str)
c_checks['year'] = pd.to_datetime(c_checks['start_date']).dt.year
c_checks['quarter'] = pd.to_datetime(c_checks['start_date']).dt.to_period('Q').astype(str)

# Sidebar filters
st.sidebar.markdown("## Filters")

# Time period
time_period = st.sidebar.selectbox(
    "Time Period",
    ["Monthly", "Quarterly", "Yearly"]
)

# Aircraft type filter
ac_types = ['All'] + sorted(c_checks['ac_typ'].unique().tolist())
selected_ac_type = st.sidebar.selectbox("Aircraft Type", ac_types)

# Apply filters
filtered_df = c_checks.copy()

if selected_ac_type != 'All':
    filtered_df = filtered_df[filtered_df['ac_typ'] == selected_ac_type]

# Planning Accuracy Trends
st.markdown("### Planning Accuracy Trends")
st.markdown("Track how accurately material requirements are being planned over time")

accuracy_data = filtered_df[filtered_df['planning_accuracy'].notna()].copy()

if len(accuracy_data) > 0:
    # Group by selected period
    period_col = 'year_month' if time_period == 'Monthly' else 'quarter' if time_period == 'Quarterly' else 'year'

    accuracy_trend = accuracy_data.groupby(period_col).agg({
        'planning_accuracy': 'mean',
        'wpno_i': 'count'
    }).reset_index()

    accuracy_trend.columns = ['Period', 'Average Accuracy %', 'Count']

    # Create chart
    fig_accuracy = go.Figure()

    fig_accuracy.add_trace(go.Scatter(
        x=accuracy_trend['Period'],
        y=accuracy_trend['Average Accuracy %'],
        mode='lines+markers',
        name='Planning Accuracy',
        line=dict(color='#2B3087', width=3),
        marker=dict(size=8)
    ))

    fig_accuracy.add_hline(
        y=100,
        line_dash="dash",
        line_color="green",
        annotation_text="Perfect Accuracy (100%)"
    )

    fig_accuracy.update_layout(
        title=f"Planning Accuracy Over Time ({time_period})",
        xaxis_title="Period",
        yaxis_title="Average Accuracy (%)",
        hovermode='x unified'
    )

    st.plotly_chart(fig_accuracy, width='stretch')

    # Statistics
    with st.container(border=True):
        col1, col2, col3 = st.columns(3)

        with col1:
            overall_accuracy = accuracy_data['planning_accuracy'].mean()
            st.metric("Overall Average Accuracy", f"{overall_accuracy:.1f}%")

        with col2:
            trend_direction = "Improving" if accuracy_trend['Average Accuracy %'].iloc[-1] > accuracy_trend['Average Accuracy %'].iloc[0] else "Declining"
            st.metric("Trend Direction", trend_direction)

        with col3:
            best_period = accuracy_trend.loc[accuracy_trend['Average Accuracy %'].idxmax(), 'Period']
            st.metric("Best Period", f"{best_period}")
else:
    st.info("Insufficient data with planning accuracy for trend analysis")

st.markdown("---")

# Cost Trends
st.markdown("### Cost Trends")
st.markdown("Analyze how material costs are changing over time")

cost_data = filtered_df[filtered_df['consumed_cost'].notna()].copy()

if len(cost_data) > 0:
    period_col = 'year_month' if time_period == 'Monthly' else 'quarter' if time_period == 'Quarterly' else 'year'

    # Overall cost trend
    cost_trend = cost_data.groupby(period_col).agg({
        'consumed_cost': 'mean',
        'wpno_i': 'count'
    }).reset_index()

    cost_trend.columns = ['Period', 'Average Cost', 'Count']

    fig_cost = px.line(
        cost_trend,
        x='Period',
        y='Average Cost',
        title=f"Average Cost per C-Check Over Time ({time_period})",
        markers=True
    )

    fig_cost.update_traces(line_color='#2B3087')
    fig_cost.update_layout(
        yaxis_title="Average Cost (EUR)",
        xaxis_title="Period"
    )

    st.plotly_chart(fig_cost, width='stretch')

    # By aircraft type
    if selected_ac_type == 'All':
        st.markdown("#### Cost Trends by Aircraft Type")

        cost_by_type = cost_data.groupby([period_col, 'ac_typ']).agg({
            'consumed_cost': 'mean'
        }).reset_index()

        cost_by_type.columns = ['Period', 'Aircraft Type', 'Average Cost']

        fig_cost_type = px.line(
            cost_by_type,
            x='Period',
            y='Average Cost',
            color='Aircraft Type',
            title="Cost Trends by Aircraft Type",
            markers=True
        )

        fig_cost_type.update_layout(
            yaxis_title="Average Cost (EUR)",
            xaxis_title="Period"
        )

        st.plotly_chart(fig_cost_type, width='stretch')

    # Cost statistics
    with st.container(border=True):
        col1, col2, col3 = st.columns(3)

        with col1:
            avg_cost = cost_data['consumed_cost'].mean()
            st.metric("Average Cost", format_currency(avg_cost))

        with col2:
            cost_change = ((cost_trend['Average Cost'].iloc[-1] / cost_trend['Average Cost'].iloc[0]) - 1) * 100
            st.metric("Cost Change", f"{cost_change:+.1f}%")

        with col3:
            max_cost = cost_data['consumed_cost'].max()
            st.metric("Highest Cost", format_currency(max_cost))
else:
    st.info("Insufficient cost data for trend analysis")

st.markdown("---")

# Material Usage Trends
st.markdown("### Material Usage Trends")
st.markdown("Track the number of parts used per C-check over time")

parts_data = filtered_df[filtered_df['consumed_parts_count'].notna()].copy()

if len(parts_data) > 0:
    period_col = 'year_month' if time_period == 'Monthly' else 'quarter' if time_period == 'Quarterly' else 'year'

    parts_trend = parts_data.groupby(period_col).agg({
        'consumed_parts_count': ['mean', 'min', 'max'],
        'wpno_i': 'count'
    }).reset_index()

    parts_trend.columns = ['Period', 'Average Parts', 'Min Parts', 'Max Parts', 'Count']

    # Create chart with range
    fig_parts = go.Figure()

    fig_parts.add_trace(go.Scatter(
        x=parts_trend['Period'],
        y=parts_trend['Average Parts'],
        mode='lines+markers',
        name='Average',
        line=dict(color='#2B3087', width=3),
        marker=dict(size=8)
    ))

    fig_parts.add_trace(go.Scatter(
        x=parts_trend['Period'],
        y=parts_trend['Max Parts'],
        mode='lines',
        name='Max',
        line=dict(color='#FFA500', width=1, dash='dash'),
        fill=None
    ))

    fig_parts.add_trace(go.Scatter(
        x=parts_trend['Period'],
        y=parts_trend['Min Parts'],
        mode='lines',
        name='Min',
        line=dict(color='#FFA500', width=1, dash='dash'),
        fill='tonexty',
        fillcolor='rgba(255, 165, 0, 0.2)'
    ))

    fig_parts.update_layout(
        title=f"Parts Count Trends ({time_period})",
        xaxis_title="Period",
        yaxis_title="Number of Parts",
        hovermode='x unified'
    )

    st.plotly_chart(fig_parts, width='stretch')

    # Statistics
    with st.container(border=True):
        col1, col2, col3 = st.columns(3)

        with col1:
            avg_parts = parts_data['consumed_parts_count'].mean()
            st.metric("Average Parts", f"{avg_parts:.0f}")

        with col2:
            parts_std = parts_data['consumed_parts_count'].std()
            st.metric("Standard Deviation", f"{parts_std:.0f}")

        with col3:
            parts_range = parts_data['consumed_parts_count'].max() - parts_data['consumed_parts_count'].min()
            st.metric("Range", f"{parts_range:.0f}")
else:
    st.info("Insufficient parts data for trend analysis")

st.markdown("---")

# Station Performance Comparison
st.markdown("### Station Performance Comparison")
st.markdown("Compare material planning performance across different stations")

station_data = filtered_df[
    (filtered_df['planning_accuracy'].notna()) |
    (filtered_df['consumed_cost'].notna())
].copy()

if len(station_data) > 0:
    station_stats = station_data.groupby('station').agg({
        'wpno_i': 'count',
        'planning_accuracy': 'mean',
        'consumed_cost': 'mean',
        'consumed_parts_count': 'mean',
        'duration_days': 'mean'
    }).reset_index()

    station_stats.columns = [
        'Station', 'C-Checks', 'Avg Accuracy %', 'Avg Cost',
        'Avg Parts', 'Avg Duration (days)'
    ]

    # Sort by accuracy
    station_stats = station_stats.sort_values('Avg Accuracy %', ascending=False)

    # Bar chart of accuracy by station
    fig_station = px.bar(
        station_stats,
        x='Station',
        y='Avg Accuracy %',
        title="Planning Accuracy by Station",
        color='Avg Accuracy %',
        color_continuous_scale='Blues'
    )

    fig_station.add_hline(
        y=100,
        line_dash="dash",
        line_color="green",
        annotation_text="Perfect Accuracy"
    )

    st.plotly_chart(fig_station, width='stretch')

    # Table
    st.markdown("#### Station Performance Table")

    display_stats = station_stats.copy()
    display_stats['Avg Accuracy %'] = display_stats['Avg Accuracy %'].apply(lambda x: f"{x:.1f}%" if pd.notna(x) else "N/A")
    display_stats['Avg Cost'] = display_stats['Avg Cost'].apply(lambda x: f"€{x:,.0f}" if pd.notna(x) else "N/A")
    display_stats['Avg Parts'] = display_stats['Avg Parts'].apply(lambda x: f"{x:.0f}" if pd.notna(x) else "N/A")
    display_stats['Avg Duration (days)'] = display_stats['Avg Duration (days)'].apply(lambda x: f"{x:.1f}" if pd.notna(x) else "N/A")

    st.dataframe(
        display_stats,
        width='stretch',
        hide_index=True
    )
else:
    st.info("Insufficient data for station comparison")

st.markdown("---")
st.markdown("*Use the sidebar to filter by aircraft type or navigate to other pages*")
