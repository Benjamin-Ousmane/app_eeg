import streamlit as st
import pandas as pd

def update_sidebar_log():
    if 'eeg_sidebar_placeholder' in st.session_state:
        placeholder = st.session_state['eeg_sidebar_placeholder']
        
        with placeholder.container():
            if 'eeg_process_log' in st.session_state and st.session_state['eeg_process_log']:
                st.subheader("📝 Processing Log")
                
                log_data = st.session_state['eeg_process_log']
                
                # Format the log text
                log_text = f"Subject: {log_data.get('subject_name', 'Unknown')}\n\n"
                
                if log_data.get('do_trim'):
                    log_text += f"- Trimmed: {log_data.get('param_trim_start')} to {log_data.get('param_trim_end')}\n"
                    log_text += f"  (Duration after last trigger: +{log_data.get('param_trim_dur')}s)\n\n"
                    
                if log_data.get('do_notch'):
                    log_text += "- Notch Filter: Applied (50, 100, 150 Hz)\n\n"
                    
                if log_data.get('do_bandpass'):
                    log_text += f"- Bandpass Filter: {log_data.get('param_highpass')}Hz - {log_data.get('param_lowpass')}Hz\n\n"
                    
                if log_data.get('do_resample'):
                    log_text += f"- Resample: down to {log_data.get('param_sfreq')} Hz\n\n"
                    
                if log_data.get('do_manual_bads'):
                    log_text += "- Bad Channels Selection: Manual step enabled\n\n"
                    
                if log_data.get('do_interpolate'):
                    log_text += "- Interpolation: Applied to bad channels\n\n"
                    
                if log_data.get('do_reference'):
                    log_text += "- Reference: Average Reference computed\n\n"
                
                
                # # Download button for the log
                # st.download_button(
                #     label="Download Log (.txt)",
                #     data=log_text,
                #     file_name=f"{log_data.get('subject_name', 'subject')}_preprocess_log.txt",
                #     mime="text/plain",
                #     key="dl_logs_btn"
                # )
            else:
                st.info("Run preprocessing steps to view the log summary here.")

def Sidebar():
    """
    Renders the sidebar documentation and processing logs for EEG pages.
    Should be called at the beginning of the EEG Preprocessing page.
    """
    with st.sidebar:
        st.header("🧠 EEG Preprocessing")
        st.session_state['eeg_sidebar_placeholder'] = st.empty()
        
    update_sidebar_log()
