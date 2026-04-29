import os
import numpy as np
import pandas as pd
import mne
from scipy.spatial.distance import pdist, squareform
from mne_connectivity import spectral_connectivity_epochs

from src.constants.connectivity_constants import DEFAULT_FREQ_BANDS, DEFAULT_CON_METHOD, DEFAULT_CON_TMIN

def analyze_connectivity(epochs_data, selected_chans=None, subject_name=None):
    """
    Extracts spectral connectivity for specified channels and frequency bands from an epoched FIF file.
    Returns a DataFrame with short, mid, and long distance connectivity per condition and band.
    """
    if subject_name is None:
        subject_name = "Subject"
    
    # Define channels to use
    if selected_chans is None or len(selected_chans) == 0:
        chans_names = epochs_data.ch_names
    else:
        chans_names = [ch for ch in selected_chans if ch in epochs_data.ch_names]
        
    n_chans = len(chans_names)
    if n_chans < 2:
        print("Not enough channels to compute connectivity.")
        return pd.DataFrame()

    # Calculate distance matrix & quartiles
    montage = mne.channels.make_standard_montage('GSN-HydroCel-128')
    pos_dict = montage.get_positions()['ch_pos']
    common_chs = [ch for ch in chans_names if ch in pos_dict]
    
    if len(common_chs) < 2:
        print("Not enough channels with known positions to compute spatial distances.")
        return pd.DataFrame()
        
    pos = np.array([pos_dict[ch] for ch in common_chs])
    dist_mat = squareform(pdist(pos))
    dists = dist_mat[np.triu_indices_from(dist_mat, k=1)]
    q1, q3 = np.percentile(dists, [25, 75])

    conditions = list(epochs_data.event_id.keys())
    summary = []
    index_tuples = []

    for cond in conditions:
        try:
            epochs_cond = epochs_data[cond]
            if len(epochs_cond) == 0:
                continue
                
            sel = epochs_cond
            if selected_chans is not None and len(selected_chans) > 0:
                sel = sel.pick_channels(chans_names, ordered=True)

            for band_name, (fmin, fmax) in DEFAULT_FREQ_BANDS.items():
                con_data = spectral_connectivity_epochs(
                    sel,
                    method=DEFAULT_CON_METHOD,
                    mode='multitaper',
                    sfreq=epochs_data.info['sfreq'],
                    fmin=fmin, fmax=fmax,
                    faverage=True,
                    tmin=DEFAULT_CON_TMIN,
                    mt_adaptive=False,
                    n_jobs=1,
                    verbose=False
                )
                cm_full = con_data.get_data(output="dense")[:, :, 0]
                cm_sym = (cm_full + cm_full.T) / 2.0

                chans_local = sel.ch_names
                idx = [chans_local.index(ch) for ch in common_chs]
                cm = cm_sym[np.ix_(idx, idx)]
                triu = np.triu_indices_from(cm, k=1)
                vals = cm[triu]
                dist_vals = dist_mat[np.ix_(idx, idx)][triu]

                short_mask = dist_vals < q1
                mid_mask = (dist_vals >= q1) & (dist_vals < q3)
                long_mask = dist_vals >= q3

                global_mean = vals.mean() if len(vals) > 0 else np.nan
                short_mean = vals[short_mask].mean() if short_mask.any() else np.nan
                mid_mean = vals[mid_mask].mean() if mid_mask.any() else np.nan
                long_mean = vals[long_mask].mean() if long_mask.any() else np.nan

                summary.append([global_mean, short_mean, mid_mean, long_mean])
                index_tuples.append((subject_name, cond, band_name))
                
        except Exception as e:
            print(f"Skipping condition {cond} due to error: {e}")

    if not summary:
        return pd.DataFrame()

    columns = ["Connectivity", "ShortDistQ1", "MidDistQ1Q3", "LongDistQ3"]
    index = pd.MultiIndex.from_tuples(index_tuples, names=["Subject", "Condition", "FreqBand"])
    df = pd.DataFrame(summary, index=index, columns=columns)
    
    return df
