
import streamlit as st
from SidebarEEG import SidebarEEG
from src.components import (
    LoadMffFolder, 
    PreprocessEEG,
    IndependentComponentAnalysisEEG,
)

st.set_page_config(page_title="Preprocessing", layout="wide", initial_sidebar_state="expanded")

# Render Global Header & Sidebar
SidebarEEG()

st.title("🧠 Preprocessing")
st.markdown("Preprocess EEG signals from EGI .mff folders or preprocessed .fif files.")

tab_load, tab_filter, tab_ica = st.tabs(["Load .mff folder", "Preprocess", "ICA"])

with tab_load:
    LoadMffFolder()

with tab_filter:
    PreprocessEEG()

with tab_ica:
    IndependentComponentAnalysisEEG()

