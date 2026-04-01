import streamlit as st
import os
import matplotlib.pyplot as plt
import mne
import pandas as pd

from src.functions import read_triggers, epoch_data, crop_raw_to_conditions
from src.constants.config_eeg import DEFAULT_TRIGGERS
from src.constants import DEFAULT_WINDOW_SIZE

def EpochingEEG(key="epoch-eeg"):
    """
    Component to Epoch EEG data based on selected triggers and sliding windows.
    """
    st.markdown("### EEG Epoching")

    # --- Global Inputs ---
    input_path = st.text_input(
        "Input FIF File Path",
        placeholder="Enter path to .fif file (e.g., subject_processed.fif)",
        help="Path to the preprocessed .fif file",
        key=f"{key}-input"
    )
    if input_path.startswith('"') and input_path.endswith('"'):
        input_path = input_path[1:-1]
    elif input_path.startswith("'") and input_path.endswith("'"):
        input_path = input_path[1:-1]

    output_dir = st.text_input(
        "Output Directory",
        placeholder="Enter output directory ...",
        help="Directory to save the epoched file",
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

    # --- Parameters ---
    st.markdown("---")
    st.markdown("#### Epoching Parameters")
    
    # 1. Select Triggers
    col_t1, col_t2 = st.columns([1, 4])
    with col_t1:
        do_select_triggers = st.checkbox("Select Triggers", value=True, help="Décochez pour epochiser l'intégralité du signal brut (sans condition assignée)", key=f"{key}-do-select")
    with col_t2:
        with st.expander("Trigger Selection", expanded=do_select_triggers):
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

            trigger_df = pd.DataFrame()
            edited_trigger_df = pd.DataFrame()
            if raw and param_stim_channels:
                try:
                    trigger_df = read_triggers(raw, stim_channels=param_stim_channels, verbose=False)
                    if not trigger_df.empty:
                        # Add Keep column
                        trigger_df.insert(0, "Keep", True)
                        
                        st.markdown("Select which events to keep as condition starts:")
                        edited_trigger_df = st.data_editor(
                            trigger_df,
                            width='stretch',
                            hide_index=True,
                            column_config={'mne_val': None},
                            key=f"{key}-trigger-editor"
                        )
                except Exception as e:
                    st.warning(f"Could not load triggers: {e}")
                    
            param_condition_duration = st.number_input("Condition Duration (s)", value=60.0, min_value=1.0, step=1.0, key=f"{key}-cond-dur", help="La durée de la condition après chaque trigger sélectionné.")

    # 2. Apply Epoching
    col_e1, col_e2 = st.columns([1, 4])
    with col_e1:
        do_apply_epoching = st.checkbox("Apply Epoching", value=True, disabled=True, key=f"{key}-do-epoch")
    with col_e2:
        with st.expander("Epoching Settings", expanded=do_apply_epoching):
            c_e1, c_e2, c_e3 = st.columns(3)
            with c_e1:
                param_window_size = st.number_input("Window Size (s)", value=DEFAULT_WINDOW_SIZE, min_value=0.1, step=1.0, key=f"{key}-win-size")
            with c_e2:
                do_baseline = st.checkbox("Apply Baseline", value=False, key=f"{key}-base")
                param_baseline = (None, 0) if do_baseline else None
            with c_e3:
                do_detrend = st.checkbox("Apply Detrend", value=False, help="Linear detrending", key=f"{key}-detrend")
                param_detrend = 1 if do_detrend else None

    # 3. Manual Inspection
    col_m1, col_m2 = st.columns([1, 4])
    with col_m1:
        do_manual_inspection = st.checkbox("Manual Inspection", value=True, help="Ouvre une fenêtre interactive pour rejeter manuellement de mauvaises epochs.", key=f"{key}-do-inspect")

    # --- Processing ---
    st.markdown("---")
    if st.button("Run Epoching", type="primary", disabled=not (input_path and output_dir and is_valid), key=f"{key}-btn"):
        
        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
            except Exception as e:
                st.error(f"Could not create output directory: {e}")
                return
                
        if edited_trigger_df.empty:
            st.error("No triggers available or selected. Ensure you have loaded valid data and selected Stim Channels.")
            return

        subject_name = os.path.splitext(os.path.basename(input_path))[0]
        
        orig_backend = plt.get_backend()

        try:
            if do_select_triggers:
                with st.spinner("Cropping raw data to selected conditions..."):
                    keep_events_df = edited_trigger_df[edited_trigger_df["Keep"] == True]
                    if keep_events_df.empty:
                        st.error("No triggers marked as 'Keep'.")
                        return
                    
                    raw_segments, event_codes_list, event_id_dict = crop_raw_to_conditions(raw, keep_events_df, condition_duration=param_condition_duration)

                with st.spinner("Creating Epochs and assigning triggers..."):
                    epochs = epoch_data(
                        data=raw_segments,
                        event_id_list=event_codes_list,
                        event_dict=event_id_dict,
                        window_size=param_window_size,
                        baseline=param_baseline,
                        detrend=param_detrend,
                        verbose=True
                    )
            else:
                with st.spinner("Creating Epochs across entire raw signal..."):
                    epochs = epoch_data(
                        data=raw,
                        event_id=None,
                        window_size=param_window_size,
                        baseline=param_baseline,
                        detrend=param_detrend,
                        verbose=True
                    )
            
            if epochs is None or len(epochs) == 0:
                st.error("Failed to extract valid epochs. The signal may be too short for the chosen window size.")
                return
            
            # Interactive visualization
            if do_manual_inspection:
                try:
                    try: plt.switch_backend('Qt5Agg')
                    except: plt.switch_backend('TkAgg')
                    
                    st.info("Opening interactive plot on the server. Close the plot window to continue.")
                    epochs.plot(
                        events=epochs.events,
                        event_id=epochs.event_id,
                        title=f'Epochs for {subject_name} - Click to drop epochs', 
                        show=True, 
                        block=True, 
                        scalings=dict(eeg=50e-6)
                    )
                except Exception as e:
                    st.warning(f"Interactive plot Error (check your display server): {e}")
                finally:
                    try: plt.switch_backend(orig_backend)
                    except: pass

            # Save
            filename = f"{subject_name}_epo.fif"
            save_path = os.path.join(output_dir, filename)
            
            with st.spinner(f"Saving to {save_path}..."):
                epochs.save(save_path, overwrite=True)
            
            st.success(f"✅ Epoching Complete. Saved to `{save_path}`")

        except Exception as e:
            st.error(f"❌ Epoching Error: {e}")
            st.exception(e)
