import os
import sys
import signal
import time
import copy
import asyncio
import threading
import keyboard
import numpy as np
import tensorflow as tf
from BLEScan import get_ble_device_address
from BLEBleak import BLE_device_instance
from params import *
from Experiment import Experiment
from utils.signal_processing import notch_filter, butter_bandpass_lfilter, base_filter, preprocess_sqc_data
from utils.channel_selection import is_signal_noisy
from utils.WindowFiltering import *
from utils.gaze_sqc_model.gaze_sqc_feature_extraction import extract_sqc_features, sqc_window_len_s, sqc_window_stride_s
from facial_gesture_detection.gaze_detection import lf5_rf6_gaze_params, detect_gaze, gaze_window_len_s, gaze_window_stride_s, REVERSE_EYE_GAZE_MAPPING
from facial_gesture_detection.blink_detection import blink_window_len_s, blink_window_stride_s, blink_search_region_size, candidate_blink_region, get_blink_peak_inds
from facial_gesture_detection.emg_event_detection import emg_window_len_s, emg_window_stride_s, emg_event_exists
import matplotlib.pyplot as plt
from matplotlib.widgets import Button

def ble_initializer(address):
    asyncio.run(Ble_stack.main(address))
    
def switch_eeg_channel(event):
    global eeg_channel_index
    eeg_channel_index = (eeg_channel_index+1)%num_eeg_channels
    
def exit_signal_handler(sig, frame):
    global expected_sequence_number, DATA_SAVED
    print('Exiting...')
    
    if not DATA_SAVED:
        # Save any additionall EEG data still in the raw data buffer
        remaining_eeg_data = copy.deepcopy(Ble_stack.raw_eeg_data)
        remaining_eeg_pc_timestamps = copy.deepcopy(Ble_stack.raw_eeg_pc_timestamps)
        while len(remaining_eeg_data) > 0:
            packet_data = remaining_eeg_data.pop(0)
            pc_packet_timestamp = remaining_eeg_pc_timestamps.pop(0)
            timestamp, seq_num, channel_data = Ble_stack.get_data_from_eeg_binary_packet(packet_data, n_channels=num_eeg_channels)
            if expected_sequence_number is None:
                expected_sequence_number = (seq_num+1)%256
            else:
                if seq_num != expected_sequence_number:
                    print('Missing or Duplicate packet')
                    continue
                else:
                    experiment.add_eeg_data(channel_data, pc_packet_timestamp)
                    expected_sequence_number = (expected_sequence_number+1)%256

        # Save IMU data still in the raw data buffer
        remaining_imu_data = copy.deepcopy(Ble_stack.raw_imu_data)
        remaining_imu_pc_timestamps = copy.deepcopy(Ble_stack.raw_imu_pc_timestamps)
        while len(remaining_imu_data) > 0:
            packet_data = remaining_imu_data.pop(0)
            pc_packet_timestamp = remaining_imu_pc_timestamps.pop(0)
            timestamp, data = Ble_stack.get_data_from_imu_binary_packet(packet_data, n_channels=num_imu_channels)
            experiment.add_imu_data(data, pc_packet_timestamp)

        # Save PPG data still in the raw data buffer
        remaining_ppg_data = copy.deepcopy(Ble_stack.raw_ppg_data)
        remaining_ppg_pc_timestamps = copy.deepcopy(Ble_stack.raw_ppg_pc_timestamps)
        while len(remaining_ppg_data) > 0:
            packet_data = remaining_ppg_data.pop(0)
            pc_packet_timestamp = remaining_ppg_pc_timestamps.pop(0)
            timestamp, data = Ble_stack.get_data_from_ppg_binary_packet(packet_data, n_channels=num_ppg_channels)
            experiment.add_ppg_data(data, pc_packet_timestamp)

        experiment.save_data()
        DATA_SAVED = True
        print('Data saved')
        
    Ble_stack.close()
    sys.exit(0)
    
def keyboard_event(event):
    if event.name in event_key_bindings.keys():
        experiment.add_event_timestamp([time.time(), event_key_bindings[event.name]])

