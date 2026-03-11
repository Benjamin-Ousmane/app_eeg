import mne
import numpy as np

def trim_eeg_data(raw, start_time, end_time, verbose=True):
    """
    Trim EEG data to start at `start_time` and end at `end_time` seconds.
    """
    
    tmin = max(0, start_time)
    tmax = end_time
    
    # Ensure tmax doesn't exceed the actual raw duration
    max_time = raw.times[-1]
    if tmax > max_time:
        if verbose:
            print(f"Warning: Calculated tmax ({tmax:.2f}s) exceeds data duration ({max_time:.2f}s). Trimming to end of data.")
        tmax = max_time
        
    if verbose:
        print(f"Trimming data: tmin={tmin:.2f}s, tmax={tmax:.2f}s")
        
    try:
        raw.crop(tmin=tmin, tmax=tmax)
        if verbose:
            print("Trimming successful.")
    except Exception as e:
        if verbose:
            print(f"Error during cropping: {e}")
            
    return raw
