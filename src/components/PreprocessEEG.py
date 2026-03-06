
import streamlit as st
import os
import matplotlib.pyplot as plt
import mne
import numpy as np
import pandas as pd

from src.functions import (
    notch_filter, 
    bandpass_filter,
    resample_data, 
    interpolate_bads,
    set_average_reference,
    trim_eeg_data,
    read_triggers
)

from src.components.Sidebar import update_sidebar_log
from src.constants.config_eeg import DEFAULT_TRIGGERS

def PreprocessEEG(key="preprocess-eeg"):
    """
    Component to preprocess EEG data with granular step control.
    """

    # --- Global Inputs ---

    input_path = st.text_input(
        "Input FIF File Path",
        placeholder="Enter path to .fif file (e.g., subject_raw.fif)",
        help="Path to the raw converted .fif file",
        key=f"{key}-input"
    )
    output_dir = st.text_input(
        "Output Directory",
        placeholder="Enter output directory ...",
        help="Directory to save the preprocessed file",
        key=f"{key}-output"
    )

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

    ## Checkboxes and Parameters ---------------------------    
    st.markdown("---")
    st.markdown("#### Processing Steps")

    # 1. Trimming
    col_s4, col_e4 = st.columns([1, 4])
    with col_s4:
         do_trim = st.checkbox(
            "Trim Data", 
            value=True, 
            key=f"{key}-do-trim",
            help="Removes signals before the 1st trigger and after the end of last trigger"
        )
    with col_e4:
         with st.expander("Trimming Parameters", expanded=do_trim):
             
             # Select Stim/Trigger Channels
             if raw:
                 all_channels = raw.ch_names
                 available_di = [ch for ch in DEFAULT_TRIGGERS if ch in all_channels]
                 param_stim_channels = st.multiselect(
                     "Stim/Trigger Channels",
                     options=all_channels,
                     default=available_di,
                     key=f"{key}-stim-ch"
                 )
             else:
                 param_stim_channels = []

             # List to hold formatting strings for the selectboxes
             trigger_options = []
             
             # If trimming is enabled, and the raw file exists
             if do_trim and raw is not None:
                 try:
                     # Parse the raw file to extract events formatted as "{index}_{code}_{time}s" using selected channels
                     trigger_df = read_triggers(raw, stim_channels=param_stim_channels, verbose=False)
                     
                     if not trigger_df.empty:
                         # Options Formatting
                         for index, row in trigger_df.iterrows():
                             option_str = f"{row['idx']}_{row['code']}_{row['time']:.3f}s"
                             trigger_options.append(option_str)
                             
                 except Exception as e:
                     st.warning(f"Could not load triggers for preview: {e}")
                     
             if trigger_options:
                 st.dataframe(trigger_df, width='stretch', hide_index=True, height=160)

                 col_start, col_end, col_duration = st.columns(3)
                 with col_start:
                     param_trim_start = st.selectbox("Start Trigger", options=trigger_options, index=0, key=f"{key}-trim-start")
                 with col_end:
                     param_trim_end = st.selectbox("End Trigger", options=trigger_options, index=len(trigger_options)-1, key=f"{key}-trim-end")
                 with col_duration:
                     param_trim_dur = st.number_input("Duration after last trigger (s)", value=60.0, min_value=0.0, step=1.0, key=f"{key}-trim-dur")
                 
                 # Store index in session state or extract from string later
             else:
                 st.info("Provide valid input FIF to select triggers.")
                 param_trim_start = None
                 param_trim_end = None

    # 2. Notch Filter
    col_s1, col_e1 = st.columns([1, 4])
    with col_s1:
        do_notch = st.checkbox(
            "Notch Filter (50Hz)", 
            value=True, 
            key=f"{key}-do-notch", 
            help="Applies 50, 100, 150 Hz notch filter automatically."
        )
            
    # 3. Bandpass Filter
    col_s2, col_e2 = st.columns([1, 4])
    with col_s2:
        do_bandpass = st.checkbox(
            "Bandpass Filter", 
            value=True, 
            key=f"{key}-do-bp",
            help="Applies Bandpass Filter."
            
        )
    with col_e2:
        with st.expander("Bandpass Parameters", expanded=do_bandpass):
            col_bp1, col_bp2 = st.columns(2)
            with col_bp1:
                param_highpass = st.number_input("Highpass (Hz)", value=0.5, min_value=0.0, step=0.1, key=f"{key}-hp")
            with col_bp2:
                param_lowpass = st.number_input("Lowpass (Hz)", value=45.0, min_value=0.0, step=1.0, key=f"{key}-lp")

    # 4. Resample
    col_s3, col_e3 = st.columns([1, 4])
    with col_s3:
        do_resample = st.checkbox(
            "Resample", 
            value=True, 
            key=f"{key}-do-resamp",
            help="Applies Resample."
        )
    with col_e3:
        with st.expander("Resample Parameters", expanded=do_resample):
            # Validation logic: freq >= 2 * lowpass
            min_resample = max(1.0, param_lowpass * 2.0) if do_bandpass else 1.0
            param_sfreq = st.number_input(
                "Resample Freq (Hz)", 
                value=max(200.0, min_resample), 
                min_value=float(min_resample), 
                step=10.0, 
                key=f"{key}-sfreq",
                help=f"Must be >= 2 * Lowpass ({min_resample} Hz) to respect Nyquist."
            )

    
    # 5. Bad Channels Manual Selection
    col_s5, col_e5 = st.columns([1, 4])
    with col_s5:
        do_manual_bads = st.checkbox(
            "Select Bad Channels", 
            value=True, 
            key=f"{key}-do-bads",
            help="Opens native MNE plot for manual selection of bad Channels."
        )


    # 6. Interpolation
    col_s6, col_e6 = st.columns([1, 4])
    with col_s6:
        do_interpolate = st.checkbox(
            "Interpolate Bads", 
            value=True, 
            key=f"{key}-do-interp",
            help="Spherical spline interpolation for selected bad channels."
        )
    
    # 7. Referencing
    col_s7, col_e7 = st.columns([1, 4])
    with col_s7:
        do_reference = st.checkbox(
            "Average Reference", 
            value=True, 
            key=f"{key}-do-ref",
            help="Re-reference data to the average of all channels."
        )

    st.markdown("---")

    # --- Processing -----------------------------------------------------
    if st.button("Run Selected Steps", type="primary", disabled=not (input_path and output_dir and is_valid), key=f"{key}-btn"):
        
        # Ensure output dir exists
        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
            except Exception as e:
                st.error(f"Could not create output directory: {e}")
                return

        subject_name = os.path.splitext(os.path.basename(input_path))[0].replace('_raw', '') 
        
        st.info(f"Processing: {os.path.basename(input_path)}")
        
        # --- Save to Session State for Sidebar Log immediately ---
        st.session_state['eeg_process_log'] = {
            'subject_name': subject_name,
            'do_trim': do_trim,
            'param_trim_start': param_trim_start if do_trim else None,
            'param_trim_end': param_trim_end if do_trim else None,
            'param_trim_dur': param_trim_dur if do_trim else None,
            'do_notch': do_notch,
            'do_bandpass': do_bandpass,
            'param_highpass': param_highpass if do_bandpass else None,
            'param_lowpass': param_lowpass if do_bandpass else None,
            'do_resample': do_resample,
            'param_sfreq': param_sfreq if do_resample else None,
            'do_manual_bads': do_manual_bads,
            'do_interpolate': do_interpolate,
            'do_reference': do_reference
        }
        
        # Immediately render the log in the sidebar
        update_sidebar_log()

        try:
            with st.spinner("Loading data into memory..."):
                raw.load_data() 
            
            orig_backend = plt.get_backend()

            # --- 1. Trimming ---
            if do_trim:
                if not param_trim_start or not param_trim_end:
                    st.error("Cannot trim: Triggers not loaded properly. Check your Event ID File.")
                    return
                
                # Parse start/end times from the selectbox option string {index}_{code}_{time}s
                start_time_str = param_trim_start.split('_')[-1].replace('s', '')
                end_time_str = param_trim_end.split('_')[-1].replace('s', '')
                
                start_time = float(start_time_str)
                end_time = float(end_time_str)
                
                if start_time > end_time:
                    st.warning("Selected Start Trigger occurs after End Trigger. Swapping them.")
                    start_time, end_time = end_time, start_time
                
                with st.spinner(f"Trimming data (keeping up to +{param_trim_dur}s after last trigger)..."):
                    raw = trim_eeg_data(raw, start_time=start_time, end_time=end_time, duration_after_last=param_trim_dur, verbose=True)


            # --- 2. Notch Filter ---
            if do_notch:
                with st.spinner("Applying Notch Filter (50, 100, 150 Hz)..."):
                    raw = notch_filter(raw, verbose=True)

            # --- 3. Bandpass Filter ---
            if do_bandpass:
                with st.spinner(f"Applying Bandpass Filter ({param_highpass}-{param_lowpass} Hz)..."):
                    raw = bandpass_filter(raw, highpass=param_highpass, highcut=param_lowpass, verbose=True)

            # Plot PSD if either filter was applied
            if do_notch or do_bandpass:
                st.info("Opening PSD Plot (Native)... Close it to continue.")
                try:
                    try: plt.switch_backend('Qt5Agg')
                    except: plt.switch_backend('TkAgg')
                    raw.compute_psd().plot(show=False) 
                    plt.show(block=True)
                except Exception as e:
                    st.warning(f"PSD Plot error: {e}")
                finally:
                    try: plt.switch_backend(orig_backend)
                    except: pass


            # --- 4. Downsample ---
            if do_resample:
                with st.spinner(f"Resampling to {param_sfreq}Hz..."):
                    raw = resample_data(raw, sfreq=param_sfreq)

            

            # --- 5. Manual Bad Channel/Period Selection ---
            if do_manual_bads:
                st.info("Opening Signal Plot for Manual Inspection... Mark bad channels/segments. Close to continue.")
                try:
                    try: plt.switch_backend('Qt5Agg')
                    except: plt.switch_backend('TkAgg')
                    
                    raw.plot(show_options=True, title='Tag Bad Channels & Artifacts', block=True)
                    
                    st.info(f"Bad Channels marked: {raw.info['bads']}")
                except Exception as e:
                     st.warning(f"Manual Inspection error: {e}")
                finally:
                    try: plt.switch_backend(orig_backend)
                    except: pass

            # --- 6. Interpolation ---
            if do_interpolate:
                if len(raw.info['bads']) > 0:
                    with st.spinner("Interpolating bad channels..."):
                        raw = interpolate_bads(raw)
                else:
                    st.info("No bad channels to interpolate.")

            # --- 7. Re-referencing ---
            if do_reference:
                with st.spinner("Re-referencing to Average..."):
                    raw = set_average_reference(raw)


            # --- 8. Save ---
            filename = f"{subject_name}_filter.fif"
            save_path = os.path.join(output_dir, filename)
            
            with st.spinner(f"Saving to {save_path}..."):
                raw.save(save_path, overwrite=True)
            
            st.success(f"✅ Processing Complete. Saved to `{save_path}`")
            
            # --- Final Inspection ---
            st.info("Opening Final Signal Plot... Close to finish.")
            try:
                try: plt.switch_backend('Qt5Agg')
                except: plt.switch_backend('TkAgg')
                
                raw.plot(show_options=True, title='Preprocessing finished', block=True)
                
            except Exception as e:
                 st.warning(f"Final Inspection error: {e}")
            finally:
                try: plt.switch_backend(orig_backend)
                except: pass
                

            
        except Exception as e:
            st.error(f"❌ Processing Error: {e}")
            st.exception(e)
