import mne
import numpy as np

def crop_raw_to_conditions(raw, events_df, condition_duration):
    """
    Keep only the segments of raw data from event['time'] to event['time'] + condition_duration.
    Concatenates the segments and returns a single raw object.
    Adds MNE Annotations describing the condition to allow robust event mapping later.
    Returns:
       raw_concat (mne.io.Raw)
       event_id (dict)
    """
    raw_segments = []
    event_id_dict = {}
    event_codes = []
    
    for _, row in events_df.iterrows():
        tmin = row['time']
        tmax = tmin + condition_duration
        code_str = str(row['code'])
        code_val = int(row['mne_val'])
        
        event_id_dict[code_str] = code_val
        
        if tmax > raw.times[-1]:
            tmax = raw.times[-1]
            
        if tmin < raw.times[0]:
            tmin = raw.times[0]
            
        if tmin >= tmax:
            continue
            
        # Crop the segment perfectly
        raw_crop = raw.copy().crop(tmin=tmin, tmax=tmax)
        
        raw_segments.append(raw_crop)
        event_codes.append(code_val)
    
    if not raw_segments:
        raise ValueError("No valid segments obtained after cropping to conditions.")
        
    return raw_segments, event_codes, event_id_dict
