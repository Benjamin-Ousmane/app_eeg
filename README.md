# Streamlit Desktop App for EEG processing 

## OVERVIEW
This is a **Streamlit** web application 

## RUNNING AN APP 
```sh
streamlit run Home.py 
```

## CREATE AN .EXE APP

# 1. Create the environment
```sh
python -m venv venv_app_eeg --clear
```

```sh
.\venv_app_eeg\Scripts\python -m pip install --upgrade pip
```

# 2. Activate the environment
```sh
.\venv_app_eeg\Scripts\activate
```

# 3. Install dependencies
```sh
.\venv_app_eeg\Scripts\pip install -r requirements.txt
```

# 4. Run the command to generate the build folder
```sh
python -m PyInstaller --clean --noconfirm --onefile --name app_eeg `
--copy-metadata streamlit `
--copy-metadata pandas --copy-metadata pyarrow `
--copy-metadata openpyxl --copy-metadata mne `
--collect-submodules streamlit `
--collect-submodules pandas --collect-submodules pyarrow `
--collect-submodules openpyxl --collect-submodules mne `
--collect-data streamlit `
--collect-data pandas --collect-data pyarrow `
--collect-data openpyxl --collect-data mne `
--hidden-import pandas `
--hidden-import pyarrow `
--hidden-import openpyxl --hidden-import openpyxl.cell `
--hidden-import mne `
--add-data "Home.py;." --add-data "SidebarEEG.py;." --add-data "pages;pages" --add-data "src;src" `
run_app.py
```

# 4. Copy source code in the build folder
The executable file (`app_eeg.exe`) will be available in the `dist/` folder.
You need to copy theses files in the `dist/` folder to make the executable works :
- the folder `pages/` 
- the folder `src/` 
- the file `Home.py`


# Bonus. Clean the environment (if existing)
```sh
Remove-Item -Path .\venv_app_eeg -Recurse -Force
```

## Contributors
- **Benjamin-Ousmane M'Bengue**
- **Alexandra Corneyllie**
- **Bruno Michelot**

## License
