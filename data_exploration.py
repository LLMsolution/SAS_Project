"""
SAS Material Supply Analysis - Data Exploration Script
Author: Data Analysis Team
Purpose: Inspect datasets and understand structure before transformation
"""

import pandas as pd
import numpy as np
import os
from pathlib import Path

# Set display options for better readability
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', 50)

# Define file paths
base_path = Path(r"C:\Users\jesse\Documents\Aviation Opleiding\SAS_Project")
files = {
    'maintenance_workpacks': base_path / 'maintenance_workpacks filtered.xlsx',
    'aircraft_utilization': base_path / 'aircraft_utilization.xlsx',
    'material_consumption': base_path / 'material_consumption.xlsx',
    'planned_material': base_path / 'planned_material_on_workpacks.xlsx'
}

def inspect_dataset(file_path, dataset_name):
    """
    Inspect a dataset and print key information
    """
    print(f"\n{'='*80}")
    print(f"DATASET: {dataset_name}")
    print(f"{'='*80}")

    try:
        # Read the file
        df = pd.read_excel(file_path)

        # Basic info
        print(f"\nShape: {df.shape[0]} rows × {df.shape[1]} columns")
        print(f"\nColumn Names and Types:")
        print(df.dtypes)

        # Show first few rows
        print(f"\nFirst 5 rows:")
        print(df.head())

        # Missing values
        print(f"\nMissing Values:")
        missing = df.isnull().sum()
        if missing.sum() > 0:
            print(missing[missing > 0])
        else:
            print("No missing values")

        # For maintenance workpacks, show unique values in key columns
        if 'maintenance_workpacks' in dataset_name.lower():
            print(f"\n--- MAINTENANCE WORKPACKS SPECIFIC ANALYSIS ---")

            # Try to find description-like columns
            desc_columns = [col for col in df.columns if 'desc' in col.lower() or 'description' in col.lower()]
            if desc_columns:
                print(f"\nDescription columns found: {desc_columns}")
                for col in desc_columns:
                    print(f"\nSample values from '{col}':")
                    print(df[col].value_counts().head(10))

            # Try to find station/location columns
            station_columns = [col for col in df.columns if 'station' in col.lower() or 'location' in col.lower()]
            if station_columns:
                print(f"\nStation/Location columns found: {station_columns}")
                for col in station_columns:
                    print(f"\nUnique values in '{col}':")
                    print(df[col].value_counts())

            # Try to find aircraft type columns
            aircraft_columns = [col for col in df.columns if 'aircraft' in col.lower() or 'type' in col.lower() or 'registration' in col.lower()]
            if aircraft_columns:
                print(f"\nAircraft-related columns found: {aircraft_columns}")
                for col in aircraft_columns[:3]:  # Limit to first 3 to avoid clutter
                    print(f"\nUnique values in '{col}':")
                    print(df[col].value_counts())

        return df

    except Exception as e:
        print(f"Error reading {dataset_name}: {str(e)}")
        return None

def main():
    """
    Main exploration function
    """
    print("="*80)
    print("SAS MATERIAL SUPPLY ANALYSIS - DATA EXPLORATION")
    print("="*80)

    # Store dataframes for later use
    dataframes = {}

    # Inspect each dataset
    for name, path in files.items():
        if path.exists():
            df = inspect_dataset(path, name)
            if df is not None:
                dataframes[name] = df
        else:
            print(f"\nWarning: File not found - {path}")

    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"\nDatasets loaded: {len(dataframes)}/{len(files)}")
    for name, df in dataframes.items():
        print(f"  - {name}: {df.shape[0]} rows × {df.shape[1]} columns")

    return dataframes

if __name__ == "__main__":
    datasets = main()
