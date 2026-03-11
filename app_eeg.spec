# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files
from PyInstaller.utils.hooks import collect_submodules
from PyInstaller.utils.hooks import copy_metadata

datas = [('Home.py', '.'), ('pages', 'pages'), ('src', 'src')]
hiddenimports = ['pandas', 'pyarrow', 'openpyxl', 'openpyxl.cell', 'mne', 'matplotlib.backends.backend_tkagg', 'matplotlib.backends.backend_qt5agg', 'tkinter']
datas += collect_data_files('streamlit')
datas += collect_data_files('pandas')
datas += collect_data_files('pyarrow')
datas += collect_data_files('openpyxl')
datas += collect_data_files('mne')
datas += copy_metadata('streamlit')
datas += copy_metadata('pandas')
datas += copy_metadata('pyarrow')
datas += copy_metadata('openpyxl')
datas += copy_metadata('mne')
hiddenimports += collect_submodules('streamlit')
hiddenimports += collect_submodules('pandas')
hiddenimports += collect_submodules('pyarrow')
hiddenimports += collect_submodules('openpyxl')
hiddenimports += collect_submodules('mne')


a = Analysis(
    ['run_app.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='app_eeg',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
