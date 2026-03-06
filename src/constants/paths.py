import os
import sys

# Root 
def get_app_root() -> str:
    # Exe mode with Pyinstaller
    if getattr(sys, "frozen", False):
        return os.path.abspath(os.path.dirname(sys.executable))
    # Dev mode with `streamlit run Home.py`
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

APP_ROOT = get_app_root()

