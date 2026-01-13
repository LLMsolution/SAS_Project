"""
SAS Material Supply Analysis - Data Loader Module
Handles loading data from session state (uploaded files)
"""

import streamlit as st
import pandas as pd
import numpy as np


def is_data_uploaded():
    """Check if all required data files have been uploaded"""
    required_keys = [
        'uploaded_workpacks',
        'uploaded_utilization',
        'uploaded_consumption',
        'uploaded_planned'
    ]
    return all(key in st.session_state and st.session_state[key] is not None for key in required_keys)


def get_missing_uploads():
    """Get list of files that haven't been uploaded yet"""
    files = {
        'uploaded_workpacks': 'Maintenance Workpacks',
        'uploaded_utilization': 'Aircraft Utilization',
        'uploaded_consumption': 'Material Consumption',
        'uploaded_planned': 'Planned Material'
    }
    missing = []
    for key, name in files.items():
        if key not in st.session_state or st.session_state[key] is None:
            missing.append(name)
    return missing


def show_upload_required():
    """Show message that data upload is required"""
    st.error("Data not available")
    st.markdown("Please upload all required files on the **Data Upload** page first.")
    missing = get_missing_uploads()
    if missing:
        st.markdown("**Missing files:**")
        for name in missing:
            st.markdown(f"- {name}")
    st.stop()


@st.cache_data
def load_workpacks():
    """
    Load maintenance workpacks from session state
    Returns: DataFrame with workpacks or None
    """
    if 'uploaded_workpacks' not in st.session_state or st.session_state['uploaded_workpacks'] is None:
        return None

    try:
        df = st.session_state['uploaded_workpacks'].copy()

        # Convert dates
        df['start_date'] = pd.to_datetime(df['start_date'], errors='coerce')
        df['end_date'] = pd.to_datetime(df['end_date'], errors='coerce')

        # Calculate duration
        df['duration_days'] = (df['end_date'] - df['start_date']).dt.total_seconds() / (24*3600)

        # Ensure required boolean columns exist
        if 'is_eol' not in df.columns:
            df['is_eol'] = 0
        if 'is_bridging_task' not in df.columns:
            df['is_bridging_task'] = 0

        return df

    except Exception as e:
        st.error(f"Error processing workpacks: {str(e)}")
        return None


@st.cache_data
def load_utilization():
    """
    Load aircraft utilization data from session state
    Returns: DataFrame with utilization data or None
    """
    if 'uploaded_utilization' not in st.session_state or st.session_state['uploaded_utilization'] is None:
        return None

    try:
        df = st.session_state['uploaded_utilization'].copy()

        # Convert date
        df['date'] = pd.to_datetime(df['date'], errors='coerce')

        return df

    except Exception as e:
        st.error(f"Error processing utilization: {str(e)}")
        return None


@st.cache_data
def load_consumption():
    """
    Load material consumption data from session state
    Filters for consumables (AA, EA, AS, ES) and rotables (YA, YE)
    Returns: DataFrame aggregated by wpno_i with date/station validation
    """
    if 'uploaded_consumption' not in st.session_state or st.session_state['uploaded_consumption'] is None:
        return None

    try:
        df = st.session_state['uploaded_consumption'].copy()

        # Convert dates
        df['del_date'] = pd.to_datetime(df['del_date'], errors='coerce')

        # Filter for consumables (AA, EA, AS, ES) and rotables (YA, YE)
        consumable_modes = ['AA', 'EA', 'AS', 'ES']
        rotable_modes = ['YA', 'YE']

        df_filtered = df[df['vm'].isin(consumable_modes + rotable_modes)].copy()

        # Separate consumables and rotables
        df_filtered['material_category'] = df_filtered['vm'].apply(
            lambda x: 'consumable' if x in consumable_modes else 'rotable'
        )

        # Remove rows without wpno_i for direct matching
        df_clean = df_filtered[df_filtered['wpno_i'].notna()].copy()

        if len(df_clean) == 0:
            return None

        # Aggregate by workpack with date and station info
        agg_df = df_clean.groupby('wpno_i').agg({
            'partno': 'count',
            'qty': lambda x: abs(x).sum(),
            'average_price': 'sum',
            'del_date': ['min', 'max'],
            'station': lambda x: x.mode()[0] if len(x.mode()) > 0 else x.iloc[0]
        }).reset_index()

        agg_df.columns = ['wpno_i', 'consumed_parts_count', 'consumed_qty', 'consumed_cost',
                          'consumption_start_date', 'consumption_end_date', 'consumption_station']

        # Calculate average price per part
        agg_df['consumed_avg_price'] = agg_df['consumed_cost'] / agg_df['consumed_parts_count']

        return agg_df

    except Exception as e:
        st.error(f"Error processing consumption: {str(e)}")
        return None


