import streamlit as st
import os
import pandas as pd
import matplotlib.pyplot as plt
import mne
from src.functions import analyze_connectivity
from src.constants import CHANNEL_CODES

def AnalysisConnectivity(key="analysis-connectivity"):
    """
    Component to compute and extract spectral connectivity from an epoched FIF file.
    """
    st.markdown("### Connectivity Analysis")

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
        help="Directory to save the resulting CSV file",
        key=f"{key}-output"
    )
    if output_dir.startswith('"') and output_dir.endswith('"'):
        output_dir = output_dir[1:-1]
    elif output_dir.startswith("'") and output_dir.endswith("'"):
        output_dir = output_dir[1:-1]

    # --- Validation & Display ---
    is_valid = True
    raw_info = None
    
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
    st.markdown("#### Connectivity Parameters")

    # 1. Plot Epochs
    col_p1, col_p2 = st.columns([1, 4])
    with col_p1:
        do_plot_epochs = st.checkbox("Plot Epochs", value=False, help="Will open an MNE window to visually inspect the used epochs.", key=f"{key}-do-plot")

    # 2. Select Channels
    available_chans = raw_info['ch_names'] if raw_info else []
            
    col_s1, col_s2 = st.columns([1, 4])
    
    with col_s1:
        st.checkbox("Select channels for connectivity", value=True, disabled=True, key=f"{key}-do-select")
        
    with col_s2:
        with st.expander("Final Channels Selection", expanded=True):
            selected_channels = st.multiselect(
                "Channels to include in connectivity analysis",
                options=available_chans,
                default=available_chans,
                key=f"{key}-select-chans-{input_path}" if input_path else f"{key}-select-chans"
            )

    # --- Processing ---
    st.markdown("---")
    if st.button("Run Connectivity Analysis", type="primary", disabled=not (input_path and output_dir and is_valid), key=f"{key}-btn"):
        
        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
            except Exception as e:
                st.error(f"Could not create output directory: {e}")
                return

        orig_backend = plt.get_backend()

        try:
            # 1. Load Epochs (always)
            with st.spinner("Loading Epochs..."):
                epochs_data = mne.read_epochs(input_path, preload=True, verbose=False)

            # 2. Optionnal Plotting
            if do_plot_epochs:
                try:
                    try: plt.switch_backend('Qt5Agg')
                    except: plt.switch_backend('TkAgg')
                    
                    st.info("Opening interactive plot on the server. Close the plot window to continue connectivity extraction.")
                    epochs_data.plot(
                        events=epochs_data.events,
                        event_id=epochs_data.event_id,
                        title='Verify Epochs for Connectivity', 
                        show=True, 
                        block=True, 
                        scalings=dict(eeg=50e-6)
                    )
                except Exception as e:
                    st.warning(f"Interactive plot Error (check your display server): {e}")
                finally:
                    try: plt.switch_backend(orig_backend)
                    except: pass
                    
            # 3. Proceed with Extraction
            with st.spinner("Extracting Connectivity power..."):
                subject_name = os.path.splitext(os.path.basename(input_path))[0]
                df_sub = analyze_connectivity(
                    epochs_data=epochs_data,
                    selected_chans=selected_channels,
                    subject_name=subject_name
                )
                    
            if not df_sub.empty:
                # Save CSV
                filename_data = f"{subject_name}_connectivity.csv"
                save_path_data = os.path.join(output_dir, filename_data)
                
                try:
                    # Rename conditions if applicable in the multi-index
                    # analyze_connectivity returns MultiIndex (Subject, Condition, FreqBand)
                    # We can map Condition level
                    if 'Condition' in df_sub.index.names:
                        level_values = df_sub.index.get_level_values('Condition')
                        new_level_values = [CHANNEL_CODES.get(val, val) for val in level_values]
                        
                        # Reconstruct MultiIndex
                        new_index = pd.MultiIndex.from_arrays(
                            [
                                df_sub.index.get_level_values('Subject'),
                                new_level_values,
                                df_sub.index.get_level_values('FreqBand')
                            ],
                            names=df_sub.index.names
                        )
                        df_sub.index = new_index

                    # Save CSV
                    df_sub.to_csv(save_path_data)
                    st.success(f"✅ Connectivity Extraction Complete. Saved to `{save_path_data}`")
                    st.dataframe(df_sub)
                    
                except Exception as e:
                    st.error(f"Error saving outputs: {e}")
            else:
                st.warning("No data extracted. Please check parameters and file.")

        except Exception as e:
            st.error(f"Error processing {input_path}: {e}")
