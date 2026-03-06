import mne
import numpy as np
import pandas as pd

def read_triggers(raw, stim_channels=None, verbose=False):
    """
    Reads and chronologically combines events (triggers) from a list of channels.
    If no channels are provided, lets MNE detect them automatically.
    Formats these events into a DataFrame and a list of options for the user interface.
    
    Returns:
        trigger_df (pd.DataFrame): DataFrame with columns ['idx', 'code', 'time']
    """
    events_list = []
    
    # 1. Event Extraction
    if not stim_channels:
        try:
            if verbose: print("Letting MNE auto-detect stim channel")
            events = mne.find_events(raw, verbose=verbose)
            for ev in events:
                events_list.append({'sample': ev[0], 'code': str(ev[2]), 'time': ev[0] / raw.info['sfreq'], 'mne_val': ev[2]})
        except Exception as e:
            if verbose: print(f"Error finding events: {e}")
            return pd.DataFrame(columns=['idx', 'code', 'time'])
    else:
        try:
            if verbose: print(f"Extracting events from channels: {stim_channels}")
            for ch in stim_channels:
                if ch in raw.ch_names:
                    ch_events = mne.find_events(raw, stim_channel=ch, verbose=False)
                    for ev in ch_events:
                        events_list.append({'sample': ev[0], 'code': ch, 'time': ev[0] / raw.info['sfreq'], 'mne_val': ev[2]})
        except Exception as e:
            if verbose: print(f"Error finding events: {e}")
            return pd.DataFrame(columns=['idx', 'code', 'time'])

    if not events_list:
        return pd.DataFrame(columns=['idx', 'code', 'time'])

    # Create DataFrame and sort chronologically by time
    df = pd.DataFrame(events_list)
    df = df.sort_values('time').reset_index(drop=True)
    df.index.name = 'idx'
    df = df.reset_index()
        
    # Return limited DataFrame for UI
    trigger_df = df[['idx', 'code', 'time']]

    return trigger_df