@st.cache_data
def load_consumption_detailed():
    """
    Load detailed material consumption from session state
    Returns: DataFrame with all consumption records
    """
    if 'uploaded_consumption' not in st.session_state or st.session_state['uploaded_consumption'] is None:
        return None

    try:
        df = st.session_state['uploaded_consumption'].copy()
        df['del_date'] = pd.to_datetime(df['del_date'], errors='coerce')

        # Filter for consumables (AA, EA, AS, ES) and rotables (YA, YE)
        consumable_modes = ['AA', 'EA', 'AS', 'ES']
        rotable_modes = ['YA', 'YE']

        df_filtered = df[df['vm'].isin(consumable_modes + rotable_modes)].copy()

        # Add material category
        df_filtered['material_category'] = df_filtered['vm'].apply(
            lambda x: 'consumable' if x in consumable_modes else 'rotable'
        )

        return df_filtered

    except Exception as e:
        st.error(f"Error processing detailed consumption: {str(e)}")
        return None


@st.cache_data
def load_planned_material():
    """
    Load planned material data from session state
    Returns: DataFrame aggregated by wpno_i
    """
    if 'uploaded_planned' not in st.session_state or st.session_state['uploaded_planned'] is None:
        return None

    try:
        df = st.session_state['uploaded_planned'].copy()

        # Remove rows without wpno_i
        df_clean = df[df['wpno_i'].notna()].copy()

        # Ensure confirmed_qty exists
        if 'confirmed_qty' not in df_clean.columns:
            df_clean['confirmed_qty'] = 0

        # Aggregate by workpack
        agg_df = df_clean.groupby('wpno_i').agg({
            'partno': 'count',
            'qty': 'sum',
            'confirmed_qty': 'sum',
            'average_price': 'sum',
        }).reset_index()

        agg_df.columns = ['wpno_i', 'planned_parts_count', 'planned_qty', 'planned_confirmed_qty', 'planned_cost']

        # Calculate average price per part
        agg_df['planned_avg_price'] = agg_df['planned_cost'] / agg_df['planned_parts_count']

        return agg_df

    except Exception as e:
        st.error(f"Error processing planned material: {str(e)}")
        return None


@st.cache_data
def load_planned_material_detailed():
    """
    Load detailed planned material from session state
    Returns: DataFrame with all planned material records
    """
    if 'uploaded_planned' not in st.session_state or st.session_state['uploaded_planned'] is None:
        return None

    try:
        df = st.session_state['uploaded_planned'].copy()

        # Ensure optional columns exist
        if 'description' not in df.columns:
            df['description'] = ''
        if 'confirmed_qty' not in df.columns:
            df['confirmed_qty'] = 0
        if 'tool' not in df.columns:
            df['tool'] = ''
        if 'mat_class' not in df.columns:
            df['mat_class'] = ''
        if 'externally_provisioned' not in df.columns:
            df['externally_provisioned'] = 'N'

        return df

    except Exception as e:
        st.error(f"Error processing detailed planned material: {str(e)}")
        return None


