import mne
import pandas as pd

def read_triggers(raw, stim_channels=None, verbose=False):
    """
    Reads and chronologically combines events (triggers) from raw annotations or channels.
    Prioritizes Annotations (immune to resampling artifacts). Fallbacks to MNE auto-detect or specific channels.
    Formats these events into a DataFrame and a list of options for the user interface.
    
    Returns:
        trigger_df (pd.DataFrame): DataFrame with columns ['idx', 'code', 'time']
    """
    events_list = []
    
    # 1. Try Annotations first (highly robust in MNE for EGI files format)
    if hasattr(raw, 'annotations') and len(raw.annotations) > 0:
        if verbose: print("Extracting events from annotations")
        try:
            events, event_dict = mne.events_from_annotations(raw, verbose=False)
            inv_event_dict = {v: k for k, v in event_dict.items()}
            
            for ev in events:
                desc = inv_event_dict[ev[2]]
                # Filter by user-selected stim channels if provided
                if stim_channels is None or desc in stim_channels:
                    events_list.append({
                        'sample': ev[0], 
                        'code': desc, 
                        'time': (ev[0] - raw.first_samp) / raw.info['sfreq'], 
                        'mne_val': ev[2]
                    })
        except Exception as e:
            if verbose: print(f"Failed to extract from annotations: {e}")
            
    # 2. Fallback to extracting from continuous physical STIM channels
    if not events_list:
        if not stim_channels:
            try:
                if verbose: print("Letting MNE auto-detect stim channel")
                events = mne.find_events(raw, verbose=verbose)
                for ev in events:
                    events_list.append({'sample': ev[0], 'code': str(ev[2]), 'time': (ev[0] - raw.first_samp) / raw.info['sfreq'], 'mne_val': ev[2]})
            except Exception as e:
                if verbose: print(f"Error finding events: {e}")
        else:
            try:
                if verbose: print(f"Extracting events from continuous channels: {stim_channels}")
                for ch in stim_channels:
                    if ch in raw.ch_names:
                        ch_events = mne.find_events(raw, stim_channel=ch, verbose=False)
                        for ev in ch_events:
                            events_list.append({'sample': ev[0], 'code': ch, 'time': (ev[0] - raw.first_samp) / raw.info['sfreq'], 'mne_val': ev[2]})
            except Exception as e:
                if verbose: print(f"Error finding events: {e}")

    # 3. Format Output
    if not events_list:
        return pd.DataFrame(columns=['idx', 'code', 'time'])

    df = pd.DataFrame(events_list)
    df = df.sort_values('time').reset_index(drop=True)
    df.index.name = 'idx'
    df = df.reset_index()
        
    # Return DataFrame for UI
    trigger_df = df[['idx', 'code', 'time', 'mne_val']]
    return trigger_df
