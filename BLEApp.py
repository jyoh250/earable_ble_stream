import os
import sys
import argparse
import signal
import time
import copy
import asyncio
import threading
import subprocess
import keyboard
import numpy as np
from BLEScan import get_ble_device_address
from BLEBleak import BLE_device_instance
from params import *
from WindowFiltering import *
from Experiment import Experiment
from utils.signal_processing import notch_filter, butter_bandpass_lfilter, base_filter, preprocess_sqc_data
from utils.channel_selection import is_signal_noisy
from sleep_scoring.auto_sleep_scoring import AutoSleepScoring
import matplotlib.pyplot as plt
from matplotlib.widgets import Button

# add -W ignore to the command line to ignore warnings
# add --log-level=1 to the command line to set log level to 1
# add --no_visualization to the command line to disable EEG visualization
# add --score_sleep to the command line to enable sleep scoring

def short_term_sqc(sqc_window_stride_s=3, sqc_window_len_s=3):
    data_processing_time = time.time()
    
    # Signal quality indicators for lf5, rf6, otel, oter. 0 indicates noisy, 1 indicates OK
    lf5_signal_quality = 0
    rf6_signal_quality = 0
    otel_signal_quality = 0
    oter_signal_quality = 0
    # check data size? what is included and what is not, 4ch EEG and timestamps?
    # eeg_sampling_rate = 250, experiment.eeg_data_size = 1000
    # self.eeg_data = np.memmap(os.path.join(self.experiment_id, 'eeg.dat'), dtype=np.float64, mode='w+', \
    #   shape=(int(eeg_sampling_rate*max_streaming_time_s),num_eeg_channels)), eeg_sampling_rate*max_streaming_time_s = 250*3600 = 900,000
    # max_streaming_time_s = 3600, int(60*60*1), num_eeg_channels = 6

    old_sqc_data_len = experiment.eeg_data_size
    while data_is_processing:
        new_sqc_samples = experiment.eeg_data_size - old_sqc_data_len 
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
            
            lf5_signal_quality = 0 if (is_signal_noisy(lf5_window, eeg_sampling_rate) or np.any(np.abs(lf5_window > 100))) else 1
            rf6_signal_quality = 0 if (is_signal_noisy(rf6_window, eeg_sampling_rate) or np.any(np.abs(rf6_window > 100))) else 1
            otel_signal_quality = 0 if is_signal_noisy(otel_window, eeg_sampling_rate) else 1
            oter_signal_quality = 0 if is_signal_noisy(oter_window, eeg_sampling_rate) else 1
            
            print('Signal Qualities [LF5, RF6, OTEL, OTER] (1: OK, 0: Bad): {}'.format([lf5_signal_quality, rf6_signal_quality, otel_signal_quality, oter_signal_quality]))
            old_sqc_data_len = experiment.eeg_data_size
        time.sleep(1)

def score_sleep():
    t0 = time.time()
    scorer = AutoSleepScoring()
    samples_per_epoch = int(10*eeg_sampling_rate)
    old_exg_data_len = experiment.eeg_data_size
    while data_is_processing:
        new_exg_samples = experiment.eeg_data_size - old_exg_data_len
        if (new_exg_samples >= samples_per_epoch):
            print(time.time()-t0)
            print(experiment.eeg_data_size)
            old_exg_data_len = experiment.eeg_data_size
            lf5_epoch = np.array(experiment.eeg_data[old_exg_data_len-samples_per_epoch:old_exg_data_len,0])
            otel_epoch = np.array(experiment.eeg_data[old_exg_data_len-samples_per_epoch:old_exg_data_len,1])
            bel_epoch = np.array(experiment.eeg_data[old_exg_data_len-samples_per_epoch:old_exg_data_len,2])
            rf6_epoch = np.array(experiment.eeg_data[old_exg_data_len-samples_per_epoch:old_exg_data_len,3])
            oter_epoch = np.array(experiment.eeg_data[old_exg_data_len-samples_per_epoch:old_exg_data_len,4])
            ber_epoch = np.array(experiment.eeg_data[old_exg_data_len-samples_per_epoch:old_exg_data_len,5])
            inferred_sleep_stage, aggregated_sleep_stage_confs = scorer.score_epoch(lf5_epoch, otel_epoch, bel_epoch,\
                                                                                    rf6_epoch, oter_epoch, ber_epoch, eeg_sampling_rate)
            print('Fatigue Stage Prediction: {}'.format(inferred_sleep_stage))
            print('Fatigue Stage Confidences: {}'.format(aggregated_sleep_stage_confs))
            print()
    return np.array(scorer.inferred_stages), np.array(scorer.sleep_stage_confs)

