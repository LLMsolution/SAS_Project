"""
SAS Material Supply Analysis - Feature Engineering Module
Creates features for ML model training
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder


def create_ml_features(master_df):
    """
    Create features for ML model from master dataset

    Args:
        master_df: Master dataframe with all joined data

    Returns:
        X: Feature dataframe
        y: Target variable (consumed_parts_count)
        feature_names: List of feature names
    """
    # Filter to rows with consumption data (for training)
    df = master_df[master_df['consumed_parts_count'].notna()].copy()

    if len(df) == 0:
        return None, None, None

    # Feature list
    features = []

    # 1. Aircraft type (encoded)
    le_ac_typ = LabelEncoder()
    df['ac_typ_encoded'] = le_ac_typ.fit_transform(df['ac_typ'].fillna('Unknown'))
    features.append('ac_typ_encoded')

    # 2. Aircraft utilization
    df['aircraft_hours_filled'] = df['aircraft_hours'].fillna(df['aircraft_hours'].median())
    df['aircraft_cycles_filled'] = df['aircraft_cycles'].fillna(df['aircraft_cycles'].median())
    df['hours_per_cycle_filled'] = df['hours_per_cycle'].fillna(df['hours_per_cycle'].median())
    features.extend(['aircraft_hours_filled', 'aircraft_cycles_filled', 'hours_per_cycle_filled'])

    # 3. EOL flag
    df['is_eol_filled'] = df['is_eol'].fillna(0)
    features.append('is_eol_filled')

    # 5. Station (encoded)
    le_station = LabelEncoder()
    df['station_encoded'] = le_station.fit_transform(df['station'].fillna('Unknown'))
    features.append('station_encoded')

    # 6. Duration
    df['duration_days_filled'] = df['duration_days'].fillna(df['duration_days'].median())
    features.append('duration_days_filled')

    # 7. Planned material (if available)
    df['planned_parts_count_filled'] = df['planned_parts_count'].fillna(0)
    df['planned_cost_filled'] = df['planned_cost'].fillna(0)
    features.extend(['planned_parts_count_filled', 'planned_cost_filled'])

    # Target variable
    y = df['consumed_parts_count']

    # Feature matrix
    X = df[features]

    # Store encoders for later use
    encoders = {
        'ac_typ': le_ac_typ,
        'station': le_station
    }

    return X, y, features, encoders, df


def categorize_check_type(check_type_str):
    """
    Categorize check type into simplified categories
    """
    if pd.isna(check_type_str):
        return 'Unknown'

    check_str = str(check_type_str).lower()

    if '6' in check_str or '72' in check_str:
        return '6-year'
    elif '4' in check_str or '48' in check_str:
        return '4-year'
    elif '2' in check_str or '24' in check_str:
        return '2-year'
    else:
        return 'Other'


def prepare_prediction_features(input_data, encoders, feature_names):
    """
    Prepare features for prediction from user input

    Args:
        input_data: dict with user inputs
        encoders: dict of label encoders
        feature_names: list of feature names

    Returns:
        DataFrame with features ready for prediction
    """
    # Create empty dataframe with correct columns
    X_new = pd.DataFrame(columns=feature_names)

    # Aircraft type
    try:
        ac_typ_encoded = encoders['ac_typ'].transform([input_data.get('ac_typ', 'A320S')])[0]
    except:
        ac_typ_encoded = 0
    X_new.loc[0, 'ac_typ_encoded'] = ac_typ_encoded

    # Utilization
    X_new.loc[0, 'aircraft_hours_filled'] = input_data.get('aircraft_hours', 10000)
    X_new.loc[0, 'aircraft_cycles_filled'] = input_data.get('aircraft_cycles', 5000)
    X_new.loc[0, 'hours_per_cycle_filled'] = input_data.get('aircraft_hours', 10000) / max(input_data.get('aircraft_cycles', 5000), 1)

    # EOL
    X_new.loc[0, 'is_eol_filled'] = 1 if input_data.get('is_eol', False) else 0

    # Station
    try:
        station_encoded = encoders['station'].transform([input_data.get('station', 'TLLM')])[0]
    except:
        station_encoded = 0
    X_new.loc[0, 'station_encoded'] = station_encoded

    # Duration (use input or default to median)
    X_new.loc[0, 'duration_days_filled'] = input_data.get('duration_days', 18)

    # Planned material (use 0 for prediction if not provided)
    X_new.loc[0, 'planned_parts_count_filled'] = input_data.get('planned_parts_count', 0)
    X_new.loc[0, 'planned_cost_filled'] = input_data.get('planned_cost', 0)

    return X_new


def get_feature_importance_names(feature_names, encoders):
    """
    Get human-readable feature names
    """
    name_map = {
        'ac_typ_encoded': 'Aircraft Type',
        'aircraft_hours_filled': 'Aircraft Hours',
        'aircraft_cycles_filled': 'Aircraft Cycles',
        'hours_per_cycle_filled': 'Hours per Cycle',
        'is_eol_filled': 'End of Lease',
        'station_encoded': 'Station',
        'duration_days_filled': 'Duration (days)',
        'planned_parts_count_filled': 'Planned Parts Count',
        'planned_cost_filled': 'Planned Cost',
    }

    return [name_map.get(f, f) for f in feature_names]
