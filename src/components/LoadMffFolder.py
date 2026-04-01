
import streamlit as st
import os
import matplotlib.pyplot as plt
import numpy as np
import mne
import pandas as pd

from src.functions import assign_channels
from src.constants import loading_constants

def LoadMffFolder(key="load-mff"):
    """
    Component to load an MFF folder and convert it to .fif format.
    Input: Path to a single .mff folder (e.g., subject.mff)
    Output: Saves .fif file to output directory.
    """
    st.header("Load .mff Folder")

    # --- Inputs ---
    input_path = st.text_input(
        "Input MFF Folder Path",
        placeholder="Enter path to .mff folder ...",
        help="Path to a folder ending in .mff",
        key=f"{key}-input"
    )
    if input_path.startswith('"') and input_path.endswith('"'):
        input_path = input_path[1:-1]
    elif input_path.startswith("'") and input_path.endswith("'"):
        input_path = input_path[1:-1]

    output_dir = st.text_input(
        "Output Directory",
        placeholder="Enter path ...",
        help="Where to save the converted .fif file",
        key=f"{key}-output"
    )
    if output_dir.startswith('"') and output_dir.endswith('"'):
        output_dir = output_dir[1:-1]
    elif output_dir.startswith("'") and output_dir.endswith("'"):
        output_dir = output_dir[1:-1]

    # --- Validation ---
    is_valid = True
    if input_path:
        if not os.path.exists(input_path):
            st.error("Input path does not exist.")
            is_valid = False
        elif not input_path.lower().endswith('.mff'):
            st.error("Input path must end with .mff")
            is_valid = False
        elif not os.path.isdir(input_path):
            st.error("Input path is not a directory.")
            is_valid = False

    if output_dir:
        if not os.path.exists(output_dir):
            st.error("Output directory does not exist.")
            is_valid = False

    raw_preview = None
    if input_path and os.path.isdir(input_path) and is_valid:
        try:
            # Pre-load lightly to fetch channels
            raw_preview = mne.io.read_raw_egi(input_path, preload=False, verbose=False)
        except Exception as e:
            st.error(f"Failed to pre-load MFF to gather channels: {e}")
            is_valid = False
    
    # --- Advanced Settings (Dynamic mapping) ---
    st.markdown("### Mapping & Montage Definitions")
    
    # Initialize defaults
    default_mapping = loading_constants.MAPPING_TYPE
    default_montage = loading_constants.EEG_CHAN_NAMES
    
    mapping_dict = default_mapping
    montage_ch_names = default_montage
    
    if raw_preview:
        ch_names = raw_preview.ch_names
        
        # Step 1: Montage
        col_s1, col_s2 = st.columns([1, 4])
        with col_s1:
            do_montage = st.checkbox("1. Select eeg channels montage", disabled=True, value=True, key=f"{key}-do-montage")
        with col_s2:
            if do_montage:
                valid_defaults = [ch for ch in default_montage if ch in ch_names]
                montage_str = st.text_area(
                    "Sequence of EEG Channels for Coordinates Mapping (comma separated)",
                    value=", ".join(valid_defaults),
                    height=200,
                    help="Keep the exact order. Delete or add channels as strings separated by commas.",
                    key=f"{key}-montage-text"
                )
                montage_ch_names = [x.strip() for x in montage_str.split(",") if x.strip()]
        
        # Step 2: Mapping
        col_m1, col_m2 = st.columns([1, 4])
        with col_m1:
            do_mapping = st.checkbox("2. Channel types Mapping", disabled=True, value=True, help="Other than eeg channels", key=f"{key}-do-mapping")
        with col_m2:
            if do_mapping:
                mapping_df = pd.DataFrame(list(default_mapping.items()), columns=['Channel', 'Type'])
                
                edited_df = st.data_editor(
                    mapping_df, 
                    num_rows="dynamic", 
                    column_config={
                        'Type': st.column_config.SelectboxColumn(
                            "Type",
                            help="MNE Channel Type",
                            options=loading_constants.AVAILABLE_MAPPING_TYPES,
                            required=True
                        )
                    },
                    key=f"{key}-map-editor", 
                    width='stretch',
                    height=200
                )
                mapping_dict = dict(zip(edited_df['Channel'], edited_df['Type']))

        # Step 3: Plot Sensors
        col_p1, col_p2 = st.columns([1, 4])
        with col_p1:
            do_plot_sensors = st.checkbox("3. Plot Sensors", value=True, key=f"{key}-do-plot-sensors")
        
        # Step 4: Plot Channels
        col_c1, col_c2 = st.columns([1, 4])
        with col_c1:
            do_plot_raw = st.checkbox("4. Plot Channels", value=True, key=f"{key}-do-plot-raw")

    st.divider()

    # --- Processing ---
    # Convert disabled if required steps are unchecked
    is_ready = is_valid and do_montage and do_mapping
    if st.button("Convert to .fif", type="primary", disabled=not (input_path and output_dir and is_ready), key=f"{key}-btn"):
        
        subject_name = os.path.splitext(os.path.basename(os.path.normpath(input_path)))[0]
        st.info(f"Processing subject: {subject_name}")

        try:
            with st.spinner(f"Loading and converting {subject_name}..."):
                # True payload read
                raw_full = mne.io.read_raw_egi(input_path, preload=True, verbose=None)
                raw = assign_channels(raw_full, input_path, subject_name, mapping_dict, montage_ch_names)

            # Display info
            col_info1, col_info2 = st.columns(2)
            with col_info1:
                st.dataframe(pd.DataFrame({'Channel Name': raw.info['ch_names']}), hide_index=True, height=200)
            with col_info2:
                st.write('Channels number: ', len(raw.info['ch_names']))
                st.write('Highpass: ', raw.info['highpass'])
                st.write('Lowpass: ', raw.info['lowpass'])
                st.write('SFreq: ', raw.info['sfreq'])
            
            # --- Native Interactive Plotting ---
            if do_plot_sensors or do_plot_raw:
                st.info("Opening interactive windows on server... Check your taskbar.")
                
                # Save current backend to restore later
                orig_backend = plt.get_backend()
                try:
                    # Switch to interactive backend
                    try:
                        plt.switch_backend('Qt5Agg')
                    except:
                        try:
                            plt.switch_backend('TkAgg')
                        except:
                            pass

                    # 1. 3D Sensors (Blocking)
                    if do_plot_sensors:
                        fig_3d = raw.plot_sensors(kind='3d')
                        plt.show(block=True)

                    # 2. Raw Signal Plot (Blocking)
                    if do_plot_raw:
                        picks = mne.pick_types(raw.info, eeg=True, ecg=True, emg=True, stim=True, eog=True, exclude=[])
                        raw.plot(show_options=True, block=True, picks=picks)

                except Exception as e:
                    st.error(f"Failed to open native plots: {e}")
                
                finally:
                    # Restore backend (best effort)
                    try:
                        plt.switch_backend(orig_backend)
                    except:
                        pass

            # Save
            save_name = f"{subject_name}_raw.fif"
            save_path = os.path.join(output_dir, save_name)
            with st.spinner(f"Saving to {save_path}..."):
                raw.save(save_path, overwrite=True)
            
            st.toast(f"✅ Saved {save_name}")
            st.success(f"Successfully loaded and saved to `{save_path}`")
            
        except Exception as e:
            st.error(f"❌ Error loading {subject_name}: {e}")
