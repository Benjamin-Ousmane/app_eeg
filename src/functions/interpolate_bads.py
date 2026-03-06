
def interpolate_bads(data, reset_bads=True, verbose=True):
    """
    Interpolate bad channels.
    """
    if verbose:
        print(f"Interpolating bad channels: {data.info['bads']}")

    data.interpolate_bads(reset_bads=reset_bads, verbose=verbose)
    return data