# def binaural_beats_test(frequency):
#     nostim_timestamps_fpath = os.path.join(experiment_id_data_path, 'nostim_audio_timestamps.npy')
#     audio_timestamps_fpath = os.path.join(experiment_id_data_path, 'binaural_audio_timestamps.npy')
#     while experiment.eeg_data_size/eeg_sampling_rate < 10:
#         time.sleep(1)
#     nostim_timestamps = np.array([time.time(), 0])
#     time.sleep(330)
#     nostim_timestamps[1] = time.time()
#     np.save(nostim_timestamps_fpath, nostim_timestamps)
#     subprocess.getstatusoutput('python3 stimulation/run_binaural_beats.py {} {}'.format(frequency, audio_timestamps_fpath))
        
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
                experiment.add_eeg_data(channel_data, pc_packet_timestamp, timestamp)
                expected_sequence_number = (seq_num+1)%256
            else:
                if seq_num != expected_sequence_number:
                    print('Missing or Duplicate packet')
                    continue
                else:
                    experiment.add_eeg_data(channel_data, pc_packet_timestamp, timestamp)
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
    #print('Key pressed')
    if event.name in event_key_bindings.keys():
        experiment.add_event_timestamp([time.time(), event_key_bindings[event.name]])

eeg_channel_index = 0
eeg_channel_filters = []
for _ in range(num_eeg_channels):
    eeg_channel_filters.append(WindowFilter([WindowIIRNotchFilter(60, 12, eeg_sampling_rate), \
                                             #WindowIIRNotchFilter(50, 10, eeg_sampling_rate), \
                                             WindowButterBandpassFilter(1, 0.5, 20, eeg_sampling_rate)]))
expected_sequence_number = None
DATA_SAVED = False
data_is_processing = True

fig = plt.figure()
ax = fig.add_subplot(111)
axbutton = plt.axes([0.91, 0.5, 0.075, 0.075])
button = Button(axbutton, 'CH')
button.on_clicked(switch_eeg_channel)
x_plotting = np.arange(0, int(eeg_sampling_rate*visualization_timescale))
y_plotting = np.zeros_like(x_plotting)

parser = argparse.ArgumentParser()
parser.add_argument('--device_id', action='store', type=str, required=True)
parser.add_argument('--experiment_id', action='store', type=str, required=False)
parser.add_argument('--no_visualization', action='store_true')
parser.add_argument('--score_sleep', action='store_true')
# parser.add_argument('--smart_alarm', action='store_true')
# parser.add_argument('--mrt', action='store_true')
# parser.add_argument('--binaural_freq', action='store', type=int, required=False)
parser.add_argument('--log-level=1', help='Set log level to 1')

if __name__== '__main__':
    args = parser.parse_args()
    if args.no_visualization:
        VISUALIZATION_ON = False
    # print(args.log_level)
    # User event handler 
    keyboard.on_press(keyboard_event)
    signal.signal(signal.SIGINT, exit_signal_handler)
    
    # Set up BLE streaming and recording
    ble_address = asyncio.run(get_ble_device_address(args.device_id))
    if ble_address is None: sys.exit('Unable to find device {}'.format(args.device_id))
    if args.experiment_id is None:
        experiment_id = str(time.time())
    else:
        experiment_id = '{}_{}'.format(args.experiment_id, time.time())
    experiment_id_data_path = os.path.join('./experiment_data', experiment_id)
    experiment = Experiment(max_streaming_time_s=max_streaming_time_s, params=all_params, device_id=args.device_id, experiment_id=experiment_id_data_path)
    Ble_stack = BLE_device_instance()
    init_thread = threading.Thread(name='ble_initializer', target=ble_initializer, args=(ble_address,))
    init_thread.start()
    
    # Start signal quality check thread
    sqc_thread = threading.Thread(name='signal_quality_check', target=short_term_sqc)
    sqc_thread.start()
    
    # Start any specified applications
    sleep_scoring_thread = None
    # smart_alarm_thread = None
    # if args.smart_alarm:
    #     args.score_sleep = True
    #     smart_alarm_thread = threading.Thread(name='smart_alarm', target=smart_alarm)
    #     smart_alarm_thread.start()
    # if args.score_sleep:
    sleep_scoring_thread = threading.Thread(name='score_sleep', target=score_sleep)
    sleep_scoring_thread.start()
    # if args.mrt:
    #     os.system('python ./focus/MRT/MRT.py {}'.format(experiment_id))
    # if args.binaural_freq is not None:
    #     binarual_beats_thread = threading.Thread(name='binaural_beats', target=binaural_beats_test, args=(args.binaural_freq,))
    #     binarual_beats_thread.start()

    clock = time.time()
    filtered_data = [[] for _ in range(num_eeg_channels)]
    data_for_filtering = None
    while True:
        if len(Ble_stack.raw_eeg_data) == 0:
            continue
        else:
            # Get oldest, unprocessed binary packet data and process it
            packet_data = Ble_stack.raw_eeg_data.pop(0)
            pc_packet_timestamp = Ble_stack.raw_eeg_pc_timestamps.pop(0)
            timestamp, seq_num, channel_data = Ble_stack.get_data_from_eeg_binary_packet(packet_data)
            if expected_sequence_number is None:
                experiment.add_eeg_data(channel_data, pc_packet_timestamp, timestamp)
                expected_sequence_number = (seq_num+1)%256
            else:
                if seq_num != expected_sequence_number:
                    print('Missing or Duplicate packet')
                    continue
                else:
                    experiment.add_eeg_data(channel_data, pc_packet_timestamp, timestamp)
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
