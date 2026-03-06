
import numpy as np
def resample_data(data, sfreq=200, verbose=True):
    """
    Resample the data to the target frequency.
    """
    
    if verbose:
        print(f"Resampling data to {sfreq} Hz")
        
    return data.resample(sfreq, npad="auto")
