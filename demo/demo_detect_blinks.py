import sys
import numpy as np
import pandas as pd
import tensorflow as tf
sys.path.append('..')
from utils.WindowFiltering import *
from utils.signal_processing import base_filter, preprocess_sqc_data
from utils.channel_selection import is_signal_noisy
from facial_gesture_detection.blink_detection import blink_window_len_s, blink_window_stride_s, blink_search_region_size, candidate_blink_region, get_blink_peak_inds

input_fpath = './sample_data/gp_blink_10.csv'
fs = 125 # EXG Sample Rate

# Window parameters for evalauting signal quality
sqc_window_len_s = 3
sqc_window_stride_s = 1

if __name__ == '__main__':
    # Load data
    data = pd.read_csv(input_fpath)
    otel_data = np.array(data['ch2_OTE_L-FpZ'])
    oter_data = np.array(data['ch5_OTE_R-FpZ'])

    # Blink parameters
    blink_eogl_hist = []
    blink_eogr_hist = []
    blink_eogl_filter = WindowFilter([WindowIIRNotchFilter(60, 12, fs), \
                                      WindowIIRNotchFilter(50, 10, fs), \
                                      WindowButterBandpassFilter(2, 0.1, 10, fs)])
    blink_eogr_filter = WindowFilter([WindowIIRNotchFilter(60, 12, fs), \
                                      WindowIIRNotchFilter(50, 10, fs), \
                                      WindowButterBandpassFilter(2, 0.1, 10, fs)])
    candidate_blink_regions = []
    detected_blink_indices = []
    
    # Timestamp for next signal quality check
    next_sqc_check_ts = blink_window_len_s
    window_l_signal_quality, window_r_signal_quality = 0, 0
    for i in range(int(blink_window_len_s*fs), data.shape[0], int(blink_window_stride_s*fs)):
        if ((i/fs) >= next_sqc_check_ts) and (i >= int(sqc_window_len_s*fs)):
            next_sqc_check_ts += 1
            # evaluate signal quality
            sqc_window_data_l = otel_data[i-int(sqc_window_len_s*fs):i]
            sqc_window_data_l = sqc_window_data_l-np.mean(sqc_window_data_l)
            sqc_window_data_l = preprocess_sqc_data(base_filter(sqc_window_data_l, fs), fs)

            sqc_window_data_r = oter_data[i-int(sqc_window_len_s*fs):i]
            sqc_window_data_r = sqc_window_data_r-np.mean(sqc_window_data_r)
            sqc_window_data_r = preprocess_sqc_data(base_filter(sqc_window_data_r, fs), fs)
            
            window_l_signal_quality = 0 if is_signal_noisy(sqc_window_data_l, fs) else 1
            window_r_signal_quality = 0 if is_signal_noisy(sqc_window_data_r, fs) else 1
            
        if (window_l_signal_quality == 1) and (window_r_signal_quality == 1):
            window_data_l = -1*np.array(otel_data[i-int(blink_window_len_s*fs):i])
            window_data_r = -1*np.array(oter_data[i-int(blink_window_len_s*fs):i])
            blink_eogl_hist += list(blink_eogl_filter.filter_data(window_data_l))
            blink_eogr_hist += list(blink_eogr_filter.filter_data(window_data_r))
            if candidate_blink_region(blink_eogl_hist[-1*int(blink_window_len_s*fs):], \
                                      blink_eogr_hist[-1*int(blink_window_len_s*fs):]):
                # Compute endpoints for candidate region.  Total region will be blink_search_region_size seconds in duration
                # The endpoint may be at a timestamp in the future, and we will process the candidate once that time is reached
                midpoint = int(len(blink_eogl_hist)-((blink_window_len_s*fs)/2))
                region_extension = int((blink_search_region_size/2)*fs)
                candidate_start_idx, candidate_end_idx = max(0, midpoint-region_extension), midpoint+region_extension
                candidate_blink_regions.append([candidate_start_idx, candidate_end_idx])

            expired_candidate_timestamps = []
            for candidate_idx, [start, end] in enumerate(candidate_blink_regions):
                # Maximum length of candidate_blink_regions is (region_duration/window_len_s)/2
                if len(blink_eogl_hist) >= end:
                    # We have access to the full candidate region data
                    expired_candidate_timestamps.append([start, end])
                    eogl_seg = blink_eogl_hist[start:end]
                    eogr_seg = blink_eogr_hist[start:end]
                    blink_peak_inds = get_blink_peak_inds(eogl_seg, eogr_seg, fs, start_idx=start, lr_correlation_thresh=0.5)
                    for ind in blink_peak_inds:
                        if len(detected_blink_indices) == 0:
                            print('\nBlink detected\n')
                            detected_blink_indices.append(ind)
                        else:
                            if ind > detected_blink_indices[-1]:
                                print('\nBlink detected\n')
                                detected_blink_indices.append(ind)
            for expired_candidate_timestamp in expired_candidate_timestamps:
                candidate_blink_regions.remove(expired_candidate_timestamp)
                
        else:
            print('Left/Right EOG channels not stable for blink detection')
            
        # save data