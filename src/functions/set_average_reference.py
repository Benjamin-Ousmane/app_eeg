
def set_average_reference(data, projection=False, verbose=True):
    """
    Set EEG reference to average.
    """
    if verbose:
        print("Setting EEG reference to average.")

    data.set_eeg_reference(ref_channels='average', projection=projection, verbose=verbose)
    return data
