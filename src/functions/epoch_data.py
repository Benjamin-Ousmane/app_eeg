
import mne
import numpy as np
import pandas as pd
from src.constants import config_eeg as cfg

def epoch_data(data, event_id_dict, tmin=-0.2, tmax=1.2, baseline=None, verbose=True):
    """
    Epoch the data based on events and remapping.
    """
    SubName = data.info['subject_info']['his_id'] if data.info['subject_info'] else "Unknown"

    if verbose:
        print(f"Epoching data for {SubName}")

    # Find events (assuming STI 014 exists)
    try:
        events = mne.find_events(data, stim_channel='STI 014', verbose=False)
    except Exception as e:
        print(f"Could not find events on STI 014: {e}")
        return None
    
    translate_dict = event_id_dict # This is the raw.event_id from Load step
    
    new_dict = {}
    new_events = events.copy()
    
  
    val_map = {} # OldCode -> NewCode
    
    for key, value in translate_dict.items():
         # Skip artifacts
         if key in ['D255', 'DIN4', 'DI75', 'DI77', 'DI79', 'net']:
             continue
             
         # Clean key
         digits = ''.join(x for x in key if x.isdigit())
         if digits:
             new_code = int(digits)
             val_map[value] = new_code
             
    # Apply remapping
    # Iterate events and replace values
    for i in range(len(new_events)):
        val = new_events[i, 2]
        if val in val_map:
            new_events[i, 2] = val_map[val]
            
    
    GOOD_TRIGS = [65, 66, 67, 68, 69, 70] # From config_video_EEG.py
    NB_ADD = 5
    WIN_SIZE = 10
    
    new_trigs = []
    sfreq = data.info['sfreq']
    
    for i in range(len(new_events)):
        val = new_events[i, 2]
        if val in GOOD_TRIGS:
            time_sample = new_events[i, 0]
            for j in range(NB_ADD):
                new_time = int(time_sample + (j+1) * WIN_SIZE * sfreq)
                new_trigs.append([new_time, 0, val])
                
    if new_trigs:
        new_trigs = np.array(new_trigs)
        new_events = np.concatenate((new_events, new_trigs), axis=0)
        new_events = new_events[np.argsort(new_events[:, 0])] # Sort by time


    # Subject specific removals
    if SubName == 'CR004_1' and len(new_events) > 6:
        print(f"⚠️ Removing first 6 triggers for {SubName}")
        new_events = new_events[30:] 
        
    elif SubName == 'CR005_2' and len(new_events) > 6:
        print(f"⚠️ Removing triggers 360-389 for {SubName}")
        keep_idx = np.concatenate((np.arange(0, 360), np.arange(390, len(new_events))))
        new_events = new_events[keep_idx, :]

    
    EVENTS_ID = {'Music': 65, 'Noise':66, 'Rest after Music':67, 'Rest after noise':68,
                 'Interact music': 69, 'Interact noise':70}

    # Only pick eeg channels
    picks_eeg = mne.pick_types(data.info, eeg=True, exclude=[])
    
    # Detrend logic
    detrend = None # cfg.erp_detrend

    epochs = mne.Epochs(data, events=new_events, event_id=EVENTS_ID, tmin=tmin, tmax=tmax,
                        baseline=baseline, detrend=detrend, picks=picks_eeg, on_missing='warn',
                        reject=None, preload=True, reject_by_annotation=False)
                        
    if verbose:
        print(f"Created {len(epochs)} epochs.")
        
    return epochs
