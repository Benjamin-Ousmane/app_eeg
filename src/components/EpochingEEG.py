
import streamlit as st
import os
import matplotlib.pyplot as plt
import mne
import numpy as np
import pandas as pd

from src.functions import (
    epoch_data
)

def EpochingEEG(key="epoch-eeg"):
    """
    Component to Epoch EEG data.
    """

    # --- Global Inputs ---

    input_path = st.text_input(
        "Input FIF File Path",
        placeholder="Enter path to .fif file (e.g., subject_raw.fif)",
        help="Path to the raw converted .fif file",
        key=f"{key}-input"
    )
    if input_path.startswith('"') and input_path.endswith('"'):
        input_path = input_path[1:-1]
    elif input_path.startswith("'") and input_path.endswith("'"):
        input_path = input_path[1:-1]

    output_dir = st.text_input(
        "Output Directory",
        placeholder="Enter output directory ...",
        help="Directory to save the preprocessed file",
        key=f"{key}-output"
    )
    if output_dir.startswith('"') and output_dir.endswith('"'):
        output_dir = output_dir[1:-1]
    elif output_dir.startswith("'") and output_dir.endswith("'"):
        output_dir = output_dir[1:-1]

    # --- Parameters ---
    col1, col2, col3 = st.columns(3)
    with col1:
        param_tmin = st.number_input("Tmin (s)", value=-0.2, step=0.1, key=f"{key}-tmin")
    with col2:
        param_tmax = st.number_input("Tmax (s)", value=1.2, step=0.1, key=f"{key}-tmax")
    with col3:
        param_baseline = st.checkbox("Apply Baseline", value=False, key=f"{key}-base") # Default None in code, checkbox False = None?
        # Logic: if checked, use (None, 0)? Or use standard baseline? epoch.py uses cfg.erp_baseline which was None.
        # Let's assume unchecked = None.

    # --- Validation & Display ---
    is_valid = True
    raw = None
    
    if input_path:
        if not os.path.exists(input_path):
            st.error("Input file does not exist.")
            is_valid = False
        elif not input_path.lower().endswith('.fif'):
            st.error("Input file must end with .fif")
            is_valid = False
        else:
            try:
                # Load .fif file 
                raw = mne.io.read_raw_fif(input_path, preload=False, verbose=False)

                # Display .fif info
                col_info1, col_info2 = st.columns(2)
                with col_info1:
                    st.dataframe(pd.DataFrame({'Channel Name': raw.info['ch_names']}), hide_index=True, height=160)
                with col_info2:
                    st.write('Channels number: ', len(raw.info['ch_names']))
                    st.write('Highpass: ', raw.info['highpass'])
                    st.write('Lowpass: ', raw.info['lowpass'])
                    st.write('SFreq: ', raw.info['sfreq'])
            except Exception as e:
                st.error(f"Error loading FIF metadata: {e}")
                is_valid = False
            
    if output_dir and not os.path.exists(output_dir):
        st.warning("Output directory does not exist. It will be created if possible.")

    st.warning("Not implemented yet...")


