import sys
import numpy as np
import pandas as pd
import tensorflow as tf
sys.path.append('..')
from utils.signal_processing import base_filter, preprocess_sqc_data
from utils.channel_selection import is_signal_noisy
from utils.gaze_sqc_model.gaze_sqc_feature_extraction import extract_sqc_features, sqc_window_len_s, sqc_window_stride_s
from utils.gaze_sqc_model.GazeSQCModelTFLite import GazeSQCModelTFLite
from facial_gesture_detection.gaze_detection import lf5_rf6_gaze_params, detect_gaze, gaze_window_len_s, gaze_window_stride_s, REVERSE_EYE_GAZE_MAPPING

#input_fpath = './sample_data/right_eye_gaze_data.csv'
input_fpath = './sample_data/gp_fgd_testing_0.csv'

# Load Gaze Signal Quality Check Model
gaze_sqc_model_fpath = '../utils/gaze_sqc_model/gaze_sqc_model.tflite'
gaze_sqc_feature_means_fpath = '../utils/gaze_sqc_model/gaze_sqc_model_feature_means.npy'
gaze_sqc_feature_stds_fpath = '../utils/gaze_sqc_model/gaze_sqc_model_feature_stds.npy'
gaze_sqc_model = GazeSQCModelTFLite(gaze_sqc_model_fpath, gaze_sqc_feature_means_fpath, gaze_sqc_feature_stds_fpath)

fs = 125 # EXG Sample Rate

if __name__ == '__main__':
    # Load data
    data = pd.read_csv(input_fpath)
    lf5_data = np.array(data['ch1_LF5-FpZ'])
    rf6_data = np.array(data['ch4_RF6-FpZ'])

    # Gaze parameters
    min_dist_from_prev = lf5_rf6_gaze_params['min_dist_from_prev']
    min_duration = lf5_rf6_gaze_params['min_duration']
    max_duration = lf5_rf6_gaze_params['max_duration']
    min_threshold_amp = lf5_rf6_gaze_params['min_threshold_amp']
    max_threshold_amp = lf5_rf6_gaze_params['max_threshold_amp']
    soft_zc_threshold = lf5_rf6_gaze_params['soft_zc_threshold']
    prev_endpoint_timestamp = -1*min_dist_from_prev
    group_endpoints = []
    groupings = []
    detections = []
    
    # Timestamp for next signal quality check
    next_sqc_check_ts = gaze_window_len_s
    for i in range(int(gaze_window_len_s*fs), data.shape[0], int(gaze_window_stride_s*fs)):
        if ((i/fs) >= next_sqc_check_ts) and (i >= int(sqc_window_len_s*fs)):
            next_sqc_check_ts += 1
            # evaluate signal quality
            sqc_window_data_l = lf5_data[i-int(sqc_window_len_s*fs):i]
            sqc_window_data_l = sqc_window_data_l-np.mean(sqc_window_data_l)
            sqc_window_data_l = preprocess_sqc_data(base_filter(sqc_window_data_l, fs), fs)

            sqc_window_data_r = rf6_data[i-int(sqc_window_len_s*fs):i]
            sqc_window_data_r = sqc_window_data_r-np.mean(sqc_window_data_r)
            sqc_window_data_r = preprocess_sqc_data(base_filter(sqc_window_data_r, fs), fs)
            
            window_l_signal_quality = 0 if is_signal_noisy(sqc_window_data_l, fs) else 1
            window_r_signal_quality = 0 if is_signal_noisy(sqc_window_data_r, fs) else 1
            
            correlation = np.corrcoef(sqc_window_data_l, sqc_window_data_r)[0,1]
            if not ((correlation < -0.6) and (window_l_signal_quality == 1) and (window_r_signal_quality == 1)):
                window_l_sqc_feats = extract_sqc_features(sqc_window_data_l, fs)
                window_r_sqc_feats = extract_sqc_features(sqc_window_data_r, fs)
                window_l_signal_quality = 1-(np.round(gaze_sqc_model.predict(np.array(window_l_sqc_feats))).item())
                window_r_signal_quality = 1-(np.round(gaze_sqc_model.predict(np.array(window_r_sqc_feats))).item())
                            
        if (window_l_signal_quality == 1) and (window_r_signal_quality == 1):
            window_time_offset = i/fs
            window_data_l = lf5_data[i-int(gaze_window_len_s*fs):i]
            window_data_r = rf6_data[i-int(gaze_window_len_s*fs):i]
            gazes, group_endpoints, groupings, prev_endpoint_timestamp = detect_gaze(
                        window_data_l, window_data_r, fs, group_endpoints, groupings, prev_endpoint_timestamp, window_time_offset, \
                        min_dist_from_prev, min_duration=min_duration, max_duration=max_duration, min_threshold_amp=min_threshold_amp, \
                        max_threshold_amp=max_threshold_amp, soft_zc_threshold=soft_zc_threshold)
            if len(gazes) > 0:
                print('Gaze detected at time t= {}: {}'.format(window_time_offset, REVERSE_EYE_GAZE_MAPPING[gazes[-1]]))
                detections.append([window_time_offset, REVERSE_EYE_GAZE_MAPPING[gazes[-1]]])
        else:
            print('Left/Right EOG channels not stable for gaze detection')
    
    
    
