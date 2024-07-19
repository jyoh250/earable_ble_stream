import numpy as np
import scipy
from utils.signal_processing import *

emg_window_len_s, emg_window_stride_s = 1, 1
BP_EVENT_SIG_THRESHOLD = 3
BP_REF_LEN = 2
REF_DECAY_TIME = 3

num_emg_channels = 4
bandpower_trends = [[] for _ in range(num_emg_channels)]
reference_bps = [None]*num_emg_channels
reference_scaled_trends = np.zeros(num_emg_channels)
reference_decays = [REF_DECAY_TIME]*num_emg_channels

def emg_event_exists(multichannel_data, fs):
    global bp_trends, reference_bps, reference_scaled_trends, reference_decays
    detected = False
    emg_freq_band = [20, fs/2]

    emg_data = np.array([preprocess_emg(data, fs) for data in multichannel_data])
    
    for ch_idx in range(emg_data.shape[0]):
        emg_seg = emg_data[ch_idx]
        bp = compute_band_powers(emg_seg, fs, bands=emg_freq_band, normalize=False)[0]
        if len(bandpower_trends[ch_idx]) < BP_REF_LEN:
            bandpower_trends[ch_idx].append(bp)
        else:
            bandpower_trends[ch_idx][:-1] = bandpower_trends[ch_idx][1:]
            bandpower_trends[ch_idx][-1] = bp
        amplitude_mask = 1 if (np.max(np.abs(emg_seg)) > 10) else 0
        if reference_bps[ch_idx] is None:
            reference_bps[ch_idx] = bp
        reference_scaled_bp = bp/reference_bps[ch_idx]
        reference_scaled_trends[ch_idx] = reference_scaled_bp*amplitude_mask
        if (reference_scaled_bp < BP_EVENT_SIG_THRESHOLD) or (reference_decays[ch_idx] <= 0):
            reference_bps[ch_idx] = np.min(bandpower_trends[ch_idx])
            reference_decays[ch_idx] = REF_DECAY_TIME
        reference_decays[ch_idx] -= 1
    if np.any(reference_scaled_trends >= BP_EVENT_SIG_THRESHOLD):
          detected = True

    return detected
