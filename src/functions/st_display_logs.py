import streamlit as st
import json

def st_display_logs(log_data, placeholder, key="process_logs", is_final=False):
    """
    Displays the log dictionary as formatted text in the Streamlit placeholder.
    """
    with placeholder.container():
        st.subheader("📝 Processing Log")
        
        display_dict = {}
        display_dict["Subject"] = log_data.get('subject_name', 'Unknown')
        
        process_type = log_data.get('process_type')
        config = log_data.get('config', {})
        
        if process_type == 'preprocess' or process_type is None:
            # Excluded Channels
            if log_data.get('do_exclude_misc'):
                param_misc = log_data.get('param_misc_channels')
                display_dict["Excluded Channels"] = param_misc if param_misc else "None selected"
            elif config.get('do_exclude_misc'):
                display_dict["Excluded Channels"] = "Pending..."
            else:
                display_dict["Excluded Channels"] = False
                
            # Trim
            if log_data.get('do_trim'):
                display_dict["Trim"] = {
                    "start_trigger": log_data.get('param_trim_start'),
                    "dur_before_start_trigger": log_data.get('param_trim_dur_before', 0),
                    "end_trigger": log_data.get('param_trim_end'),
                    "dur_after_end_trigger": log_data.get('param_trim_dur_after', 0)
                }
            elif config.get('do_trim'):
                display_dict["Trim"] = "Pending..."
            else:
                display_dict["Trim"] = False
                
            # Notch Filter
            if log_data.get('do_notch'):
                display_dict["Notch Filter (50Hz)"] = True
            elif config.get('do_notch'):
                display_dict["Notch Filter (50Hz)"] = "Pending..."
            else:
                display_dict["Notch Filter (50Hz)"] = False
                
            # Bandpass Filter
            if log_data.get('do_bandpass'):
                display_dict["Bandpass Filter"] = {
                    "Highpass (Hz)": log_data.get('param_highpass'),
                    "Lowpass (Hz)": log_data.get('param_lowpass')
                }
            elif config.get('do_bandpass'):
                display_dict["Bandpass Filter"] = "Pending..."
            else:
                display_dict["Bandpass Filter"] = False
                
            # Resample
            if log_data.get('do_resample'):
                display_dict["Resample"] = f"{log_data.get('param_sfreq')} Hz"
            elif config.get('do_resample'):
                display_dict["Resample"] = "Pending..."
            else:
                display_dict["Resample"] = False

            # Bad Channels
            if log_data.get('do_manual_bads'):
                marked_bads = log_data.get('marked_bads')
                if marked_bads is not None:
                    display_dict["Bad Channels"] = marked_bads if marked_bads else 'None'
                else:
                    display_dict["Bad Channels"] = "Manual Selection (pending...)"
            elif config.get('do_manual_bads'):
                display_dict["Bad Channels"] = "Pending..."
            else:
                display_dict["Bad Channels"] = False
                
            # Interpolation
            if log_data.get('do_interpolate'):
                display_dict["Interpolation"] = True
            elif config.get('do_interpolate'):
                display_dict["Interpolation"] = "Pending..."
            else:
                display_dict["Interpolation"] = False
                
            # Average Reference
            if log_data.get('do_reference'):
                display_dict["Average Reference"] = True
            elif config.get('do_reference'):
                display_dict["Average Reference"] = "Pending..."
            else:
                display_dict["Average Reference"] = False
                
        if process_type == 'ica' or (process_type is None and 'do_find_blinks' in log_data):
            # Blinks Detection
            if log_data.get('do_find_blinks'):
                blinks_count = log_data.get('blinks_count')
                if blinks_count is not None:
                     display_dict["Blinks Detected"] = int(blinks_count)
                else:
                     display_dict["Blinks Detected"] = True
            elif config.get('do_find_blinks'):
                display_dict["Blinks Detected"] = "Pending..."
            else:
                display_dict["Blinks Detected"] = False
                
            # EOG Proxy
            if log_data.get('do_find_eog'):
                display_dict["EOG Proxy"] = log_data.get('param_eog_ch')
            elif config.get('do_find_eog'):
                display_dict["EOG Proxy"] = "Pending..."
            else:
                display_dict["EOG Proxy"] = False
                
            # ICA
            if log_data.get('do_apply_ica'):
                ica_dict = {
                    "components": log_data.get('param_n_components'),
                    "method": log_data.get('param_method', '')
                }
                final_excludes = log_data.get('ica_excludes')
                if final_excludes is not None:
                    ica_dict["Removed Components"] = final_excludes
                display_dict["ICA"] = ica_dict
            elif config.get('do_apply_ica'):
                display_dict["ICA"] = "Pending..."
            else:
                display_dict["ICA"] = False
        
        # Display as Dictionary/JSON payload
        st.json(display_dict)
        
        if is_final:
            log_str = json.dumps(display_dict, indent=4)
            st.download_button(
                label="Download Log (.json)",
                data=log_str,
                file_name=f"{log_data.get('subject_name', 'subject')}_log.json",
                mime="application/json",
                key=f"{key}_dl_log"
            )
