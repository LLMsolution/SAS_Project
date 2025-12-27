"""
SAS Material Supply Analysis - Parts Comparison Page
Detailed comparison of planned vs consumed parts per workpackage
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
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
st.title("Parts Comparison")
st.markdown("Detailed comparison of planned vs consumed parts for each C-check")

# Load data
with st.spinner("Loading data..."):
    master_df = get_master_view()
    consumption_detail = load_consumption_detailed()
    planned_detail = load_planned_material_detailed()

if master_df is None:
    st.error("Could not load data")
    st.stop()

# Filter to C-checks only with both planned and consumed data
c_checks = master_df[
    (master_df['is_c_check'] == 1) &
    (master_df['consumed_parts_count'].notna()) &
    (master_df['planned_parts_count'].notna())
].copy()

st.markdown(f"**C-Checks with both planned and consumed data:** {len(c_checks)} out of {len(master_df[master_df['is_c_check'] == 1])} total")

if len(c_checks) == 0:
    st.warning("No C-checks found with both planned and consumed material data")
    st.stop()

# Sidebar: C-Check Selector
st.sidebar.markdown("## Select C-Check")

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

# C-Check Summary
st.markdown("### Selected C-Check Summary")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Planned Parts", int(selected_check['planned_parts_count']))

with col2:
    st.metric(
        "Consumed Parts",
        int(selected_check['consumed_parts_count']),
        delta=int(selected_check['parts_variance']) if pd.notna(selected_check['parts_variance']) else None
    )

with col3:
    if pd.notna(selected_check['planning_accuracy']):
        accuracy = selected_check['planning_accuracy']
        st.metric("Planning Accuracy", f"{accuracy:.1f}%")

with col4:
    if pd.notna(selected_check['consumption_validated']):
        validated = selected_check['consumption_validated']
        if validated:
            st.success("Data Validated")
        else:
            st.warning("Data Issues")
            if not selected_check['consumption_date_valid']:
                st.caption("Date mismatch")
            if not selected_check['consumption_station_valid']:
                st.caption("Station mismatch")
    else:
        st.info("No validation")

st.markdown("---")

# Load detailed parts data
planned_parts = None
consumed_parts = None

if planned_detail is not None:
    planned_parts = planned_detail[planned_detail['wpno_i'] == selected_check['wpno_i']].copy()

if consumption_detail is not None:
    consumed_parts = consumption_detail[consumption_detail['wpno_i'] == selected_check['wpno_i']].copy()

if planned_parts is None or consumed_parts is None or len(planned_parts) == 0 or len(consumed_parts) == 0:
    st.error("Could not load detailed parts data for this C-check")
    st.stop()

# Part-level comparison
st.markdown("### Part-Level Comparison")

# Merge planned and consumed by part number
planned_summary = planned_parts.groupby('partno').agg({
    'description': 'first',
    'qty': 'sum',
    'average_price': 'sum',
    'tool': 'first',
    'mat_class': 'first'
}).reset_index()
planned_summary.columns = ['partno', 'description', 'planned_qty', 'planned_cost', 'tool', 'mat_class']

# Filter only consumed parts (negative qty means consumed/used)
consumed_used = consumed_parts[consumed_parts['qty'] < 0].copy()
consumed_used['consumed_qty'] = consumed_used['qty'].abs()  # Make positive

consumed_summary = consumed_used.groupby('partno').agg({
    'consumed_qty': 'sum',
    'average_price': 'sum',  # average_price is already total price
    'ata_chapter': 'first'
}).reset_index()
consumed_summary.columns = ['partno', 'consumed_qty', 'consumed_cost', 'ata_chapter']

# Full outer join to catch all parts
comparison = planned_summary.merge(consumed_summary, on='partno', how='outer')

# Fill NaN
comparison['planned_qty'] = comparison['planned_qty'].fillna(0)
comparison['planned_cost'] = comparison['planned_cost'].fillna(0)
comparison['consumed_qty'] = comparison['consumed_qty'].fillna(0)
comparison['consumed_cost'] = comparison['consumed_cost'].fillna(0)

# Calculate variances
comparison['qty_variance'] = comparison['consumed_qty'] - comparison['planned_qty']
comparison['cost_variance'] = comparison['consumed_cost'] - comparison['planned_cost']

# Categorize parts
def categorize_part(row):
    if row['planned_qty'] > 0 and row['consumed_qty'] > 0:
        return 'Both (Planned & Consumed)'
    elif row['planned_qty'] > 0 and row['consumed_qty'] == 0:
        return 'Planned Only (Not Used)'
    elif row['planned_qty'] == 0 and row['consumed_qty'] > 0:
        return 'Used (Not Planned)'
    else:
        return 'Unknown'

comparison['category'] = comparison.apply(categorize_part, axis=1)

# Remove Unknown category (should not exist with valid data)
comparison = comparison[comparison['category'] != 'Unknown']

# Summary statistics
st.markdown("#### Summary Statistics")

col1, col2, col3, col4 = st.columns(4)

with col1:
    both_count = len(comparison[comparison['category'] == 'Both (Planned & Consumed)'])
    st.metric("Parts: Both", both_count)

with col2:
    planned_only = len(comparison[comparison['category'] == 'Planned Only (Not Used)'])
    st.metric("Parts: Planned Only", planned_only)

with col3:
    consumed_only = len(comparison[comparison['category'] == 'Used (Not Planned)'])
    st.metric("Parts: Used Only", consumed_only)

with col4:
    total_parts = len(comparison)
    st.metric("Total Unique Parts", total_parts)

# Visual breakdown
st.markdown("#### Category Breakdown")

category_counts = comparison['category'].value_counts().reset_index()
category_counts.columns = ['Category', 'Count']

fig_category = px.pie(
    category_counts,
    values='Count',
    names='Category',
    title="Parts Distribution by Category",
    color_discrete_sequence=['#2B3087', '#FFA500', '#FF6B6B']
)

st.plotly_chart(fig_category, width='stretch')

st.markdown("---")

# Cost Impact Analysis (moved to top for prominence)
st.markdown("### Cost Impact Analysis")
st.markdown("Overall cost variance between planned and consumed materials")

total_over = comparison[comparison['cost_variance'] > 0]['cost_variance'].sum()
total_under = abs(comparison[comparison['cost_variance'] < 0]['cost_variance'].sum())
net_variance = comparison['cost_variance'].sum()

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Total Over-Consumption", f"€{total_over:,.2f}")

with col2:
    st.metric("Total Under-Consumption", f"€{total_under:,.2f}")

with col3:
    variance_pct = (net_variance / comparison['planned_cost'].sum() * 100) if comparison['planned_cost'].sum() > 0 else 0
    st.metric(
        "Net Cost Variance",
        f"€{net_variance:,.2f}",
        delta=f"{variance_pct:+.1f}%"
    )

# Waterfall chart for cost breakdown
st.markdown("#### Cost Breakdown: Planned vs Consumed")

col1, col2 = st.columns(2)

with col1:
    # Stacked bar comparing planned vs consumed by category
    cost_by_category = comparison.groupby('category').agg({
        'planned_cost': 'sum',
        'consumed_cost': 'sum'
    }).reset_index()

    fig_cost_category = go.Figure()

    fig_cost_category.add_trace(go.Bar(
        name='Planned',
        x=cost_by_category['category'],
        y=cost_by_category['planned_cost'],
        marker_color='#2B3087'
    ))

    fig_cost_category.add_trace(go.Bar(
        name='Consumed',
        x=cost_by_category['category'],
        y=cost_by_category['consumed_cost'],
        marker_color='#FFA500'
    ))

    fig_cost_category.update_layout(
        title="Planned vs Consumed Cost by Category",
        barmode='group',
        xaxis_title="Category",
        yaxis_title="Cost (EUR)",
        showlegend=True
    )

    st.plotly_chart(fig_cost_category, use_container_width=True)

with col2:
    # Variance distribution
    variance_data = comparison[comparison['cost_variance'] != 0].copy()

    if len(variance_data) > 0:
        fig_variance = px.histogram(
            variance_data,
            x='cost_variance',
            nbins=30,
            title="Cost Variance Distribution",
            labels={'cost_variance': 'Cost Variance (EUR)', 'count': 'Parts Count'},
            color_discrete_sequence=['#2B3087']
        )

        fig_variance.add_vline(x=0, line_dash="dash", line_color="red", annotation_text="Perfect Match")

        st.plotly_chart(fig_variance, use_container_width=True)
    else:
        st.info("No variance data available")

st.markdown("---")

# Matching Parts Analysis (Both Planned AND Consumed)
st.markdown("### Matching Parts Analysis")
st.markdown("Parts that were **both planned AND actually consumed**")

matching_parts = comparison[comparison['category'] == 'Both (Planned & Consumed)'].copy()

if len(matching_parts) > 0:
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Matching Parts", len(matching_parts))

    with col2:
        match_accuracy = (matching_parts['consumed_qty'] / matching_parts['planned_qty']).mean() * 100
        st.metric("Avg Qty Accuracy", f"{match_accuracy:.1f}%")

    with col3:
        total_match_value = matching_parts['consumed_cost'].sum()
        st.metric("Total Matching Cost", f"€{total_match_value:,.0f}")

    # Visualizations for matching parts
    st.markdown("#### Matching Parts Visualizations")

    col1, col2 = st.columns(2)

    with col1:
        # Top 10 matching parts by cost
        top_matching_chart = matching_parts.nlargest(10, 'consumed_cost').copy()

        fig_top_matching = go.Figure()

        fig_top_matching.add_trace(go.Bar(
            name='Planned Cost',
            x=top_matching_chart['partno'],
            y=top_matching_chart['planned_cost'],
            marker_color='#2B3087'
        ))

        fig_top_matching.add_trace(go.Bar(
            name='Consumed Cost',
            x=top_matching_chart['partno'],
            y=top_matching_chart['consumed_cost'],
            marker_color='#FFA500'
        ))

        fig_top_matching.update_layout(
            title="Top 10 Matching Parts: Planned vs Consumed Cost",
            xaxis_title="Part Number",
            yaxis_title="Cost (EUR)",
            barmode='group',
            showlegend=True
        )

        st.plotly_chart(fig_top_matching, use_container_width=True)

    with col2:
        # Accuracy distribution for matching parts
        matching_parts['accuracy_pct'] = (matching_parts['consumed_qty'] / matching_parts['planned_qty'] * 100).clip(0, 200)

        fig_accuracy_dist = px.histogram(
            matching_parts,
            x='accuracy_pct',
            nbins=20,
            title="Quantity Accuracy Distribution",
            labels={'accuracy_pct': 'Accuracy (%)', 'count': 'Parts Count'},
            color_discrete_sequence=['#2B3087']
        )

        fig_accuracy_dist.add_vline(x=100, line_dash="dash", line_color="green", annotation_text="Perfect Match")

        st.plotly_chart(fig_accuracy_dist, use_container_width=True)

else:
    st.info("No matching parts found (no parts were both planned and consumed)")

st.markdown("---")

# Planned Material Insights
st.markdown("### Planned Material Insights")

if planned_parts is not None and len(planned_parts) > 0:
    st.markdown("#### Stock & Provisioning Analysis")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        confirmed_count = (planned_parts['confirmed_qty'] > 0).sum()
        st.metric("Parts Confirmed", confirmed_count)

    with col2:
        confirmed_pct = (planned_parts['confirmed_qty'] > 0).sum() / len(planned_parts) * 100
        st.metric("Confirmation Rate", f"{confirmed_pct:.1f}%")

    with col3:
        if 'externally_provisioned' in planned_parts.columns:
            external_count = (planned_parts['externally_provisioned'] == 'Y').sum()
            st.metric("Externally Provisioned", external_count)
        else:
            st.metric("Externally Provisioned", "N/A")

    with col4:
        if 'externally_provisioned' in planned_parts.columns:
            external_pct = (planned_parts['externally_provisioned'] == 'Y').sum() / len(planned_parts) * 100
            st.metric("External Rate", f"{external_pct:.1f}%")
        else:
            st.metric("External Rate", "N/A")

    # Qty vs Confirmed Qty Analysis
    st.markdown("#### Planned Qty vs Confirmed Qty")

    planned_summary_full = planned_parts.groupby('partno').agg({
        'description': 'first',
        'qty': 'sum',
        'confirmed_qty': 'sum',
        'externally_provisioned': 'first',
        'average_price': 'sum'
    }).reset_index()

    planned_summary_full['confirmation_gap'] = planned_summary_full['qty'] - planned_summary_full['confirmed_qty']
    planned_summary_full['confirmation_rate'] = (planned_summary_full['confirmed_qty'] / planned_summary_full['qty'] * 100).fillna(0)

    # Show parts with confirmation gaps
    st.markdown("##### Top 10 Parts with Largest Confirmation Gap")

    gap_parts = planned_summary_full[planned_summary_full['confirmation_gap'] > 0].nlargest(10, 'confirmation_gap')[[
        'partno', 'description', 'qty', 'confirmed_qty', 'confirmation_gap',
        'externally_provisioned', 'average_price'
    ]].copy()

    if len(gap_parts) > 0:
        gap_parts['externally_provisioned'] = gap_parts['externally_provisioned'].fillna('N')
        gap_parts['description'] = gap_parts['description'].fillna('N/A')
        gap_parts['average_price'] = gap_parts['average_price'].apply(lambda x: f"€{x:,.2f}")

        gap_parts.columns = [
            'Part Number', 'Description', 'Planned Qty', 'Confirmed Qty', 'Gap',
            'External', 'Cost'
        ]

        st.dataframe(
            gap_parts,
            width='stretch',
            hide_index=True
        )

        # Summary of gap
        total_gap = planned_summary_full['confirmation_gap'].sum()
        total_planned = planned_summary_full['qty'].sum()
        gap_pct = (total_gap / total_planned * 100) if total_planned > 0 else 0

        st.info(f"**Total Confirmation Gap:** {total_gap:.0f} parts ({gap_pct:.1f}% of total planned)")
    else:
        st.success("All planned parts were confirmed!")

    # Externally provisioned breakdown
    if 'externally_provisioned' in planned_parts.columns:
        st.markdown("##### External vs Internal Provisioning")

        external_breakdown = planned_parts.groupby('externally_provisioned').agg({
            'partno': 'count',
            'average_price': 'sum'
        }).reset_index()

        external_breakdown.columns = ['External', 'Part Count', 'Total Cost']
        external_breakdown['External'] = external_breakdown['External'].fillna('N')

        col1, col2 = st.columns(2)

        with col1:
            fig_external = px.pie(
                external_breakdown,
                values='Part Count',
                names='External',
                title="Parts Count: External vs Internal",
                color_discrete_sequence=['#FFA500', '#2B3087']
            )
            st.plotly_chart(fig_external, width='stretch')

        with col2:
            fig_external_cost = px.pie(
                external_breakdown,
                values='Total Cost',
                names='External',
                title="Cost: External vs Internal",
                color_discrete_sequence=['#FFA500', '#2B3087']
            )
            st.plotly_chart(fig_external_cost, width='stretch')

else:
    st.info("No planned material data available for this C-check")

st.markdown("---")

# Detailed comparison table with filters
st.markdown("### Detailed Parts Table")

# Visualizations before table
st.markdown("#### Parts Overview Visualizations")

col1, col2 = st.columns(2)

with col1:
    # Treemap of parts by cost
    treemap_data = comparison.nlargest(20, 'consumed_cost').copy()

    fig_treemap = px.treemap(
        treemap_data,
        path=['category', 'partno'],
        values='consumed_cost',
        title="Top 20 Parts by Consumed Cost (Treemap)",
        color='cost_variance',
        color_continuous_scale=['#2B3087', '#FFFFFF', '#FF6B6B'],
        color_continuous_midpoint=0
    )

    st.plotly_chart(fig_treemap, use_container_width=True)

with col2:
    # Sunburst of category breakdown
    fig_sunburst = px.sunburst(
        comparison,
        path=['category'],
        values='consumed_cost',
        title="Cost Distribution by Category (Sunburst)",
        color_discrete_sequence=['#2B3087', '#FFA500', '#FF6B6B']
    )

    st.plotly_chart(fig_sunburst, use_container_width=True)

# Top over/under consumed parts side by side
st.markdown("#### Top Over/Under Consumed Parts")

col1, col2 = st.columns(2)

with col1:
    over_consumed = comparison[comparison['cost_variance'] > 0].nlargest(10, 'cost_variance')

    if len(over_consumed) > 0:
        fig_over = px.bar(
            over_consumed,
            x='partno',
            y='cost_variance',
            title="Top 10 Over-Consumed Parts",
            labels={'cost_variance': 'Extra Cost (EUR)', 'partno': 'Part Number'},
            color_discrete_sequence=['#FF6B6B']
        )

        st.plotly_chart(fig_over, use_container_width=True)
    else:
        st.info("No over-consumed parts")

with col2:
    under_consumed = comparison[comparison['cost_variance'] < 0].nsmallest(10, 'cost_variance')

    if len(under_consumed) > 0:
        fig_under = px.bar(
            under_consumed,
            x='partno',
            y='cost_variance',
            title="Top 10 Under-Consumed Parts",
            labels={'cost_variance': 'Saved Cost (EUR)', 'partno': 'Part Number'},
            color_discrete_sequence=['#2B3087']
        )

        st.plotly_chart(fig_under, use_container_width=True)
    else:
        st.info("No under-consumed parts")

st.markdown("#### Filter and Sort Options")

# Filters
col1, col2 = st.columns(2)

with col1:
    selected_category = st.selectbox(
        "Filter by Category",
        ['All'] + sorted(comparison['category'].unique().tolist())
    )

with col2:
    sort_by = st.selectbox(
        "Sort by",
        ['Cost Variance (Descending)', 'Cost Variance (Ascending)',
         'Planned Cost (Descending)', 'Consumed Cost (Descending)',
         'Qty Variance (Absolute)']
    )

# Apply filter
filtered_comparison = comparison.copy()
if selected_category != 'All':
    filtered_comparison = filtered_comparison[filtered_comparison['category'] == selected_category]

# Apply sorting
if sort_by == 'Cost Variance (Descending)':
    filtered_comparison = filtered_comparison.sort_values('cost_variance', ascending=False)
elif sort_by == 'Cost Variance (Ascending)':
    filtered_comparison = filtered_comparison.sort_values('cost_variance', ascending=True)
elif sort_by == 'Planned Cost (Descending)':
    filtered_comparison = filtered_comparison.sort_values('planned_cost', ascending=False)
elif sort_by == 'Consumed Cost (Descending)':
    filtered_comparison = filtered_comparison.sort_values('consumed_cost', ascending=False)
elif sort_by == 'Qty Variance (Absolute)':
    filtered_comparison['abs_qty_var'] = filtered_comparison['qty_variance'].abs()
    filtered_comparison = filtered_comparison.sort_values('abs_qty_var', ascending=False)

# Format display table
display_comparison = filtered_comparison[[
    'partno', 'description', 'category',
    'planned_qty', 'consumed_qty', 'qty_variance',
    'planned_cost', 'consumed_cost', 'cost_variance',
    'ata_chapter', 'mat_class'
]].copy()

display_comparison['planned_cost'] = display_comparison['planned_cost'].apply(lambda x: f"€{x:,.2f}")
display_comparison['consumed_cost'] = display_comparison['consumed_cost'].apply(lambda x: f"€{x:,.2f}")
display_comparison['cost_variance'] = display_comparison['cost_variance'].apply(lambda x: f"€{x:,.2f}")
display_comparison['description'] = display_comparison['description'].fillna('N/A')
display_comparison['ata_chapter'] = display_comparison['ata_chapter'].fillna('N/A')
display_comparison['mat_class'] = display_comparison['mat_class'].fillna('N/A')

display_comparison.columns = [
    'Part Number', 'Description', 'Category',
    'Planned Qty', 'Consumed Qty', 'Qty Variance',
    'Planned Cost', 'Consumed Cost', 'Cost Variance',
    'ATA Chapter', 'Material Class'
]

st.dataframe(
    display_comparison,
    width='stretch',
    hide_index=True
)

st.markdown(f"**Showing {len(filtered_comparison)} out of {len(comparison)} parts**")

st.markdown("---")
st.markdown("*Use the sidebar to select different C-checks or navigate to other pages*")