def process_emg_data():
    data_processing_time = time.time()
    old_emg_data_len = experiment.eeg_data_size
    while data_is_processing:
        new_emg_samples = experiment.eeg_data_size - old_emg_data_len
        if (new_emg_samples >= int(emg_window_stride_s*eeg_sampling_rate)) and (experiment.eeg_data_size >= int(emg_window_len_s*eeg_sampling_rate)):
            lf5_window = np.array(experiment.eeg_data[experiment.eeg_data_size-int(emg_window_len_s*eeg_sampling_rate):experiment.eeg_data_size,0])
            rf6_window = np.array(experiment.eeg_data[experiment.eeg_data_size-int(emg_window_len_s*eeg_sampling_rate):experiment.eeg_data_size,3])
            #otel_window = np.array(experiment.eeg_data[experiment.eeg_data_size-int(emg_window_len_s*eeg_sampling_rate):experiment.eeg_data_size,1])
            #oter_window = np.array(experiment.eeg_data[experiment.eeg_data_size-int(emg_window_len_s*eeg_sampling_rate):experiment.eeg_data_size,4])
            emg_event = emg_event_exists([lf5_window, rf6_window], eeg_sampling_rate)
            if emg_event:
    	        print('\nEMG event\n')
            old_emg_data_len = experiment.eeg_data_size
        time.sleep(0.05)
        
