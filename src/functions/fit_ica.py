
import mne
from mne.preprocessing import ICA
import numpy as np

def fit_ica(data, n_components=10, method='fastica', random_state=23, verbose=True):
    """
    Fit ICA to the data.
    """
    if verbose:
        print(f"Fitting ICA with {n_components} components using {method}...")
        
    # Filter for fitting (highpass 1Hz is recommended for ICA)
    # cleaning.py: datacopy = data.copy().filter(l_freq=1., h_freq=None)
    # We should probably do this highpass on a copy for the fit
    data_for_fit = data.copy().filter(l_freq=1.0, h_freq=None, verbose=False)
    
    ica = ICA(n_components=n_components, method=method, random_state=random_state)
    
    # Exclude bad channels from fitting
    picks = mne.pick_types(data_for_fit.info, meg=False, eeg=True, eog=False, stim=False, exclude='bads')
    
    ica.fit(data_for_fit, picks=picks, reject_by_annotation=True)
    
    if verbose:
        print(f"ICA Fit Complete: {ica}")
        
    return ica
