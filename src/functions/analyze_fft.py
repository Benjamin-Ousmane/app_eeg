import mne
from mne.time_frequency import psd_array_welch
import numpy as np
import pandas as pd
import os

from src.constants.fft_constants import DEFAULT_FREQ_BANDS, MIN_FFT_SAMPLES, MAX_N_FFT, DEFAULT_FMIN, DEFAULT_FMAX

def analyze_fft(epochs_path, roi_dict=None, subject_name=None):
    """
    Extracts relative PSD for specified ROIs and frequency bands from an epoched FIF file.
    Returns a DataFrame with results per condition.
    """
    if subject_name is None:
        subject_name = os.path.splitext(os.path.basename(epochs_path))[0]

    epochs = mne.read_epochs(epochs_path, proj=False, preload=True, verbose=False)
    
    # If no ROI specified, we compute for every individual eeg channel
    if roi_dict is None or len(roi_dict) == 0:
        eeg_picks = mne.pick_types(epochs.info, eeg=True)
        eeg_names = [epochs.ch_names[p] for p in eeg_picks]
        roi_dict = {ch: [ch] for ch in eeg_names}
        
    conditions = list(epochs.event_id.keys())
    
    results = []
    index_tuples = []

    for cond in conditions:
        try:
            epochs_cond = epochs[cond]
            if len(epochs_cond) == 0:
                continue
                
            # Compute per ROI
            row_data = []
            for roi_name, roi_labels in roi_dict.items():
                band_powers = _get_roi_band_power(epochs_cond, roi_labels, DEFAULT_FREQ_BANDS, DEFAULT_FMIN, DEFAULT_FMAX)
                row_data.extend(band_powers)
                
            results.append(row_data)
            index_tuples.append((subject_name, cond))
        except Exception as e:
            print(f"Skipping condition {cond} due to error: {e}")

    # Build DataFrame
    if not results:
        return pd.DataFrame()

    band_names = list(DEFAULT_FREQ_BANDS.keys())
    columns = []
    for roi_name in roi_dict.keys():
        for b in band_names:
            columns.append(f"{b}_{roi_name}")

    index = pd.MultiIndex.from_tuples(index_tuples, names=["Subject", "Condition"])
    df = pd.DataFrame(results, index=index, columns=columns)
    
    return df


def _get_roi_band_power(epochs, roi_labels, freq_bands, fmin, fmax):
    """
    Computes relative power for each band in the specified ROI.
    Returns a list of powers exactly in the order of freq_bands.
    """
    data = epochs.get_data(copy=False)  # (n_epochs, n_channels, n_times)
    ch_names = epochs.ch_names

    roi_idx = [ch_names.index(ch) for ch in roi_labels if ch in ch_names]
    if not roi_idx:
        return [np.nan] * len(freq_bands)

    n_epochs, n_channels, n_times = data.shape
    total_samples = n_epochs * n_times
    
    if total_samples < MIN_FFT_SAMPLES:
        print(f"Signal too short ({total_samples} samples)")
        return [np.nan] * len(freq_bands)
        
    n_fft = min(MAX_N_FFT, total_samples)
    data_concat = data.transpose(1, 0, 2).reshape(n_channels, total_samples)
    sfreq = epochs.info['sfreq']

    # Compute PSD using Welch
    psd, freqs = psd_array_welch(
        data_concat,
        sfreq=sfreq,
        fmin=fmin,
        fmax=fmax,
        n_fft=n_fft,
        n_per_seg=n_fft,
        verbose=False
    )

    # Convert to relative power per channel
    psd_rel = psd / np.sum(psd, axis=1, keepdims=True)

    band_powers = []
    for band_name, (low, high) in freq_bands.items():
        mask = (freqs >= low) & (freqs < high)
        if mask.sum() == 0:
            roi_power = np.nan
        else:
            roi_power = psd_rel[roi_idx][:, mask].sum(axis=1).mean()
        band_powers.append(roi_power)
        
    return band_powers
