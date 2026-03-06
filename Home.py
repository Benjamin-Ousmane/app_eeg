import streamlit as st
import warnings
from SidebarEEG import SidebarEEG

# Suppress matplotlib/nilearn backend warnings
warnings.filterwarnings("ignore", message="You are using the 'agg' matplotlib backend")
warnings.filterwarnings("ignore", module="nilearn")

st.set_page_config(page_title="APP EEG", layout="wide", initial_sidebar_state="expanded")

# Render Global Header & Sidebar
SidebarEEG()

st.title("APP EEG")

st.info("Select a page from the sidebar to access a module.")


st.markdown("""
- **1.Preprocessing**: 
    Preprocess EEG signals from EGI .mff folders.
- **2.Analysis - FFT**: 
    Calculate the FFT of EEG signals from EGI .mff folders.
""")

