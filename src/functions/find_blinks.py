
import mne

def find_blinks(data, eog_ch_name, verbose=True):
    """
    Find blink events based on EOG channel (or proxy).
    """
    blink_detect_th = 0.00005
    
    if verbose:
        print(f"Finding blinks using channel {eog_ch_name} with threshold {blink_detect_th}...")
        
    eog_events = mne.preprocessing.find_eog_events(data, ch_name=eog_ch_name, thresh=blink_detect_th, verbose=False)
    
    if verbose:
        print(f"Found {len(eog_events)} blink events.")
        
    return eog_events
