import streamlit as st
import pandas as pd

def Sidebar():
    """
    Renders the sidebar documentation and processing logs for EEG pages.
    Should be called at the beginning of the EEG Preprocessing page.
    """
    with st.sidebar:
        st.header("🧠 EEG Preprocessing")
        st.image('src/images/Schematic_EGI.png')
