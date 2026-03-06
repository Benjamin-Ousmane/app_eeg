
import os
import mne
from src.constants import config_eeg as cfg

def load_mff(raw_fname, subject_name, verbose=True):
    """
    Load EGI .mff data, set channel types and montage.
    """
    # Load data
    try:
        # data = mne.io.read_raw_egi(raw_fname, preload=True, verbose=verbose)
        data = mne.io.read_raw_egi(raw_fname, eog=None, misc=None, exclude=None, include=None, preload=True, verbose=None)
    except Exception as e:
        print(f"Failed to load {raw_fname}: {e}")
        raise e

    if verbose : 
        print(f"Loading {raw_fname}")
        print(f'Event ID : {data.event_id}')
        print(f'Chan in the file : {data.ch_names}')

    # Determine mapping based on subject name
    if subject_name.startswith('CHE'):
        mapping_raw = cfg.MAPPING_TYPE_CHE
    elif subject_name.startswith('TAI'):
        mapping_raw = cfg.MAPPING_TYPE_TAI
    else:
        mapping_raw = cfg.MAPPING_TYPE

    # Filter mapping for present channels
    present_chans = set(data.ch_names)
    mapping_filtre = {ch: typ for ch, typ in mapping_raw.items() if ch in present_chans}

    # Warn about missing channels
    if len(mapping_filtre) < len(mapping_raw):
        missing = set(mapping_raw) - present_chans
        if verbose:
            print(f"Missing channels in mapping: {missing}")

    # Set channel types
    data.set_channel_types(mapping_filtre)

    # Load and set montage
    coordinates_file = os.path.join(raw_fname, 'coordinates.xml')
    if os.path.exists(coordinates_file):
        try:
            montage = mne.channels.read_dig_egi(coordinates_file)
            
            # Check length match before assigning
            if len(montage.ch_names) == len(cfg.EEG_CHAN_NAMES):
                 montage.ch_names = cfg.EEG_CHAN_NAMES
            else:
                print(f"Montage channel count ({len(montage.ch_names)}) does not match expected ({len(cfg.EEG_CHAN_NAMES)}). Skipping rename.")

            data.set_montage(montage, match_case=False, on_missing='warn')
            
            data.info['subject_info'] = {'his_id' : subject_name}
            if verbose:
                print('Raw data info ch_names: ,%s', data.info['ch_names'])
                print('Raw data info channels: ,%s', len(data.info['ch_names']))
                print('Raw data info highpass: ,%s', data.info['highpass'])
                print('Raw data info lowpass: ,%s', data.info['lowpass'])
                print('Raw data info sfreq: ,%s', data.info['sfreq'])


        except Exception as e:
            print(f"Could not set montage from {coordinates_file}: {e}")
            print(f"⚠️ Could not set montage: {e}")
    else:
        print(f"coordinates.xml not found at {coordinates_file}")
        print("⚠️ coordinates.xml not found")

    return data


