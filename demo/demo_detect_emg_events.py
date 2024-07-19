import os
import sys
import numpy as np
import pandas as pd
import tensorflow as tf
sys.path.append('..')
from utils.WindowFiltering import *
from utils.signal_processing import base_filter, preprocess_sqc_data
from utils.channel_selection import is_signal_noisy
from facial_gesture_detection.emg_event_detection import emg_window_len_s, emg_window_stride_s, emg_event_exists    

sid = '98115495-da25-4e5a-9215-0a7605f261ca_1648760464_7477203547A6'
input_fpath = '/Users/galenpogoncheff/Documents/DATA/earable_data/integration/gaze_blink_emg/{}/RAW/afe/{}.csv'.format(sid, sid)
fs = 125 # EXG Sample Rate

if __name__ == '__main__':
    # Load data
    data = pd.read_csv(input_fpath)
    lf5_data = np.array(data['CH1'])
    rf6_data = np.array(data['CH4'])
    otel_data = np.array(data['CH2'])
    oter_data = np.array(data['CH5'])
    
    emg_events = []
    
    n_samples = len(lf5_data)
    for i in range(int(emg_window_len_s*fs), n_samples, int(emg_window_stride_s*fs)):
        lf5_window = np.array(lf5_data[i-int(emg_window_len_s*fs):i])
        rf6_window = np.array(rf6_data[i-int(emg_window_len_s*fs):i])
        otel_window = np.array(otel_data[i-int(emg_window_len_s*fs):i])
        oter_window = np.array(oter_data[i-int(emg_window_len_s*fs):i])
        emg_event = emg_event_exists([lf5_window, rf6_window, otel_window, oter_window], fs)
        if emg_event:
            print('t = {:.3f} : EMG event'.format(i/fs))
            emg_events.append([i/fs, 'EMG Event'])
            
    # save data
    output_fpath = os.path.join('/', *input_fpath.split('/')[:-3], '{}_emg_event_results.csv'.format(sid))
    detections_df = pd.DataFrame(data=np.array(emg_events), columns=['Time (s)', 'Event'])
    detections_df.to_csv(output_fpath, index=False)