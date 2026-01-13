"""
SAS Material Supply Analysis - Material Prediction Page
Predict material needs for future C-checks using ML model
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

# Import utilities
from utils.data_loader import get_master_view, is_data_uploaded, show_upload_required
from utils.ml_model import get_trained_model, find_similar_checks
from utils.plotly_utils import hide_warnings_css
from utils import format_currency

# Hide warnings with CSS
hide_warnings_css()

# Page config
st.title("Material Prediction")
st.markdown("Predict material requirements for future C-checks")

# Check if data is uploaded
if not is_data_uploaded():
    show_upload_required()

# Load data and model
with st.spinner("Loading model and data..."):
    master_df = get_master_view()
    model = get_trained_model()

if master_df is None:
    st.error("Could not load data")
    st.stop()

if model is None:
    st.error("Could not load or train prediction model")
    st.stop()

# Sidebar: Input Form
st.sidebar.markdown("## New C-Check Details")

# Aircraft Selection
c_checks = master_df[master_df['is_c_check'] == 1].copy()
aircraft_list = sorted(c_checks['ac_registr'].unique().tolist())

input_mode = st.sidebar.radio(
    "Input Method",
    ["Select Existing Aircraft", "Manual Input"]
)

if input_mode == "Select Existing Aircraft":
    selected_aircraft = st.sidebar.selectbox("Aircraft Registration", aircraft_list)

    # Get latest data for this aircraft
    aircraft_data = c_checks[c_checks['ac_registr'] == selected_aircraft].sort_values('start_date', ascending=False)

    if len(aircraft_data) > 0:
        latest = aircraft_data.iloc[0]
        ac_typ = latest['ac_typ']
        aircraft_hours = latest['aircraft_hours'] if pd.notna(latest['aircraft_hours']) else 10000
        aircraft_cycles = latest['aircraft_cycles'] if pd.notna(latest['aircraft_cycles']) else 5000
    else:
        ac_typ = "A320S"
        aircraft_hours = 10000
        aircraft_cycles = 5000
else:
    # Manual input
    ac_typ = st.sidebar.selectbox(
        "Aircraft Type",
        sorted(c_checks['ac_typ'].unique().tolist())
    )

    aircraft_hours = st.sidebar.number_input(
        "Aircraft Hours",
        min_value=0,
        max_value=100000,
        value=10000,
        step=1000
    )

    aircraft_cycles = st.sidebar.number_input(
        "Aircraft Cycles",
        min_value=0,
        max_value=50000,
        value=5000,
        step=500
    )

# Check details
stations = sorted(c_checks['station'].unique().tolist())
station = st.sidebar.selectbox("Station", stations)

is_eol = st.sidebar.checkbox("End of Lease (EOL)")

# Optional: Planned material data
st.sidebar.markdown("---")
st.sidebar.markdown("**Optional: Planned Material**")
has_planned = st.sidebar.checkbox("I have planned material data")

planned_parts_count = 0
planned_cost = 0

if has_planned:
    planned_parts_count = st.sidebar.number_input(
        "Planned Parts Count",
        min_value=0,
        max_value=10000,
        value=0,
        step=10
    )

    planned_cost = st.sidebar.number_input(
        "Planned Cost (EUR)",
        min_value=0,
        max_value=10000000,
        value=0,
        step=10000
    )

# Predict button
st.sidebar.markdown("---")
predict_button = st.sidebar.button("Predict Material Requirements", type="primary")

# Main content
if predict_button:
    st.markdown("---")
    st.markdown("### Prediction Results")

    # Prepare input data
    input_data = {
        'ac_typ': ac_typ,
        'aircraft_hours': aircraft_hours,
        'aircraft_cycles': aircraft_cycles,
        'station': station,
        'is_eol': is_eol,
        'planned_parts_count': planned_parts_count if has_planned else 0,
        'planned_cost': planned_cost if has_planned else 0
    }

    # Get prediction
    prediction = model.predict_with_fallback(
        input_data,
        planned_parts=planned_parts_count if has_planned and planned_parts_count > 0 else None
    )

    if prediction:
        # Display prediction
        with st.container(border=True):
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric(
                    "Predicted Parts Count",
                    f"{prediction['prediction']}",
                    delta=f"Range: {prediction['ci_lower']}-{prediction['ci_upper']}"
                )

            with col2:
                # Estimate cost (based on historical average cost per part)
                avg_cost_per_part = master_df[
                    (master_df['is_c_check'] == 1) &
                    (master_df['consumed_parts_count'].notna()) &
                    (master_df['consumed_cost'].notna())
                ]['consumed_cost'].mean() / master_df[
                    (master_df['is_c_check'] == 1) &
                    (master_df['consumed_parts_count'].notna())
                ]['consumed_parts_count'].mean()

                estimated_cost = prediction['prediction'] * avg_cost_per_part

                st.metric(
                    "Estimated Total Cost",
                    format_currency(estimated_cost),
                    delta=f"Approx. {format_currency(avg_cost_per_part)} per part"
                )

            with col3:
                confidence_color = "green" if prediction['confidence'] > 70 else "orange" if prediction['confidence'] > 50 else "red"
                st.markdown(f"**Confidence Score**")
                st.markdown(f"<span style='color:{confidence_color}; font-size:32px; font-weight:bold;'>{prediction['confidence']:.0f}%</span>", unsafe_allow_html=True)

            st.divider()

            # Method used
            st.info(f"**Prediction Method:** {prediction['method']}")
            st.markdown(f"*{prediction['explanation']}*")

        st.markdown("---")

        # Model information
        col1, col2 = st.columns(2)

        with col1:
            with st.container(border=True):
                st.markdown("#### Model Information")
                st.markdown(f"**Model Type:** Random Forest Regressor")
                st.markdown(f"**Training Samples:** {model.training_stats['n_samples']} C-checks")

                if 'cv_mean_r2' in model.training_stats:
                    r2_score = model.training_stats['cv_mean_r2']
                    st.markdown(f"**Model Accuracy (R²):** {r2_score:.2f}")

                st.markdown(f"**Training Range:** {model.training_stats['training_min']:.0f} - {model.training_stats['training_max']:.0f} parts")
                st.markdown(f"**Training Average:** {model.training_stats['training_mean']:.0f} parts")

        with col2:
            with st.container(border=True):
                st.markdown("#### Confidence Interpretation")

                if prediction['confidence'] > 70:
                    st.success("**High Confidence** - Strong historical data supports this prediction")
                elif prediction['confidence'] > 50:
                    st.warning("**Medium Confidence** - Moderate historical data available")
                else:
                    st.error("**Low Confidence** - Limited historical data for this scenario")

                st.markdown("""
                **Factors affecting confidence:**
                - Amount of similar historical C-checks
                - Availability of planned material data
                - Model training data quality
                - Aircraft type and check type representation
                """)

        st.markdown("---")

        # Feature importance
        st.markdown("#### Feature Importance")
        st.markdown("Factors that influence material requirements the most:")

        feature_importance = model.get_feature_importance()

        if feature_importance is not None:
            # Top 10 features
            top_features = feature_importance.head(10)

            fig_importance = px.bar(
                top_features,
                x='importance',
                y='feature',
                orientation='h',
                title="Top 10 Most Important Features",
                color='importance',
                color_continuous_scale='Blues'
            )

            fig_importance.update_layout(
                showlegend=False,
                xaxis_title="Importance Score",
                yaxis_title="Feature"
            )

            st.plotly_chart(fig_importance, width='stretch')

        st.markdown("---")

        # Similar historical C-checks
        st.markdown("#### Similar Historical C-Checks")
        st.markdown("These C-checks have similar characteristics to your input:")

        similar_checks = find_similar_checks(input_data, master_df, n_similar=5)

        if similar_checks is not None and len(similar_checks) > 0:
            # Display similar checks
            display_similar = similar_checks[[
                'wpno', 'ac_registr', 'ac_typ', 'station',
                'consumed_parts_count', 'consumed_cost', 'similarity_score'
            ]].copy()

            display_similar.columns = [
                'Workpack', 'Aircraft', 'Type', 'Station',
                'Parts Count', 'Cost', 'Similarity %'
            ]

            display_similar['Cost'] = display_similar['Cost'].apply(lambda x: f"€{x:,.0f}" if pd.notna(x) else "N/A")
            display_similar['Similarity %'] = display_similar['Similarity %'].apply(lambda x: f"{x:.0f}%")

            st.dataframe(
                display_similar,
                width='stretch',
                hide_index=True
            )

            # Statistics from similar checks
            if similar_checks['consumed_parts_count'].notna().sum() > 0:
                avg_similar = similar_checks['consumed_parts_count'].mean()
                st.markdown(f"**Average parts from similar checks:** {avg_similar:.0f}")

                # Comparison with prediction
                diff = prediction['prediction'] - avg_similar
                diff_pct = (diff / avg_similar * 100) if avg_similar > 0 else 0

                if abs(diff_pct) < 10:
                    st.success(f"Prediction is very close to similar historical checks ({diff_pct:+.1f}%)")
                elif abs(diff_pct) < 20:
                    st.info(f"Prediction differs moderately from similar checks ({diff_pct:+.1f}%)")
                else:
                    st.warning(f"Prediction differs significantly from similar checks ({diff_pct:+.1f}%)")
        else:
            st.info("No similar historical C-checks found")

        st.markdown("---")

        # Recommendations
        st.markdown("#### Recommendations")

        st.markdown("""
        **Based on this prediction, we recommend:**

        1. **Material Preload Planning**
           - Prepare approximately {0} parts for this C-check
           - Budget approximately €{1:,.0f} for material costs
           - Build in a buffer of ±{2} parts for uncertainty

        2. **Review Similar Cases**
           - Examine the similar C-checks listed above
           - Identify common parts and patterns
           - Learn from previous material planning experiences

        3. **Monitor During Execution**
           - Track actual consumption against prediction
           - Update planning factors based on actual results
           - Continuously improve prediction accuracy

        4. **Data Quality**
           - Record actual consumption data for this C-check
           - Document any deviations from prediction
           - Help improve future predictions
        """.format(
            prediction['prediction'],
            estimated_cost,
            int((prediction['ci_upper'] - prediction['ci_lower']) / 2)
        ))
    else:
        st.error("Could not generate prediction. Please check your inputs.")

else:
    # Initial state - show instructions
    st.markdown("""
    ### How to Use Material Prediction

    **Step 1: Enter C-Check Details**
    - Use the sidebar to input details about the planned C-check
    - You can select an existing aircraft or enter details manually

    **Step 2: Optional Planned Material**
    - If you already have planned material data, include it for better accuracy
    - This will be used to adjust the prediction

    **Step 3: Get Prediction**
    - Click "Predict Material Requirements" to get the prediction
    - Review the results, confidence score, and similar historical cases

    **Understanding the Results:**
    - **Prediction:** Estimated number of parts needed
    - **Confidence:** How reliable the prediction is (based on historical data)
    - **Method:** Whether ML model or fallback method was used
    - **Similar Checks:** Historical C-checks with similar characteristics

    **Note:** The prediction is based on historical C-check data from SAS. Only 18% of C-checks have
    consumption data, so predictions include confidence scores and use multiple methods for reliability.
    """)

    # Model statistics
    st.markdown("---")
    st.markdown("### Model Statistics")

    with st.container(border=True):
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Training Samples", f"{model.training_stats['n_samples']} C-checks")

        with col2:
            if 'cv_mean_r2' in model.training_stats:
                r2 = model.training_stats['cv_mean_r2']
                st.metric("Model Accuracy (R²)", f"{r2:.2f}")

        with col3:
            st.metric("Model Type", "Random Forest")

        st.divider()

        st.markdown(f"""
        **Training Data Range:**
        - Minimum: {model.training_stats['training_min']:.0f} parts
        - Average: {model.training_stats['training_mean']:.0f} parts
        - Maximum: {model.training_stats['training_max']:.0f} parts
        """)

st.markdown("---")
st.markdown("*Use the sidebar to navigate to other analysis pages*")