def process_eog_data():
    data_processing_time = time.time()
    
    # Gaze parameters
    min_dist_from_prev = lf5_rf6_gaze_params['min_dist_from_prev']
    min_duration = lf5_rf6_gaze_params['min_duration']
    max_duration = lf5_rf6_gaze_params['max_duration']
    min_threshold_amp = lf5_rf6_gaze_params['min_threshold_amp']
    max_threshold_amp = lf5_rf6_gaze_params['max_threshold_amp']
    soft_zc_threshold = lf5_rf6_gaze_params['soft_zc_threshold']
    group_endpoints = []
    groupings = []
    prev_endpoint_timestamp = -1*min_dist_from_prev
    
    # Blink parameters
    blink_eogl_hist = []
    blink_eogr_hist = []
    blink_eogl_filter = WindowFilter([WindowIIRNotchFilter(60, 12, eeg_sampling_rate), \
                                      WindowIIRNotchFilter(50, 10, eeg_sampling_rate), \
                                      WindowButterBandpassFilter(2, 0.1, 10, eeg_sampling_rate)])
    blink_eogr_filter = WindowFilter([WindowIIRNotchFilter(60, 12, eeg_sampling_rate), \
                                      WindowIIRNotchFilter(50, 10, eeg_sampling_rate), \
                                      WindowButterBandpassFilter(2, 0.1, 10, eeg_sampling_rate)])
    candidate_blink_regions = []
    detected_blink_indices = []
    
    # Signal quality indicators for lf5, rf5, otel, oter. 0 indicates noisy, 1 indicates OK
    lf5_signal_quality = 0
    rf6_signal_quality = 0
    otel_signal_quality = 0
    oter_signal_quality = 0
    
    old_sqc_data_len = experiment.eeg_data_size
    old_gaze_data_len = experiment.eeg_data_size
    old_blink_data_len = experiment.eeg_data_size
    while data_is_processing:
        new_sqc_samples = experiment.eeg_data_size - old_sqc_data_len
        new_gaze_samples = experiment.eeg_data_size - old_gaze_data_len
        new_blink_samples = experiment.eeg_data_size - old_blink_data_len
        
        # Perform Signal Quality Analysis
        if (new_sqc_samples >= int(sqc_window_stride_s*eeg_sampling_rate)) and (experiment.eeg_data_size >= int(sqc_window_len_s*eeg_sampling_rate)):
            lf5_window = np.array(experiment.eeg_data[experiment.eeg_data_size-int(sqc_window_len_s*eeg_sampling_rate):experiment.eeg_data_size,0])
            lf5_window = lf5_window-np.mean(lf5_window)
            lf5_window = preprocess_sqc_data(base_filter(lf5_window, eeg_sampling_rate), eeg_sampling_rate)

            rf6_window = np.array(experiment.eeg_data[experiment.eeg_data_size-int(sqc_window_len_s*eeg_sampling_rate):experiment.eeg_data_size,3])
            rf6_window = rf6_window-np.mean(rf6_window)
            rf6_window = preprocess_sqc_data(base_filter(rf6_window, eeg_sampling_rate), eeg_sampling_rate)
            
            otel_window = np.array(experiment.eeg_data[experiment.eeg_data_size-int(sqc_window_len_s*eeg_sampling_rate):experiment.eeg_data_size,1])
            otel_window = otel_window-np.mean(otel_window)
            otel_window = preprocess_sqc_data(base_filter(otel_window, eeg_sampling_rate), eeg_sampling_rate)
            
            oter_window = np.array(experiment.eeg_data[experiment.eeg_data_size-int(sqc_window_len_s*eeg_sampling_rate):experiment.eeg_data_size,4])
            oter_window = oter_window-np.mean(oter_window)
            oter_window = preprocess_sqc_data(base_filter(oter_window, eeg_sampling_rate), eeg_sampling_rate)
            
            lf5_signal_quality = 0 if is_signal_noisy(lf5_window, eeg_sampling_rate) else 1
            rf6_signal_quality = 0 if is_signal_noisy(rf6_window, eeg_sampling_rate) else 1
            otel_signal_quality = 0 if is_signal_noisy(otel_window, eeg_sampling_rate) else 1
            oter_signal_quality = 0 if is_signal_noisy(oter_window, eeg_sampling_rate) else 1

            # Further analyze signal quality contrainst of LF5 and RF6 channels for gaze detection
            correlation = np.corrcoef(lf5_window, rf6_window)[0,1]
            if not ((correlation < -0.6) and (lf5_signal_quality == 1) and (rf6_signal_quality == 1)):
                lf5_sqc_feats = extract_sqc_features(lf5_window, eeg_sampling_rate)
                lf5_sqc_feats = (lf5_sqc_feats-gaze_sqc_feature_means)/gaze_sqc_feature_stds
                
                rf6_sqc_feats = extract_sqc_features(rf6_window, eeg_sampling_rate)
                rf6_sqc_feats = (rf6_sqc_feats-gaze_sqc_feature_means)/gaze_sqc_feature_stds
                
                lf5_signal_quality, rf6_signal_quality = 1-(np.round(gaze_sqc_model.predict(np.array([lf5_sqc_feats, rf6_sqc_feats])).flatten()))
            
            print('Signal Qualities [LF5, RF6, OTEL, OTER]: {}'.format([lf5_signal_quality, rf6_signal_quality, otel_signal_quality, oter_signal_quality]))
            old_sqc_data_len = experiment.eeg_data_size

        # Perform Blink Detection
        blink_detection_ready = (otel_signal_quality == 1) \
                                and (oter_signal_quality == 1) \
                                and (new_blink_samples >= int(blink_window_stride_s*eeg_sampling_rate)) \
                                and (experiment.eeg_data_size >= int(blink_window_len_s*eeg_sampling_rate))
        if blink_detection_ready:
            otel_window = -1*np.array(experiment.eeg_data[old_blink_data_len:experiment.eeg_data_size,1])
            oter_window = -1*np.array(experiment.eeg_data[old_blink_data_len:experiment.eeg_data_size,4])
            old_blink_data_len = experiment.eeg_data_size
            blink_eogl_hist += list(blink_eogl_filter.filter_data(otel_window))
            blink_eogr_hist += list(blink_eogr_filter.filter_data(oter_window))
            if candidate_blink_region(blink_eogl_hist[-1*int(blink_window_len_s*eeg_sampling_rate):], \
                                      blink_eogr_hist[-1*int(blink_window_len_s*eeg_sampling_rate):]):
                # Compute endpoints for candidate region.  Total region will be blink_search_region_size seconds in duration
                # The endpoint may be at a timestamp in the future, and we will process the candidate once that time is reached
                midpoint = int(len(blink_eogl_hist)-((blink_window_len_s*eeg_sampling_rate)/2))
                region_extension = int((blink_search_region_size/2)*eeg_sampling_rate)
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
                    blink_peak_inds = get_blink_peak_inds(eogl_seg, eogr_seg, eeg_sampling_rate, start_idx=start, lr_correlation_thresh=0.5)
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

        # Perform Gaze Detection
        gaze_detection_ready = (lf5_signal_quality == 1) \
                               and (rf6_signal_quality == 1) \
                               and (new_gaze_samples >= int(gaze_window_stride_s*eeg_sampling_rate)) \
                               and (experiment.eeg_data_size >= int(gaze_window_len_s*eeg_sampling_rate))
        if gaze_detection_ready:
            window_time_offset = experiment.eeg_data_size/eeg_sampling_rate
            lf5_window = np.array(experiment.eeg_data[experiment.eeg_data_size-int(gaze_window_len_s*eeg_sampling_rate):experiment.eeg_data_size,0])
            rf6_window = np.array(experiment.eeg_data[experiment.eeg_data_size-int(gaze_window_len_s*eeg_sampling_rate):experiment.eeg_data_size,3])
            gazes, group_endpoints, groupings, prev_endpoint_timestamp = detect_gaze(
                                        lf5_window, rf6_window, eeg_sampling_rate, group_endpoints, groupings, prev_endpoint_timestamp, window_time_offset, \
                                        min_dist_from_prev, min_duration=min_duration, max_duration=max_duration, min_threshold_amp=min_threshold_amp, \
                                        max_threshold_amp=max_threshold_amp, soft_zc_threshold=soft_zc_threshold)
            if len(gazes) > 0:
                print('\n{}\n'.format(REVERSE_EYE_GAZE_MAPPING[gazes[-1]]))
            old_gaze_data_len = experiment.eeg_data_size
            
        '''
        if (new_emg_samples >= int(0.5*eeg_sampling_rate)) and (experiment.eeg_data_size >= int(1*eeg_sampling_rate)):
            lf5_window = np.array(experiment.eeg_data[experiment.eeg_data_size-int(1*eeg_sampling_rate):experiment.eeg_data_size,0])
            rf6_window = np.array(experiment.eeg_data[experiment.eeg_data_size-int(1*eeg_sampling_rate):experiment.eeg_data_size,3])
            otel_window = np.array(experiment.eeg_data[experiment.eeg_data_size-int(1*eeg_sampling_rate):experiment.eeg_data_size,1])
            emg_event = emg_event_exists(lf5_window, eeg_sampling_rate)
            if emg_event:
                print('EMG event')
            old_emg_data_len = experiment.eeg_data_size
        
        if (sqcs[0] == 0) and (new_alpha_samples >= int(1*eeg_sampling_rate)) and (experiment.eeg_data_size >= int(1*eeg_sampling_rate)):
            lf5_window = np.array(experiment.eeg_data[experiment.eeg_data_size-int(1*eeg_sampling_rate):experiment.eeg_data_size,0])
            #lf5_window = notch_filter(lf5_window, eeg_sampling_rate, 60, 12)
            #lf5_window = butter_bandpass_lfilter(lf5_window, 0.5, 35, eeg_sampling_rate, order=1)
            alpha_event = alpha_event_exists(lf5_window, eeg_sampling_rate)
            if alpha_event:
                print('ALPHA event')
            old_alpha_data_len = experiment.eeg_data_size
        '''
            
        # detect blinks
        time.sleep(0.005)
    


