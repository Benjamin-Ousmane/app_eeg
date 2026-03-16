
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
    read_triggers,
    st_display_logs
)

from src.constants.config_eeg import (
    DEFAULT_TRIGGERS,
    DEFAULT_CHAN_PSD_PLOT,
    DEFAULT_CHAN_MISC,
    DEFAULT_BADS,
    SFREQ
)

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

    # 0. Exclude Channels
    col_s0, col_e0 = st.columns([1, 4])
    with col_s0:
        do_exclude_misc = st.checkbox(
            "Exclude Channels (misc)", 
            value=True, 
            key=f"{key}-do-misc",
            help="Set specific channels to 'misc' type so they are ignored."
        )
    with col_e0:
        with st.expander("Channels to Exclude", expanded=do_exclude_misc):
            if raw:
                available_chans = raw.ch_names
                default_misc = [ch for ch in DEFAULT_CHAN_MISC if ch in available_chans]
            else:
                available_chans = DEFAULT_CHAN_MISC
                default_misc = DEFAULT_CHAN_MISC
                
            param_misc_channels = st.multiselect(
                "Channels to set as 'misc'",
                options=available_chans,
                default=default_misc,
                key=f"{key}-misc-ch"
            )

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

                 col_start, col_end, col_duration1, col_duration2 = st.columns(4)
                 with col_start:
                     param_trim_start = st.selectbox("Start Trigger", options=trigger_options, index=0, key=f"{key}-trim-start")
                 with col_duration1:
                     param_trim_dur_before = st.number_input("Duration before first trigger (s)", value=5.0, min_value=0.0, step=1.0, key=f"{key}-trim-before")
                 with col_end:
                     param_trim_end = st.selectbox("End Trigger", options=trigger_options, index=len(trigger_options)-1, key=f"{key}-trim-end")
                 with col_duration2:
                     param_trim_dur_after = st.number_input("Duration after last trigger (s)", value=65.0, min_value=0.0, step=1.0, key=f"{key}-trim-after")
                 
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
                
    # 3.5 Plot PSD
    col_s_psd, col_e_psd = st.columns([1, 4])
    with col_s_psd:
        do_plot_psd = st.checkbox(
            "Plot PSD", 
            value=True, 
            key=f"{key}-do-psd",
            help="Show Power Spectral Density plot."
        )
    with col_e_psd:
        with st.expander("PSD Plot Parameters", expanded=do_plot_psd):
            if raw:
                available_psd = raw.ch_names
                default_psd = [ch for ch in DEFAULT_CHAN_PSD_PLOT if ch in available_psd]
            else:
                available_psd = DEFAULT_CHAN_PSD_PLOT
                default_psd = DEFAULT_CHAN_PSD_PLOT
                
            param_psd_channels = st.multiselect(
                "Channels for PSD plot",
                options=available_psd,
                default=default_psd,
                key=f"{key}-psd-ch"
            )

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
                value=max(float(SFREQ), min_resample), 
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
    with col_e5:
        with st.expander("Bad Channels Parameters", expanded=do_manual_bads):
            if raw:
                available_bads = raw.ch_names
                default_bads = [ch for ch in DEFAULT_BADS if ch in available_bads]
            else:
                available_bads = DEFAULT_BADS
                default_bads = DEFAULT_BADS
                
            param_default_bads = st.multiselect(
                "Default Bad Channels",
                options=available_bads,
                default=default_bads,
                key=f"{key}-default-bads"
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

# --------------------------------------------------------
# --- Processing -----------------------------------------
# --------------------------------------------------------

    if st.button("Run Selected Steps", type="primary", disabled=not (input_path and output_dir and is_valid), key=f"{key}-btn"):
        
        # Ensure output dir exists
        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
            except Exception as e:
                st.error(f"Could not create output directory: {e}")
                return

        subject_name = os.path.splitext(os.path.basename(input_path))[0].replace('_raw', '') 

        
        # --- Initialize log_data and placeholder ---
        log_placeholder = st.sidebar.empty()
        log_data = {
            'subject_name': subject_name,
            'process_type': 'preprocess',
            'config': {
                'do_exclude_misc': do_exclude_misc,
                'do_trim': do_trim,
                'do_notch': do_notch,
                'do_bandpass': do_bandpass,
                'do_resample': do_resample,
                'do_manual_bads': do_manual_bads,
                'do_interpolate': do_interpolate,
                'do_reference': do_reference
            }
        }
        
        st_display_logs(log_data, log_placeholder, key=f"{key}-logs")

        try:
            with st.spinner("Loading data into memory..."):
                raw.load_data() 
            
            orig_backend = plt.get_backend()

            # --- 0. Exclude misc validation ---
            if do_exclude_misc and param_misc_channels:
                with st.spinner("Setting selected channels to 'misc'..."):
                    # Only map channels that are present in the instance
                    misc_map = {ch: 'misc' for ch in param_misc_channels if ch in raw.ch_names}
                    if misc_map:
                        raw.set_channel_types(misc_map)
                        log_data['do_exclude_misc'] = True
                        log_data['param_misc_channels'] = param_misc_channels
                        st_display_logs(log_data, log_placeholder, key=f"{key}-logs")

            # --- 1. Trimming ---
            if do_trim:
                if not param_trim_start or not param_trim_end:
                    st.error("Cannot trim: Triggers not loaded properly. Check your Event ID File.")
                    return
                
                # Parse start/end times from the selectbox option string {index}_{code}_{time}s
                start_time_str = param_trim_start.split('_')[-1].replace('s', '')
                end_time_str = param_trim_end.split('_')[-1].replace('s', '')
                
                # Apply before duration
                start_time = max(0.0, float(start_time_str) - param_trim_dur_before)
                end_time = float(end_time_str) + param_trim_dur_after
                
                if start_time > end_time:
                    st.warning("Selected Start Trigger occurs after End Trigger. Swapping them.")
                    start_time, end_time = end_time, start_time
                
                with st.spinner(f"Trimming data (keeping -{param_trim_dur_before}s before and +{param_trim_dur_after}s after)..."):
                    raw = trim_eeg_data(raw, start_time=start_time, end_time=end_time, verbose=True)
                    log_data['do_trim'] = True
                    log_data['param_trim_start'] = param_trim_start
                    log_data['param_trim_end'] = param_trim_end
                    log_data['param_trim_dur_before'] = param_trim_dur_before
                    log_data['param_trim_dur_after'] = param_trim_dur_after
                    st_display_logs(log_data, log_placeholder, key=f"{key}-logs")


            # --- 2. Notch Filter ---
            if do_notch:
                with st.spinner("Applying Notch Filter (50, 100, 150 Hz)..."):
                    raw = notch_filter(raw, verbose=True)
                    log_data['do_notch'] = True
                    st_display_logs(log_data, log_placeholder, key=f"{key}-logs")

            # --- 3. Bandpass Filter ---
            if do_bandpass:
                with st.spinner(f"Applying Bandpass Filter ({param_highpass}-{param_lowpass} Hz)..."):
                    raw = bandpass_filter(raw, highpass=param_highpass, highcut=param_lowpass, verbose=True)
                    log_data['do_bandpass'] = True
                    log_data['param_highpass'] = param_highpass
                    log_data['param_lowpass'] = param_lowpass
                    st_display_logs(log_data, log_placeholder, key=f"{key}-logs")

            # --- 3.5 Plot PSD ---
            if do_plot_psd:
                try:
                    try: plt.switch_backend('Qt5Agg')
                    except: plt.switch_backend('TkAgg')
                    
                    if param_psd_channels:
                        picks_psd_plot = mne.pick_types(raw.info, eeg=True, selection=param_psd_channels)
                        raw.plot_psd(area_mode='range', tmax=10.0, picks=picks_psd_plot, average=False)
                    else:
                        raw.plot_psd(area_mode='range', tmax=10.0, average=False) 
                    
                    plt.show(block=True)
                    log_data['do_plot_psd'] = True
                    st_display_logs(log_data, log_placeholder, key=f"{key}-logs")
                except Exception as e:
                    st.warning(f"PSD Plot error: {e}")
                finally:
                    try: plt.switch_backend(orig_backend)
                    except: pass


            # --- 4. Downsample ---
            if do_resample:
                with st.spinner(f"Resampling to {param_sfreq}Hz..."):
                    raw = resample_data(raw, sfreq=param_sfreq)
                    log_data['do_resample'] = True
                    log_data['param_sfreq'] = param_sfreq
                    st_display_logs(log_data, log_placeholder, key=f"{key}-logs")

            

            # --- 5. Select bad channels ---
            if do_manual_bads:
                try:
                    try: plt.switch_backend('Qt5Agg')
                    except: plt.switch_backend('TkAgg')
                    
                    # Set default bads
                    if param_default_bads:
                         new_bads = [ch for ch in param_default_bads if ch in raw.ch_names and ch not in raw.info['bads']]
                         raw.info['bads'].extend(new_bads)
                         
                    # Select bad channels on plot
                    picks = mne.pick_types(raw.info, eeg=True, ecg=True, emg=True, stim=True, eog=True, exclude=[])
                    raw.plot(show_options=True, title='Tag Bad Channels & Artifacts', block=True, picks=picks)
                    
                    # Show Sensors identifying bads in red
                    raw.plot_sensors(kind='3d', ch_type='eeg', title='Sensory positions, Red ones are indicated as bads', show=False)
                    plt.show(block=True)
                    
                    log_data['do_manual_bads'] = True
                    log_data['marked_bads'] = raw.info['bads']
                    st_display_logs(log_data, log_placeholder, key=f"{key}-logs")
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
                        log_data['do_interpolate'] = True
                        st_display_logs(log_data, log_placeholder, key=f"{key}-logs")

            # --- 7. Re-referencing ---
            if do_reference:
                with st.spinner("Re-referencing to Average..."):
                    raw = set_average_reference(raw)
                    log_data['do_reference'] = True
                    st_display_logs(log_data, log_placeholder, key=f"{key}-logs")


            # --- 8. Save ---
            filename = f"{subject_name}_preprocessed.fif"
            save_path = os.path.join(output_dir, filename)
            
            with st.spinner(f"Saving to {save_path}..."):
                raw.save(save_path, overwrite=True)
            
            st.success(f"✅ Processing Complete. Saved to `{save_path}`")
            
            # Finalize log
            st_display_logs(log_data, log_placeholder, key=f"{key}-logs", is_final=True)
            
            # --- Final Inspection ---
            try:
                try: plt.switch_backend('Qt5Agg')
                except: plt.switch_backend('TkAgg')
                
                picks = mne.pick_types(raw.info, eeg=True, ecg=True, emg=True, stim=True, eog=True, exclude=[])
                raw.plot(show_options=True, title='Preprocessing finished', block=True, picks=picks)
                
            except Exception as e:
                 st.warning(f"Final Inspection error: {e}")
            finally:
                try: plt.switch_backend(orig_backend)
                except: pass
                

            
        except Exception as e:
            st.error(f"❌ Processing Error: {e}")
            st.exception(e)
