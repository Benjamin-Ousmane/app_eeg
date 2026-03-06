
import streamlit as st
import os
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.functions import load_mff

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

    output_dir = st.text_input(
        "Output Directory",
        placeholder="Enter path ...",
        help="Where to save the converted .fif file",
        key=f"{key}-output"
    )

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

    
    # --- Processing ---
    if st.button("Convert to .fif", type="primary", disabled=not (input_path and output_dir and is_valid), key=f"{key}-btn"):
        
        subject_name = os.path.splitext(os.path.basename(os.path.normpath(input_path)))[0]
        st.info(f"Processing subject: {subject_name}")

        try:
            with st.spinner(f"Loading and converting {subject_name}..."):
                raw = load_mff(input_path, subject_name)

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
                fig_3d = raw.plot_sensors(kind='3d', ch_type='eeg', show=False)
                plt.show(block=True)

                # 2. Raw Signal Plot (Blocking)
                raw.plot(show_options=True, block=True)

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