def match_consumption_to_workpacks(workpacks_df, consumption_detail_df):
    """
    Match consumption to workpacks using two strategies:
    1. Direct match on wpno_i (when available)
    2. Time-based match on del_date + station + receiver/aircraft (when wpno_i is missing)
    """
    if consumption_detail_df is None or len(consumption_detail_df) == 0:
        return None

    # Prepare consumption data
    consumption = consumption_detail_df.copy()
    consumption['del_date'] = pd.to_datetime(consumption['del_date'], errors='coerce')

    matched_consumption = []

    # Strategy 1: Direct match on wpno_i (for rows that have wpno_i)
    consumption_with_wpno = consumption[consumption['wpno_i'].notna()].copy()

    if len(consumption_with_wpno) > 0:
        for wpno in workpacks_df['wpno_i'].unique():
            if pd.isna(wpno):
                continue

            matches = consumption_with_wpno[consumption_with_wpno['wpno_i'] == wpno]

            if len(matches) > 0:
                agg = {
                    'wpno_i': wpno,
                    'consumed_parts_count': len(matches),
                    'consumed_qty': matches['qty'].abs().sum(),
                    'consumed_cost': matches['average_price'].sum(),
                    'consumption_start_date': matches['del_date'].min(),
                    'consumption_end_date': matches['del_date'].max(),
                    'consumption_station': matches['station'].mode()[0] if len(matches['station'].mode()) > 0 else matches['station'].iloc[0],
                    'consumption_matched_by': 'WPNO_I',
                    'consumable_parts_count': len(matches[matches['material_category'] == 'consumable']),
                    'rotable_parts_count': len(matches[matches['material_category'] == 'rotable']),
                    'consumable_cost': matches[matches['material_category'] == 'consumable']['average_price'].sum(),
                    'rotable_cost': matches[matches['material_category'] == 'rotable']['average_price'].sum(),
                }
                matched_consumption.append(agg)

    # Strategy 2: Time-based matching for rows without wpno_i
    consumption_no_wpno = consumption[consumption['wpno_i'].isna()].copy()

    if len(consumption_no_wpno) > 0:
        for idx, wp in workpacks_df.iterrows():
            if pd.isna(wp['start_date']) or pd.isna(wp['end_date']):
                continue

            # Skip if already matched by wpno_i
            if any(m['wpno_i'] == wp['wpno_i'] and m['consumption_matched_by'] == 'WPNO_I' for m in matched_consumption):
                continue

            # Find consumption that matches this workpack by time + station + receiver/aircraft
            matches = consumption_no_wpno[
                (consumption_no_wpno['del_date'] >= wp['start_date']) &
                (consumption_no_wpno['del_date'] <= wp['end_date']) &
                (consumption_no_wpno['station'] == wp['station'])
            ]

            # Additional filters by receiver or aircraft
            if pd.notna(wp['ac_registr']) and 'ac_registr' in consumption_no_wpno.columns:
                ac_matches = matches[matches['ac_registr'] == wp['ac_registr']]
                if len(ac_matches) > 0:
                    matches = ac_matches
                elif 'receiver' in matches.columns:
                    receiver_matches = matches[matches['receiver'].str.contains(wp['ac_registr'], na=False, case=False)]
                    if len(receiver_matches) > 0:
                        matches = receiver_matches

            if len(matches) > 0:
                agg = {
                    'wpno_i': wp['wpno_i'],
                    'consumed_parts_count': len(matches),
                    'consumed_qty': matches['qty'].abs().sum(),
                    'consumed_cost': matches['average_price'].sum(),
                    'consumption_start_date': matches['del_date'].min(),
                    'consumption_end_date': matches['del_date'].max(),
                    'consumption_station': matches['station'].mode()[0] if len(matches['station'].mode()) > 0 else matches['station'].iloc[0],
                    'consumption_matched_by': 'TIME+STATION+RECEIVER',
                    'consumable_parts_count': len(matches[matches['material_category'] == 'consumable']),
                    'rotable_parts_count': len(matches[matches['material_category'] == 'rotable']),
                    'consumable_cost': matches[matches['material_category'] == 'consumable']['average_price'].sum(),
                    'rotable_cost': matches[matches['material_category'] == 'rotable']['average_price'].sum(),
                }
                matched_consumption.append(agg)

    if len(matched_consumption) > 0:
        return pd.DataFrame(matched_consumption)
    else:
        return None


def get_master_view():
    """
    Create a master view by joining all datasets
    Returns: DataFrame with workpacks + utilization + consumption + planned
    """
    # Check if data is uploaded
    if not is_data_uploaded():
        return None

    # Load all datasets
    workpacks = load_workpacks()
    utilization = load_utilization()
    consumption_detail = load_consumption_detailed()
    planned = load_planned_material()

    if workpacks is None:
        return None

    # Start with workpacks
    master = workpacks.copy()

    # Add latest utilization data
    if utilization is not None:
        master = add_utilization_data(master, utilization)

    # Add consumption data - MATCHED BY TIME + STATION
    if consumption_detail is not None:
        consumption_matched = match_consumption_to_workpacks(master, consumption_detail)

        if consumption_matched is not None:
            master = master.merge(consumption_matched, on='wpno_i', how='left')
            master['consumption_validated'] = master['consumed_parts_count'].notna()
        else:
            master['consumed_parts_count'] = np.nan
            master['consumed_qty'] = np.nan
            master['consumed_cost'] = np.nan
            master['consumption_validated'] = False

    # Add planned material data
    if planned is not None:
        master = master.merge(planned, on='wpno_i', how='left')

    # Calculate variances
    master['parts_variance'] = master['consumed_parts_count'] - master['planned_parts_count']
    master['qty_variance'] = master['consumed_qty'] - master['planned_qty']
    master['cost_variance'] = master['consumed_cost'] - master['planned_cost']

    # Calculate planning accuracy
    master['planning_accuracy'] = np.where(
        (master['planned_parts_count'] > 0) & (master['consumed_parts_count'].notna()),
        (1 - abs(master['parts_variance']) / master['planned_parts_count']) * 100,
        np.nan
    )

    return master


