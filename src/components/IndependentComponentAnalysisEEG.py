
import streamlit as st
import os
import matplotlib.pyplot as plt
import mne
import numpy as np
import pandas as pd

from src.functions import (
    fit_ica,
    find_blinks,
    st_display_logs
)

from src.constants.config_eeg import ICA_RANDOM_STATE


def IndependentComponentAnalysisEEG(key="ica-eeg"):
    """
    Component to perform ICA for blink correction with granular step control.
    """

    # --- Global Inputs ---

    input_path = st.text_input(
        "Input FIF File Path",
        placeholder="Enter path to .fif file (e.g., subject_processed.fif)",
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

    st.markdown("---")
    # 1. Find Blinks
    col_s1, col_e1 = st.columns([1, 4])
    with col_s1:
        do_find_blinks = st.checkbox("Find Blinks", value=True, key=f"{key}-do-blinks")
   
    # 2. Select EOG
    col_s2, col_e2 = st.columns([1, 4])
    with col_s2:
        do_find_eog = st.checkbox("Select EOG", value=True, help="Select the channel to use as proxy for EOG (e.g., E25).", key=f"{key}-do-eog")
    with col_e2:
        with st.expander("EOG Parameters", expanded=do_find_eog):
            if raw is not None:
                eog_opts = raw.ch_names
                default_idx = eog_opts.index("E25") if "E25" in eog_opts else 0
                param_eog_ch = st.selectbox("EOG Channel", options=eog_opts, index=default_idx, key=f"{key}-eog")
            else:
                param_eog_ch = st.selectbox("EOG Channel", options=["E25"], index=0, key=f"{key}-eog")

    # 3. Apply ICA
    col_s3, col_e3 = st.columns([1, 4])
    with col_s3:
        do_apply_ica = st.checkbox("Apply ICA", value=True, key=f"{key}-do-apply")
    with col_e3:
        with st.expander("ICA Parameters", expanded=do_apply_ica):
            col_i1, col_i2 = st.columns(2)
            with col_i1:
                param_n_components = st.number_input("N Components", value=10, min_value=1, step=1, key=f"{key}-ncomp")
            with col_i2:
                param_method = st.selectbox("Method", ["fastica", "infomax", "picard"], index=0, key=f"{key}-method")

    st.markdown("---")


    # --- Processing ---
    if st.button("Run Selected Steps", type="primary", disabled=not (input_path and output_dir and is_valid), key=f"{key}-btn"):
        
        # Ensure output dir exists
        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
            except Exception as e:
                st.error(f"Could not create output directory: {e}")
                return

        subject_name = os.path.splitext(os.path.basename(input_path))[0].replace('preprocessed', '') 
        
        # --- Initialize log_data and placeholder ---
        log_placeholder = st.sidebar.empty()
        log_data = {
            'subject_name': subject_name,
            'process_type': 'ica',
            'config': {
                'do_find_blinks': do_find_blinks,
                'do_find_eog': do_find_eog,
                'do_apply_ica': do_apply_ica
            }
        }
        
        st_display_logs(log_data, log_placeholder, key=f"{key}-logs")
        
        orig_backend = plt.get_backend()

        try:
            with st.spinner("Loading data into memory..."):
                raw.load_data()
            
            # --- 1. Find Blinks ---
            if do_find_blinks:
                with st.spinner(f"Finding blinks using {param_eog_ch if do_find_eog else 'default config'}..."):
                    ch = param_eog_ch if do_find_eog else "E25" # Fallback if EOG is unchecked
                    try:
                        eog_events = find_blinks(raw, ch)
                        log_data['do_find_blinks'] = True
                        log_data['blinks_count'] = len(eog_events)
                        st_display_logs(log_data, log_placeholder, key=f"{key}-logs")
                    except Exception as e:
                        st.warning(f"Could not find blinks on {ch}: {e}")

            if do_find_eog or do_apply_ica:
                with st.spinner(f"Fitting ICA ({param_n_components} components)..."):
                    ica = fit_ica(raw, n_components=param_n_components, method=param_method, random_state=ICA_RANDOM_STATE)

                # --- 2. Find Bad EOG ---
                if do_find_eog:
                    try:
                        eog_inds, scores = ica.find_bads_eog(raw, ch_name=param_eog_ch, threshold=3.0)
                        ica.exclude = eog_inds
                        log_data['do_find_eog'] = True
                        log_data['param_eog_ch'] = param_eog_ch
                        log_data['eog_excludes'] = eog_inds
                        st_display_logs(log_data, log_placeholder, key=f"{key}-logs")
                    except Exception as e:
                        st.warning(f"Could not find bad EOG components: {e}")

                # --- 3. Apply ICA ---
                if do_apply_ica:                    
                    # 1. Plot Components
                    try:
                        try: plt.switch_backend('Qt5Agg')
                        except: plt.switch_backend('TkAgg')

                        ica.plot_components(show=False, title="ICA Components")
                        plt.show(block=True) # Important: plot_sources is blocking next
                
                        
                    except Exception as e:
                        st.error(f"Native Plot Error: {e}")
                    finally:
                        try: plt.switch_backend(orig_backend)
                        except: pass


                    # 2. Plot Sources (Uses MNE's own blocker for raw data)
                    try:
                        try: plt.switch_backend('Qt5Agg')
                        except: plt.switch_backend('TkAgg')

                        ica.plot_sources(raw, block=True, title="ICA Sources (Click to reject, close to finish)")
                        
                    except Exception as e:
                        st.error(f"Native Plot Error: {e}")
                    finally:
                        try: plt.switch_backend(orig_backend)
                        except: pass

                    with st.spinner("Applying ICA to data..."):
                        ica.apply(raw)
                        log_data['do_apply_ica'] = True
                        log_data['param_n_components'] = param_n_components
                        log_data['param_method'] = param_method
                        log_data['ica_excludes'] = ica.exclude
                        st_display_logs(log_data, log_placeholder, key=f"{key}-logs")

            # --- Save ---
            if do_apply_ica:
                input_basename = os.path.splitext(os.path.basename(input_path))[0]
                filename = f"{input_basename}_ica.fif"
                save_path = os.path.join(output_dir, filename)
                
                with st.spinner(f"Saving to {save_path}..."):
                    raw.save(save_path, overwrite=True)
                
                st.success(f"✅ ICA Complete. Saved to `{save_path}`")
                
                # Finalize log
                st_display_logs(log_data, log_placeholder, key=f"{key}-logs", is_final=True)
            else:
                st.info("ICA was not applied. No new file saved.")
                

        except Exception as e:
            st.error(f"❌ ICA Error: {e}")
            st.exception(e)
