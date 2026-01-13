"""
SAS Material Supply Analysis - Data Upload Page
Upload required Excel files to use the application
"""

import streamlit as st
import pandas as pd
import warnings
import sys

# Suppress warnings
if not sys.warnoptions:
    warnings.simplefilter("ignore")
warnings.filterwarnings('ignore')

# Apply shared SAS styling
from utils.styling import apply_sas_styling
apply_sas_styling()

# Page config
st.title("Data Upload")
st.markdown("Upload de 4 vereiste Excel bestanden in één keer")

# Define required files and their columns
REQUIRED_FILES = {
    'workpacks': {
        'name': 'Maintenance Workpacks',
        'description': 'C-checks, EOL en bridging tasks',
        'required_columns': ['wpno_i', 'wpno', 'ac_registr', 'ac_typ', 'station',
                            'start_date', 'end_date', 'is_c_check'],
        'session_key': 'uploaded_workpacks'
    },
    'utilization': {
        'name': 'Aircraft Utilization',
        'description': 'Vliegtuig uren en cycles',
        'required_columns': ['ac_registr', 'date', 'tah', 'tac'],
        'session_key': 'uploaded_utilization'
    },
    'consumption': {
        'name': 'Material Consumption',
        'description': 'Werkelijke materiaalconsumptie',
        'required_columns': ['partno', 'qty', 'average_price', 'del_date', 'station', 'vm'],
        'session_key': 'uploaded_consumption'
    },
    'planned': {
        'name': 'Planned Material',
        'description': 'Geplande materialen per workpack',
        'required_columns': ['wpno_i', 'partno', 'qty', 'average_price'],
        'session_key': 'uploaded_planned'
    }
}


def detect_file_type(df):
    """Auto-detect which dataset type a file is based on its columns"""
    df_cols = set(df.columns.tolist())

    # Check each file type - order matters (most specific first)
    # Workpacks has unique columns like 'is_c_check', 'end_date'
    if 'is_c_check' in df_cols and 'wpno' in df_cols:
        return 'workpacks'

    # Utilization has 'tah', 'tac' which are unique
    if 'tah' in df_cols and 'tac' in df_cols:
        return 'utilization'

    # Consumption has 'vm', 'del_date' which are unique
    if 'vm' in df_cols and 'del_date' in df_cols:
        return 'consumption'

    # Planned has 'partno' and 'wpno_i' but not 'vm' or 'del_date'
    if 'partno' in df_cols and 'wpno_i' in df_cols and 'vm' not in df_cols:
        return 'planned'

    return None


def validate_columns(df, required_columns):
    """Check if dataframe has all required columns"""
    missing = [col for col in required_columns if col not in df.columns]
    return missing


def get_upload_status():
    """Get upload status for all files"""
    status = {}
    for key, config in REQUIRED_FILES.items():
        status[key] = config['session_key'] in st.session_state and st.session_state[config['session_key']] is not None
    return status


# Show overall status
st.markdown("---")
st.markdown("### Upload Status")

status = get_upload_status()
all_uploaded = all(status.values())

cols = st.columns(4)
for i, (key, config) in enumerate(REQUIRED_FILES.items()):
    with cols[i]:
        if status[key]:
            st.success(f"{config['name']}")
        else:
            st.error(f"{config['name']}")

if all_uploaded:
    st.success("Alle bestanden zijn geupload. Je kunt nu de andere pagina's gebruiken.")
else:
    st.warning("Upload alle 4 bestanden om de applicatie te gebruiken.")

st.markdown("---")

# Single multi-file uploader
st.markdown("### Upload Bestanden")
st.markdown("Selecteer alle 4 Excel bestanden tegelijk. Het systeem detecteert automatisch welk bestand wat is.")

uploaded_files = st.file_uploader(
    "Selecteer 4 Excel bestanden (.xlsx)",
    type=['xlsx'],
    accept_multiple_files=True,
    key="multi_uploader"
)

if uploaded_files:
    # Process all files
    with st.spinner("Bestanden worden verwerkt..."):
        results = []
        files_to_store = {}

        for uploaded_file in uploaded_files:
            try:
                df = pd.read_excel(uploaded_file)
                file_type = detect_file_type(df)

                if file_type is None:
                    results.append({
                        'file': uploaded_file.name,
                        'status': 'error',
                        'message': 'Kon bestandstype niet detecteren op basis van kolommen'
                    })
                else:
                    config = REQUIRED_FILES[file_type]
                    missing = validate_columns(df, config['required_columns'])

                    if missing:
                        results.append({
                            'file': uploaded_file.name,
                            'status': 'error',
                            'message': f"Ontbrekende kolommen voor {config['name']}: {', '.join(missing)}"
                        })
                    else:
                        files_to_store[config['session_key']] = df
                        results.append({
                            'file': uploaded_file.name,
                            'status': 'success',
                            'message': f"Herkend als: {config['name']} ({len(df)} rijen)"
                        })

            except Exception as e:
                results.append({
                    'file': uploaded_file.name,
                    'status': 'error',
                    'message': f"Fout bij laden: {str(e)}"
                })

        # Show results
        st.markdown("#### Resultaten:")
        for result in results:
            if result['status'] == 'success':
                st.success(f"**{result['file']}**: {result['message']}")
            else:
                st.error(f"**{result['file']}**: {result['message']}")

        # Store all successful files at once
        if files_to_store:
            for key, df in files_to_store.items():
                st.session_state[key] = df

            # Check if we have new uploads
            new_status = get_upload_status()
            if new_status != status:
                st.rerun()

# Show what files are expected
st.markdown("---")
st.markdown("### Verwachte Bestanden")

for key, config in REQUIRED_FILES.items():
    with st.expander(f"{config['name']} - {config['description']}"):
        st.markdown("**Vereiste kolommen:**")
        st.code(", ".join(config['required_columns']))

# Clear all data button
st.markdown("---")
if st.button("Wis alle data", type="secondary"):
    for config in REQUIRED_FILES.values():
        if config['session_key'] in st.session_state:
            del st.session_state[config['session_key']]
    st.rerun()

st.markdown("---")
st.markdown("*Na het uploaden van alle bestanden, gebruik de sidebar om naar de analyse pagina's te navigeren.*")