eeg_channel_index = 0
eeg_channel_filters = []
for _ in range(num_eeg_channels):
    eeg_channel_filters.append(WindowFilter([WindowIIRNotchFilter(60, 12, eeg_sampling_rate), \
                                             WindowButterBandpassFilter(1, 0.5, 20, eeg_sampling_rate)]))
expected_sequence_number = None

data_is_processing = True
DATA_SAVED = False

gaze_sqc_model = tf.keras.models.load_model('./utils/gaze_sqc_model/gaze_sqc_model.h5')
gaze_sqc_feature_means = np.load('./utils/gaze_sqc_model/gaze_sqc_model_feature_means.npy')
gaze_sqc_feature_stds = np.load('./utils/gaze_sqc_model/gaze_sqc_model_feature_stds.npy')

fig = plt.figure()
ax = fig.add_subplot(111)
axbutton = plt.axes([0.91, 0.5, 0.075, 0.075])
button = Button(axbutton, 'CH')
button.on_clicked(switch_eeg_channel)
x_plotting = np.arange(0, int(eeg_sampling_rate*visualization_timescale))
y_plotting = np.zeros_like(x_plotting)
    
if __name__== '__main__':
    signal.signal(signal.SIGINT, exit_signal_handler)
    
    # User event handler 
    keyboard.on_press(keyboard_event)
    
    ble_address = asyncio.run(get_ble_device_address(sys.argv[1]))
    if ble_address is None: sys.exit('Unable to find device {}'.format(sys.argv[1]))
    
    if len(sys.argv) > 2:
        experiment_id = sys.argv[2]
    else:
        experiment_id = None
    experiment = Experiment(max_streaming_time_s=max_streaming_time_s, params=all_params, experiment_id=experiment_id)
    
    Ble_stack = BLE_device_instance()
    init_thread = threading.Thread(name='ble_initializer', target=ble_initializer, args=(ble_address,))
    init_thread.start()
    
    eog_data_processing_thread = threading.Thread(name='process_eog_data', target=process_eog_data)
    eog_data_processing_thread.start()

    emg_data_processing_thread = threading.Thread(name='process_emg_data', target=process_emg_data)
    emg_data_processing_thread.start()

    clock = time.time()
    filtered_data = [[] for _ in range(num_eeg_channels)]
    data_for_filtering = None
    old_eeg_data_len = experiment.eeg_data_size
    #VISUALIZATION_ON = False
    while True:                
        if len(Ble_stack.raw_eeg_data) == 0:
            continue
        else:
            # Get oldest, unprocessed binary packet data and process it
            packet_data = Ble_stack.raw_eeg_data.pop(0)
            pc_packet_timestamp = Ble_stack.raw_eeg_pc_timestamps.pop(0)
            timestamp, seq_num, channel_data = Ble_stack.get_data_from_eeg_binary_packet(packet_data)
            if expected_sequence_number is None:
                expected_sequence_number = (seq_num+1)%256
            else:
                if seq_num != expected_sequence_number:
                    print('Missing or Duplicate packet')
                    continue
                else:
                    experiment.add_eeg_data(channel_data, pc_packet_timestamp)
                    expected_sequence_number = (expected_sequence_number+1)%256
                    
            if VISUALIZATION_ON:
                # Get collection of user events to display
                plotting_time = pc_packet_timestamp
                recent_events = np.array(experiment.event_timestamps)
                if len(recent_events) > 0:
                    recent_events = recent_events[(recent_events[:,0] >= plotting_time-visualization_timescale) & (recent_events[:,0] < plotting_time)]
                recent_event_inds = []
                for ts, ID in recent_events:
                    recent_event_inds.append([(ts-(plotting_time-visualization_timescale))*eeg_sampling_rate, ID])
                recent_event_inds = np.array(recent_event_inds)
            
                # Filter new data for visualization
                if data_for_filtering is None:
                    data_for_filtering = np.array(channel_data)
                else:
                    data_for_filtering = np.vstack([data_for_filtering, np.array(channel_data)])
                if data_for_filtering.shape[0] > 9:
                    for channel_i in range(num_eeg_channels):
                        filtered_data[channel_i] += list(eeg_channel_filters[channel_i].filter_data(data_for_filtering[:,channel_i]))
                    data_for_filtering = None
                
                # Plot data
                selected_channel_data = np.array(filtered_data[eeg_channel_index])
                if (len(selected_channel_data) > eeg_sampling_rate):
                    y_plotting = np.zeros_like(x_plotting)
                    data_count = min(len(selected_channel_data), len(x_plotting))
                    if data_count > 0:
                        y_plotting[-1*data_count:] = np.array(selected_channel_data[-1*data_count:])
                    ax.plot(y_plotting, linewidth=0.5)
                    for ind, ID in recent_event_inds:
                        ax.vlines([ind], eeg_display_amplitudes[0], eeg_display_amplitudes[1], color=event_colors[ID])
                    ax.set_title(eeg_channel_names[eeg_channel_index])
                    ax.set_ylim([eeg_display_amplitudes[0], eeg_display_amplitudes[1]])
                    ax.set_yticks(np.arange(eeg_display_amplitudes[0], eeg_display_amplitudes[1]+50, 50))
                    ax.set_ylabel('uV')
                    ax.grid()
                    plt.draw()
                    plt.pause(1e-20)
                    ax.clear()

                    for channel_i in range(num_eeg_channels):
                        filtered_data[channel_i] = filtered_data[channel_i][max(0,len(filtered_data[channel_i])-len(x_plotting)):]
        
        current_time = time.time()
        if current_time-clock > data_save_frequency:
            # Save experiment data
            experiment.save_data()
            clock = current_time

    init_thread.join()
    sys.exit('Exiting')
