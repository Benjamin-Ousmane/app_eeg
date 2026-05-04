import mne
import numpy as np

def bandpass_filter(data, highpass=0.5, highcut=45, verbose=True):
    """
    Apply Bandpass filter.
    """
    filtered_data = data.copy()

    if verbose:
        print(f"Applying Bandpass filter: {highpass}-{highcut} Hz")
    filtered_data.filter(highpass, highcut, method='fir', phase='zero-double', fir_design='firwin2', verbose=verbose)

    return filtered_data