def add_utilization_data(workpacks_df, utilization_df):
    """
    Add latest utilization data (hours, cycles) to workpacks
    """
    def get_latest_util(row):
        ac_registr = row['ac_registr']
        start_date = row['start_date']

        if pd.isna(ac_registr) or pd.isna(start_date):
            return pd.Series({'aircraft_hours': np.nan, 'aircraft_cycles': np.nan})

        ac_util = utilization_df[utilization_df['ac_registr'] == ac_registr].copy()

        if len(ac_util) == 0:
            return pd.Series({'aircraft_hours': np.nan, 'aircraft_cycles': np.nan})

        ac_util = ac_util[ac_util['date'] <= start_date]

        if len(ac_util) == 0:
            ac_util = utilization_df[utilization_df['ac_registr'] == ac_registr].copy()
            ac_util = ac_util.sort_values('date')
            if len(ac_util) > 0:
                latest = ac_util.iloc[0]
                return pd.Series({'aircraft_hours': latest['tah'], 'aircraft_cycles': latest['tac']})
            return pd.Series({'aircraft_hours': np.nan, 'aircraft_cycles': np.nan})

        latest = ac_util.sort_values('date', ascending=False).iloc[0]
        return pd.Series({'aircraft_hours': latest['tah'], 'aircraft_cycles': latest['tac']})

    util_data = workpacks_df.apply(get_latest_util, axis=1)
    workpacks_df['aircraft_hours'] = util_data['aircraft_hours']
    workpacks_df['aircraft_cycles'] = util_data['aircraft_cycles']
    workpacks_df['hours_per_cycle'] = workpacks_df['aircraft_hours'] / workpacks_df['aircraft_cycles']

    return workpacks_df


def get_data_completeness():
    """
    Get statistics about data completeness
    Returns: dict with completeness metrics or None if data not uploaded
    """
    if not is_data_uploaded():
        return None

    master = get_master_view()

    if master is None:
        return None

    total = len(master)
    c_checks = len(master[master['is_c_check'] == 1])

    return {
        'total_workpacks': total,
        'c_checks': c_checks,
        'with_utilization': (master['aircraft_hours'].notna().sum() / total * 100),
        'with_consumption': (master['consumed_parts_count'].notna().sum() / total * 100),
        'with_planned': (master['planned_parts_count'].notna().sum() / total * 100),
        'c_checks_with_consumption': master[master['is_c_check'] == 1]['consumed_parts_count'].notna().sum(),
        'c_checks_with_planned': master[master['is_c_check'] == 1]['planned_parts_count'].notna().sum(),
    }


def get_consumption_by_category():
    """
    Get separate statistics for consumables and rotables
    Returns: dict with consumable and rotable metrics or None if data not uploaded
    """
    if not is_data_uploaded():
        return None

    consumption_detail = load_consumption_detailed()

    if consumption_detail is None or len(consumption_detail) == 0:
        return None

    consumables = consumption_detail[consumption_detail['material_category'] == 'consumable']
    rotables = consumption_detail[consumption_detail['material_category'] == 'rotable']

    vm_counts = consumption_detail['vm'].value_counts().to_dict()

    return {
        'total_records': len(consumption_detail),
        'consumable_records': len(consumables),
        'rotable_records': len(rotables),
        'consumable_cost': consumables['average_price'].sum(),
        'rotable_cost': rotables['average_price'].sum(),
        'consumable_qty': consumables['qty'].abs().sum(),
        'rotable_qty': rotables['qty'].abs().sum(),
        'voucher_mode_counts': vm_counts,
        'records_with_wpno_i': consumption_detail['wpno_i'].notna().sum(),
        'records_without_wpno_i': consumption_detail['wpno_i'].isna().sum(),
    }
