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

# Page config
st.title("Data Upload")
st.markdown("Upload de vereiste Excel bestanden om de applicatie te gebruiken")

# Define required files and their columns
REQUIRED_FILES = {
    'workpacks': {
        'name': 'Maintenance Workpacks',
        'description': 'C-checks, EOL en bridging tasks',
        'required_columns': ['wpno_i', 'wpno', 'ac_registr', 'ac_typ', 'station',
                            'start_date', 'end_date', 'is_c_check'],
        'optional_columns': ['check_type', 'is_eol', 'is_bridging_task'],
        'session_key': 'uploaded_workpacks'
    },
    'utilization': {
        'name': 'Aircraft Utilization',
        'description': 'Vliegtuig uren en cycles',
        'required_columns': ['ac_registr', 'date', 'tah', 'tac'],
        'optional_columns': [],
        'session_key': 'uploaded_utilization'
    },
    'consumption': {
        'name': 'Material Consumption',
        'description': 'Werkelijke materiaalconsumptie',
        'required_columns': ['partno', 'qty', 'average_price', 'del_date', 'station', 'vm'],
        'optional_columns': ['wpno_i', 'ac_registr', 'receiver', 'ata_chapter'],
        'session_key': 'uploaded_consumption'
    },
    'planned': {
        'name': 'Planned Material',
        'description': 'Geplande materialen per workpack',
        'required_columns': ['wpno_i', 'partno', 'qty', 'average_price'],
        'optional_columns': ['description', 'confirmed_qty', 'tool', 'mat_class', 'externally_provisioned'],
        'session_key': 'uploaded_planned'
    }
}


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

# Upload sections
for key, config in REQUIRED_FILES.items():
    with st.container(border=True):
        col1, col2 = st.columns([3, 1])

        with col1:
            st.markdown(f"### {config['name']}")
            st.caption(config['description'])

        with col2:
            if status[key]:
                st.success("Geupload")
            else:
                st.error("Niet geupload")

        # Show required columns
        st.markdown("**Vereiste kolommen:**")
        st.code(", ".join(config['required_columns']))

        if config['optional_columns']:
            st.markdown("**Optionele kolommen:**")
            st.code(", ".join(config['optional_columns']))

        # File uploader
        uploaded_file = st.file_uploader(
            f"Upload {config['name']} (.xlsx)",
            type=['xlsx'],
            key=f"uploader_{key}"
        )

        if uploaded_file is not None:
            try:
                df = pd.read_excel(uploaded_file)

                # Validate columns
                missing = validate_columns(df, config['required_columns'])

                if missing:
                    st.error(f"Ontbrekende kolommen: {', '.join(missing)}")
                    st.markdown("**Gevonden kolommen:**")
                    st.code(", ".join(df.columns.tolist()))
                else:
                    # Store in session state
                    st.session_state[config['session_key']] = df
                    st.success(f"Bestand succesvol geladen: {len(df)} rijen")

                    # Show preview
                    with st.expander("Preview data"):
                        st.dataframe(df.head(10), use_container_width=True)

            except Exception as e:
                st.error(f"Fout bij laden: {str(e)}")

# Clear all data button
st.markdown("---")
if st.button("Wis alle data", type="secondary"):
    for config in REQUIRED_FILES.values():
        if config['session_key'] in st.session_state:
            del st.session_state[config['session_key']]
    st.rerun()

st.markdown("---")
st.markdown("*Na het uploaden van alle bestanden, gebruik de sidebar om naar de analyse pagina's te navigeren.*")
