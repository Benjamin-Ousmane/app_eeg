import streamlit as st
from src.components import EpochingEEG, AnalysisFFT, PlotFFT, AnalysisConnectivity, PlotConnectivity
from src.components.Sidebar import Sidebar

st.set_page_config(page_title="Analysis", layout="wide", initial_sidebar_state="expanded")

# Render Global Header & Sidebar
Sidebar()

st.title("📊 Analysis")
st.markdown("Perform EEG data analysis: Epoching, Frequency Analysis (FFT), Connectivity, and Plotting.")

tab_epoching, tab_fft, tab_plot_fft, tab_connectivity, tab_plot_connectivity = st.tabs([
    "Epoching", "FFT Analysis", "Plot FFT", "Connectivity Analysis", "Plot Connectivity"
])

with tab_epoching:
    EpochingEEG()

with tab_fft:
    AnalysisFFT()

with tab_plot_fft:
    PlotFFT()

with tab_connectivity:
    AnalysisConnectivity()

with tab_plot_connectivity:
    PlotConnectivity()
