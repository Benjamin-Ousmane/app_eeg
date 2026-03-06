import os
import sys

def main():
    # Forcer le port et désactiver le mode headless pour ouvrir le navigateur
    os.environ["STREAMLIT_SERVER_PORT"] = "8501"
    os.environ["STREAMLIT_SERVER_HEADLESS"] = "false"
    os.environ["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"
    os.environ["STREAMLIT_GLOBAL_DEVELOPMENT_MODE"] = "false"
    os.environ["STREAMLIT_SERVER_FILE_WATCHER_TYPE"] = "none"

    # Détecter si on est dans l'exe PyInstaller ou en dev
    if getattr(sys, "frozen", False):
        base_dir = sys._MEIPASS
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))

    script_path = os.path.join(base_dir, "Home.py")

    # Arguments pour Streamlit
    sys.argv = ["streamlit", "run", script_path, "--server.port", "8501"]

    # Import compatible avec différentes versions de Streamlit
    try:
        from streamlit.web import cli as stcli
    except ImportError:
        from streamlit import cli as stcli

    # Lancer Streamlit (appel bloquant)
    stcli.main()


if __name__ == "__main__":
    main()
