
import streamlit as st
from SidebarEEG import SidebarEEG
from src.components import (
    EpochingEEG
)

st.set_page_config(page_title="FFT", layout="wide", initial_sidebar_state="expanded")

# Render Global Header & Sidebar
SidebarEEG()

st.title("🧠 FFT")
st.markdown("Calculate the FFT of EEG signals from EGI .mff folders or preprocessed .fif files.")

EpochingEEG()
