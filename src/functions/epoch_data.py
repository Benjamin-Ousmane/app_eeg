import mne
import numpy as np
from src.constants import DEFAULT_WINDOW_SIZE

def epoch_data(data, event_id_list=None, event_dict=None, window_size=DEFAULT_WINDOW_SIZE, baseline=None, detrend=None, verbose=True):
    """
    Epoch the EEG data using fixed-length windows.
    If data is a list of Raw objects (cropped conditions), epochs them individually to prevent boundary drift.
    Returns a concatenated mne.Epochs object.
    """
    if isinstance(data, list):
        epochs_list = []
        for i, raw_seg in enumerate(data):
            code_val = event_id_list[i] if event_id_list else 1
            code_str = [k for k, v in event_dict.items() if v == code_val][0] if event_dict else str(code_val)
            
            events = mne.make_fixed_length_events(raw_seg, id=code_val, duration=window_size)
            if len(events) == 0:
                continue
                
            picks_eeg = mne.pick_types(raw_seg.info, eeg=True, exclude=[])
            eps = mne.Epochs(
                raw_seg, 
                events=events, 
                event_id={code_str: code_val}, 
                tmin=0.0, 
                tmax=window_size, 
                baseline=baseline, 
                detrend=detrend, 
                picks=picks_eeg, 
                preload=True
            )
            epochs_list.append(eps)
            
        if not epochs_list:
            return None
            
        epochs_concat = mne.concatenate_epochs(epochs_list)
        return epochs_concat
    else:
        # Full entire raw signal
        events = mne.make_fixed_length_events(data, id=1, duration=window_size)
        picks_eeg = mne.pick_types(data.info, eeg=True, exclude=[])
        eps = mne.Epochs(
            data, 
            events=events, 
            event_id={'Signal': 1}, 
            tmin=0.0, 
            tmax=window_size, 
            baseline=baseline, 
            detrend=detrend, 
            picks=picks_eeg, 
            preload=True
        )
        return eps

