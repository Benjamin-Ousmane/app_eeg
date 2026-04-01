import streamlit as st
from src.components import EpochingEEG, AnalysisFFT, PlotFFT
from src.components.Sidebar import Sidebar

st.set_page_config(page_title="Analysis", layout="wide", initial_sidebar_state="expanded")

# Render Global Header & Sidebar
Sidebar()

st.title("📊 Analysis")
st.markdown("Perform EEG data analysis: Epoching, Frequency Analysis (FFT), and Plotting.")

tab_epoching, tab_fft, tab_plot = st.tabs(["Epoching", "FFT Analysis", "Plot FFT"])

with tab_epoching:
    EpochingEEG()

with tab_fft:
    AnalysisFFT()

with tab_plot:
    PlotFFT()
