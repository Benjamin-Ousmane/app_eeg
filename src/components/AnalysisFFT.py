import streamlit as st
import os
import pandas as pd
import matplotlib.pyplot as plt
import mne

from src.functions import analyze_fft
from src.constants.fft_constants import DEFAULT_ROI_ANT, DEFAULT_ROI_POST
from src.constants import CHANNEL_CODES

def AnalysisFFT(key="analysis-fft"):
    """
    Component to compute and extract relative PSD from an epoched FIF file.
    """
    st.markdown("### FFT Relative Power Extraction")

    # --- Global Inputs ---
    input_path = st.text_input(
        "Input FIF File Path",
        placeholder="Enter path to epoched .fif file (e.g., subject_epoch.fif)",
        help="Path to the epoched .fif file",
        key=f"{key}-input"
    )
    if input_path.startswith('"') and input_path.endswith('"'):
        input_path = input_path[1:-1]
    elif input_path.startswith("'") and input_path.endswith("'"):
        input_path = input_path[1:-1]

    output_dir = st.text_input(
        "Output Directory",
        placeholder="Enter output directory ...",
        help="Directory to save the resulting Excel file",
        key=f"{key}-output"
    )
    if output_dir.startswith('"') and output_dir.endswith('"'):
        output_dir = output_dir[1:-1]
    elif output_dir.startswith("'") and output_dir.endswith("'"):
        output_dir = output_dir[1:-1]

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
                # Load .fif metadata 
                raw_info = mne.io.read_info(input_path, verbose=False)

                # Display .fif info
                col_info1, col_info2 = st.columns(2)
                with col_info1:
                    st.dataframe(pd.DataFrame({'Channel Name': raw_info['ch_names']}), hide_index=True, height=160)
                with col_info2:
                    st.write('Channels number: ', len(raw_info['ch_names']))
                    st.write('Highpass: ', raw_info['highpass'])
                    st.write('Lowpass: ', raw_info['lowpass'])
                    st.write('SFreq: ', raw_info['sfreq'])
            except Exception as e:
                st.error(f"Error loading FIF metadata: {e}")
                is_valid = False
            
    if output_dir and not os.path.exists(output_dir):
        st.warning("Output directory does not exist. It will be created if possible.")

    # --- Parameters ---
    st.markdown("---")
    st.markdown("#### Extraction Parameters")

    # 1. Plot Epochs
    col_p1, col_p2 = st.columns([1, 4])
    with col_p1:
        do_plot_epochs = st.checkbox("Plot Epochs", value=False, help="Ouvrira une fenêtre MNE pour inspecter visuellement les epochs utilisées.", key=f"{key}-do-plot")

    # 2. ROIs setup
    col_r1, col_r2 = st.columns([1, 4])
    with col_r1:
        do_roi_analysis = st.checkbox("ROI Definitions", value=True, key=f"{key}-do-roi")
    with col_r2:
        with st.expander("Regions of Interest Setup", expanded=do_roi_analysis):
            if do_roi_analysis:
                nb_rois = st.number_input("Number of ROIs", min_value=1, max_value=9, value=2, step=1, key=f"{key}-nb-rois")
                
                param_roi_dict = {}
                for i in range(int(nb_rois)):
                    # Default names
                    default_name = f"ROI_{i+1}"
                    if i == 0: default_name = "ant"
                    elif i == 1: default_name = "post"
                    
                    # Default channels
                    default_chans = []
                    if i == 0: default_chans = DEFAULT_ROI_ANT
                    elif i == 1: default_chans = DEFAULT_ROI_POST
                    
                    c_name, c_chans = st.columns([1, 3])
                    with c_name:
                        roi_name = st.text_input(f"Name ROI {i+1}", value=default_name, key=f"{key}-roi-name-{i}")
                    with c_chans:
                        channels_str = ", ".join(default_chans)
                        roi_chans_str = st.text_area(f"Channels for {roi_name}", value=channels_str, height=70, key=f"{key}-roi-chans-{i}")
                        
                    chans_list = [c.strip() for c in roi_chans_str.split(',') if c.strip()]
                    if roi_name and chans_list:
                        param_roi_dict[roi_name] = chans_list
            else:
                param_roi_dict = None
                st.info("ROI Analysis disabled. FFT will be computed independently for each EEG channel.")


    # --- Processing ---
    st.markdown("---")
    if st.button("Run FFT Extraction", type="primary", disabled=not (input_path and output_dir and is_valid), key=f"{key}-btn"):
        
        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
            except Exception as e:
                st.error(f"Could not create output directory: {e}")
                return

        orig_backend = plt.get_backend()

        try:
            # 1. Optionnal Plotting
            if do_plot_epochs:
                epochs_to_plot = mne.read_epochs(input_path, preload=False, verbose=False)
                try:
                    try: plt.switch_backend('Qt5Agg')
                    except: plt.switch_backend('TkAgg')
                    
                    st.info("Opening interactive plot on the server. Close the plot window to continue FFT extraction.")
                    epochs_to_plot.plot(
                        events=epochs_to_plot.events,
                        event_id=epochs_to_plot.event_id,
                        title='Verify Epochs for FFT', 
                        show=True, 
                        block=True, 
                        scalings=dict(eeg=50e-6)
                    )
                except Exception as e:
                    st.warning(f"Interactive plot Error (check your display server): {e}")
                finally:
                    try: plt.switch_backend(orig_backend)
                    except: pass
                    
            # 2. Proceed with Extraction
            with st.spinner("Extracting Relative FFT power..."):
                df_sub = analyze_fft(
                    epochs_path=input_path,
                    roi_dict=param_roi_dict
                )
                    
            if not df_sub.empty:
                subject_name = os.path.splitext(os.path.basename(input_path))[0]
                
                # Save Excel
                filename_data = f"{subject_name}_fft.csv"
                save_path_data = os.path.join(output_dir, filename_data)
                
                try:
                    # Rename conditions
                    df_sub = df_sub.rename(index=CHANNEL_CODES, level='Condition')

                    # Save CSV
                    df_sub.to_csv(save_path_data)
                    st.success(f"✅ FFT Extraction Complete. Saved to `{save_path_data}`")
                    st.dataframe(df_sub)
                    
                except Exception as e:
                    st.error(f"Error saving outputs: {e}")
            else:
                st.warning("No data extracted. Please check parameters and file.")

        except Exception as e:
            st.error(f"Error processing {input_path}: {e}")
