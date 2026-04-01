
import os
import mne
def assign_channels(data, raw_fname, subject_name, mapping_dict, montage_ch_names, verbose=True):
    """
    Set channel types and montage on an already loaded EGI raw object.
    """
    if verbose : 
        print(f"Assigning channels for {raw_fname}")
        print(f'Event ID : {data.event_id}')
        print(f'Chan in the file : {data.ch_names}')

    # Mapping
    mapping_raw = mapping_dict

    if verbose:
        print('mapping_raw: ', mapping_raw)

    # Filter mapping for present channels
    present_chans = set(data.ch_names)
    print('present_chans: ', present_chans)
    mapping_filtre = {ch: typ for ch, typ in mapping_raw.items() if ch in present_chans}
    print('mapping_filtre: ', mapping_filtre)

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
            # Force assigning configuration names because montage format does not always match raw names
            montage.ch_names = montage_ch_names
            data.set_montage(montage, match_case=False, on_missing='warn')
            data.info['subject_info'] = {'his_id' : subject_name}
            
            if verbose:
                print('Raw data info ch_names: ', data.info['ch_names'])
                print('chan type : ', data.get_channel_types())
                print('Raw data info channels: ', len(data.info['ch_names']))
                print('Raw data info highpass: ', data.info['highpass'])
                print('Raw data info lowpass: ', data.info['lowpass'])
                print('Raw data info sfreq: ', data.info['sfreq'])


        except Exception as e:
            print(f"Could not set montage from {coordinates_file}: {e}")
            print(f"⚠️ Could not set montage: {e}")
    else:
        print(f"coordinates.xml not found at {coordinates_file}")
        print("⚠️ coordinates.xml not found")

    return data


