import mne
import numpy as np

def notch_filter(data, notch_freqs=None, verbose=True):
    """
    Apply Notch filter.
    """
    if notch_freqs is None: notch_freqs = np.arange(50, 200, 50) # 50, 100, 150

    filtered_data = data.copy()

    picks_eeg = mne.pick_types(filtered_data.info, eeg=True)
    if verbose:
        print(f"Applying Notch filter at {notch_freqs} Hz")
    filtered_data.notch_filter(notch_freqs, picks=picks_eeg, filter_length='auto', phase='zero-double', verbose=verbose)

    return filtered_data
