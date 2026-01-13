"""
SAS Material Supply Analysis - Overview Page
High-level KPIs and summary statistics
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

# Import data loader
from utils.data_loader import get_master_view, is_data_uploaded, show_upload_required
from utils.plotly_utils import hide_warnings_css
from utils import format_currency, format_number

# Hide warnings with CSS
hide_warnings_css()

# Page config
st.title("Overview & KPIs")
st.markdown("High-level summary of C-check material planning performance")

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

# Sidebar filters
st.sidebar.markdown("## Filters")

# Aircraft type filter
ac_types = ['All'] + sorted(c_checks['ac_typ'].unique().tolist())
selected_ac_type = st.sidebar.selectbox("Aircraft Type", ac_types)

# Check type filter
check_types = ['All'] + sorted([x for x in c_checks['check_type'].unique() if pd.notna(x)])
selected_check_type = st.sidebar.selectbox("Check Type", check_types)

# Station filter
stations = ['All'] + sorted(c_checks['station'].unique().tolist())
selected_station = st.sidebar.selectbox("Station", stations)

# Apply filters
filtered_df = c_checks.copy()

if selected_ac_type != 'All':
    filtered_df = filtered_df[filtered_df['ac_typ'] == selected_ac_type]

if selected_check_type != 'All':
    filtered_df = filtered_df[filtered_df['check_type'] == selected_check_type]

if selected_station != 'All':
    filtered_df = filtered_df[filtered_df['station'] == selected_station]

# KPI Cards
st.markdown("### Key Performance Indicators")

with st.container(border=True):
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Total C-Checks",
            len(filtered_df),
            delta=f"{len(filtered_df)/len(c_checks)*100:.0f}% of total"
        )

    with col2:
        avg_accuracy = filtered_df['planning_accuracy'].mean()
        if pd.notna(avg_accuracy):
            st.metric(
                "Avg Planning Accuracy",
                f"{avg_accuracy:.1f}%",
                delta=f"{avg_accuracy-100:.1f}pp" if avg_accuracy > 0 else None
            )
        else:
            st.metric("Avg Planning Accuracy", "N/A")

    with col3:
        with_consumption = filtered_df['consumed_parts_count'].notna().sum()
        st.metric(
            "With Consumption Data",
            with_consumption,
            delta=f"{with_consumption/len(filtered_df)*100:.1f}%"
        )

    with col4:
        avg_cost = filtered_df['consumed_cost'].mean()
        if pd.notna(avg_cost):
            st.metric(
                "Avg Cost per C-Check",
                format_currency(avg_cost)
            )
        else:
            st.metric("Avg Cost per C-Check", "N/A")

    st.divider()

    # Additional metrics row
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        avg_parts = filtered_df['consumed_parts_count'].mean()
        if pd.notna(avg_parts):
            st.metric("Avg Parts per C-Check", f"{avg_parts:.0f}")
        else:
            st.metric("Avg Parts per C-Check", "N/A")

    with col2:
        avg_duration = filtered_df['duration_days'].mean()
        if pd.notna(avg_duration):
            st.metric("Avg Duration", f"{avg_duration:.1f} days")
        else:
            st.metric("Avg Duration", "N/A")

    with col3:
        total_cost_variance = filtered_df['cost_variance'].sum()
        if pd.notna(total_cost_variance):
            st.metric(
                "Total Cost Variance",
                format_currency(abs(total_cost_variance)),
                delta=f"{'Over' if total_cost_variance > 0 else 'Under'} budget"
            )
        else:
            st.metric("Total Cost Variance", "N/A")

    with col4:
        with_planned = filtered_df['planned_parts_count'].notna().sum()
        st.metric(
            "With Planned Data",
            with_planned,
            delta=f"{with_planned/len(filtered_df)*100:.1f}%"
        )

st.markdown("---")

# Charts section
st.markdown("### Visual Analytics")

# Create two columns for charts
chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    st.markdown("#### C-Checks by Aircraft Type")

    # Count by aircraft type
    ac_type_counts = filtered_df['ac_typ'].value_counts().reset_index()
    ac_type_counts.columns = ['Aircraft Type', 'Count']

    fig_ac_type = px.bar(
        ac_type_counts,
        x='Aircraft Type',
        y='Count',
        color='Count',
        color_continuous_scale='Blues',
        title="Distribution by Aircraft Type"
    )

    fig_ac_type.update_layout(
        showlegend=False,
        xaxis_title="Aircraft Type",
        yaxis_title="Number of C-Checks"
    )

    st.plotly_chart(fig_ac_type, width='stretch')

with chart_col2:
    st.markdown("#### C-Checks by Check Type")

    # Count by check type
    check_type_counts = filtered_df[filtered_df['check_type'].notna()]['check_type'].value_counts().reset_index()
    check_type_counts.columns = ['Check Type', 'Count']

    fig_check_type = px.pie(
        check_type_counts,
        values='Count',
        names='Check Type',
        title="Distribution by Check Type",
        color_discrete_sequence=px.colors.sequential.Blues
    )

    st.plotly_chart(fig_check_type, width='stretch')

# Timeline chart
st.markdown("#### C-Checks Over Time")

# Group by month
filtered_df['year_month'] = pd.to_datetime(filtered_df['start_date']).dt.to_period('M').astype(str)
timeline_data = filtered_df.groupby('year_month').size().reset_index()
timeline_data.columns = ['Month', 'Count']

fig_timeline = px.line(
    timeline_data,
    x='Month',
    y='Count',
    title="C-Checks Trend Over Time",
    markers=True
)

fig_timeline.update_traces(line_color='#2B3087')
fig_timeline.update_layout(
    xaxis_title="Month",
    yaxis_title="Number of C-Checks"
)

st.plotly_chart(fig_timeline, width='stretch')

# Station Performance
st.markdown("#### Station Performance")

# Group by station
station_stats = filtered_df.groupby('station').agg({
    'wpno_i': 'count',
    'consumed_parts_count': 'mean',
    'consumed_cost': 'mean',
    'planning_accuracy': 'mean'
}).reset_index()

station_stats.columns = ['Station', 'C-Checks', 'Avg Parts', 'Avg Cost', 'Planning Accuracy %']

# Format and display
station_stats['Avg Parts'] = station_stats['Avg Parts'].round(0)
station_stats['Avg Cost'] = station_stats['Avg Cost'].apply(lambda x: f"€{x:,.0f}" if pd.notna(x) else "N/A")
station_stats['Planning Accuracy %'] = station_stats['Planning Accuracy %'].apply(lambda x: f"{x:.1f}%" if pd.notna(x) else "N/A")

st.dataframe(
    station_stats.sort_values('C-Checks', ascending=False),
    width='stretch',
    hide_index=True
)

# Data quality section
st.markdown("---")
st.markdown("### Data Quality & Completeness")

col1, col2 = st.columns(2)

with col1:
    st.markdown("#### Data Availability")

    availability_data = {
        'Data Type': [
            'Aircraft Utilization',
            'Material Consumption',
            'Planned Material',
            'Complete Records (All Data)'
        ],
        'Available': [
            filtered_df['aircraft_hours'].notna().sum(),
            filtered_df['consumed_parts_count'].notna().sum(),
            filtered_df['planned_parts_count'].notna().sum(),
            filtered_df[
                (filtered_df['aircraft_hours'].notna()) &
                (filtered_df['consumed_parts_count'].notna()) &
                (filtered_df['planned_parts_count'].notna())
            ].shape[0]
        ],
        'Percentage': [
            f"{filtered_df['aircraft_hours'].notna().sum()/len(filtered_df)*100:.1f}%",
            f"{filtered_df['consumed_parts_count'].notna().sum()/len(filtered_df)*100:.1f}%",
            f"{filtered_df['planned_parts_count'].notna().sum()/len(filtered_df)*100:.1f}%",
            f"{filtered_df[(filtered_df['aircraft_hours'].notna()) & (filtered_df['consumed_parts_count'].notna()) & (filtered_df['planned_parts_count'].notna())].shape[0]/len(filtered_df)*100:.1f}%"
        ]
    }

    st.dataframe(
        pd.DataFrame(availability_data),
        width='stretch',
        hide_index=True
    )

with col2:
    st.markdown("#### Planning Accuracy Distribution")

    # Filter to records with planning accuracy
    accuracy_data = filtered_df[filtered_df['planning_accuracy'].notna()]['planning_accuracy']

    if len(accuracy_data) > 0:
        fig_accuracy = px.histogram(
            x=accuracy_data,
            nbins=20,
            title="Planning Accuracy Distribution",
            labels={'x': 'Planning Accuracy (%)', 'y': 'Count'}
        )

        fig_accuracy.update_traces(marker_color='#2B3087')
        st.plotly_chart(fig_accuracy, width='stretch')
    else:
        st.info("No planning accuracy data available for selected filters")

st.markdown("---")

# Aggregate Analytics Across All C-Checks
st.markdown("### Aggregate C-Check Analytics")
st.markdown("Detailed statistics across all C-checks in the selected filters")

# Custom CSS for styled containers
st.markdown("""
<style>
    .stats-container {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        border-radius: 12px;
        padding: 1.5rem;
        border-left: 4px solid #2B3087;
        margin-bottom: 1rem;
    }
    .stats-container-green {
        background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
        border-radius: 12px;
        padding: 1.5rem;
        border-left: 4px solid #16a34a;
        margin-bottom: 1rem;
    }
    .stats-container-blue {
        background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
        border-radius: 12px;
        padding: 1.5rem;
        border-left: 4px solid #2563eb;
        margin-bottom: 1rem;
    }
    .stats-container-amber {
        background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
        border-radius: 12px;
        padding: 1.5rem;
        border-left: 4px solid #d97706;
        margin-bottom: 1rem;
    }
    .stats-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: #1f2937;
        margin-bottom: 0.5rem;
    }
    .stats-subtitle {
        font-size: 0.85rem;
        color: #6b7280;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

if len(filtered_df) > 0:
    # Material consumption analytics
    consumption_data = filtered_df[filtered_df['consumed_parts_count'].notna()].copy()
    planned_data = filtered_df[filtered_df['planned_parts_count'].notna()].copy()

    col1, col2 = st.columns(2)

    with col1:
        with st.container(border=True):
            st.markdown("#### Material Consumption")

            if len(consumption_data) > 0:
                st.caption(f"C-Checks with data: {len(consumption_data)} / {len(filtered_df)} ({len(consumption_data)/len(filtered_df)*100:.1f}%)")

                # Parts statistics
                total_parts = consumption_data['consumed_parts_count'].sum()
                avg_parts = consumption_data['consumed_parts_count'].mean()
                median_parts = consumption_data['consumed_parts_count'].median()

                st.metric("Total Parts Consumed", format_number(total_parts))

                parts_stats_col1, parts_stats_col2 = st.columns(2)
                with parts_stats_col1:
                    st.metric("Avg Parts/C-Check", f"{avg_parts:.0f}")
                with parts_stats_col2:
                    st.metric("Median Parts/C-Check", f"{median_parts:.0f}")

                st.divider()

                # Cost statistics
                total_cost = consumption_data['consumed_cost'].sum()
                avg_cost = consumption_data['consumed_cost'].mean()
                median_cost = consumption_data['consumed_cost'].median()

                st.metric("Total Material Cost", format_currency(total_cost))

                cost_stats_col1, cost_stats_col2 = st.columns(2)
                with cost_stats_col1:
                    st.metric("Avg Cost/C-Check", format_currency(avg_cost))
                with cost_stats_col2:
                    st.metric("Median Cost/C-Check", format_currency(median_cost))
            else:
                st.info("No consumption data available for selected filters")

    with col2:
        with st.container(border=True):
            st.markdown("#### Planned Material")

            if len(planned_data) > 0:
                st.caption(f"C-Checks with data: {len(planned_data)} / {len(filtered_df)} ({len(planned_data)/len(filtered_df)*100:.1f}%)")

                # Parts statistics
                total_planned_parts = planned_data['planned_parts_count'].sum()
                avg_planned_parts = planned_data['planned_parts_count'].mean()
                median_planned_parts = planned_data['planned_parts_count'].median()

                st.metric("Total Parts Planned", format_number(total_planned_parts))

                planned_stats_col1, planned_stats_col2 = st.columns(2)
                with planned_stats_col1:
                    st.metric("Avg Parts/C-Check", f"{avg_planned_parts:.0f}")
                with planned_stats_col2:
                    st.metric("Median Parts/C-Check", f"{median_planned_parts:.0f}")

                st.divider()

                # Cost statistics
                total_planned_cost = planned_data['planned_cost'].sum()
                avg_planned_cost = planned_data['planned_cost'].mean()
                median_planned_cost = planned_data['planned_cost'].median()

                st.metric("Total Planned Cost", format_currency(total_planned_cost))

                planned_cost_col1, planned_cost_col2 = st.columns(2)
                with planned_cost_col1:
                    st.metric("Avg Cost/C-Check", format_currency(avg_planned_cost))
                with planned_cost_col2:
                    st.metric("Median Cost/C-Check", format_currency(median_planned_cost))
            else:
                st.info("No planned material data available for selected filters")

    # Variance analysis in its own container
    variance_data = filtered_df[
        (filtered_df['consumed_parts_count'].notna()) &
        (filtered_df['planned_parts_count'].notna())
    ].copy()

    if len(variance_data) > 0:
        with st.container(border=True):
            st.markdown("#### Variance Analysis (Planned vs Consumed)")

            col1, col2, col3 = st.columns(3)

            with col1:
                avg_parts_variance = variance_data['parts_variance'].mean()
                delta_color = "inverse" if avg_parts_variance < 0 else "normal"
                st.metric("Avg Parts Variance", f"{avg_parts_variance:+.0f}",
                         delta="Under planned" if avg_parts_variance < 0 else "Over planned",
                         delta_color=delta_color)

            with col2:
                avg_cost_variance = variance_data['cost_variance'].mean()
                delta_color = "inverse" if avg_cost_variance < 0 else "normal"
                st.metric("Avg Cost Variance", format_currency(avg_cost_variance),
                         delta="Under budget" if avg_cost_variance < 0 else "Over budget",
                         delta_color=delta_color)

            with col3:
                avg_accuracy = variance_data['planning_accuracy'].mean()
                st.metric("Avg Planning Accuracy", f"{avg_accuracy:.1f}%",
                         delta=f"{avg_accuracy - 100:+.1f}pp from target")

            st.divider()

            # Variance distribution
            st.markdown("##### Parts Variance Distribution")

            fig_variance = px.histogram(
                variance_data,
                x='parts_variance',
                nbins=20,
                title="Distribution of Parts Variance (Consumed - Planned)",
                labels={'parts_variance': 'Parts Variance', 'count': 'Frequency'}
            )

            fig_variance.add_vline(x=0, line_dash="dash", line_color="red", annotation_text="Perfect Planning")
            fig_variance.update_traces(marker_color='#2B3087')
            st.plotly_chart(fig_variance, use_container_width=True)
    else:
        st.info("No C-checks with both planned and consumed data for variance analysis")

st.markdown("---")
st.markdown("*Use the sidebar to navigate to other analysis pages*")
