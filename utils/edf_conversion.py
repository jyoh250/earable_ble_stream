import os
import sys
import datetime
import numpy as np
import pandas as pd
from pyedflib import highlevel

def get_study_data(data_dir):
    recording_info = np.load(os.path.join(data_dir, 'recording_data.npz'), allow_pickle=True)
    recording_parameters = recording_info['params'].item()

    if 'num_eeg_channels' in recording_parameters:
        num_eeg_channels = recording_parameters['num_eeg_channels']
    else:
        num_eeg_channels = 6

    if 'eeg_sampling_rate' in recording_parameters:
        eeg_fs = recording_parameters['eeg_sampling_rate']
    else:
        eeg_fs = 125

    if 'num_imu_channels' in recording_parameters:
        num_imu_channels = recording_parameters['num_imu_channels']
    else:
        num_imu_channels = 3

    if 'imu_sampling_rate' in recording_parameters:
        imu_fs = recording_parameters['imu_sampling_rate']
    else:
        imu_fs = 50

    if 'num_ppg_channels' in recording_parameters:
        num_ppg_channels = recording_parameters['num_ppg_channels']
    else:
        num_ppg_channels = 3

    if 'ppg_sampling_rate' in recording_parameters:
        ppg_fs = recording_parameters['ppg_sampling_rate']
    else:
        ppg_fs = 25

    eeg_data = np.array(np.memmap(os.path.join(data_dir, 'eeg.dat'), dtype='float64', mode='r'))
    eeg_data = eeg_data.reshape((-1,num_eeg_channels))
    eeg_data = eeg_data[:int(recording_info['eeg_data_size']),:].T

    imu_data = np.array(np.memmap(os.path.join(data_dir, 'imu.dat'), dtype='float64', mode='r'))
    imu_data = imu_data.reshape((-1,num_imu_channels))
    imu_data = imu_data[:int(recording_info['imu_data_size']),:].T

    ppg_data = np.array(np.memmap(os.path.join(data_dir, 'ppg.dat'), dtype='float64', mode='r'))
    ppg_data = ppg_data.reshape((-1,num_ppg_channels))
    ppg_data = ppg_data[:int(recording_info['ppg_data_size']),:].T

    return eeg_data, eeg_fs, imu_data, imu_fs, ppg_data, ppg_fs, recording_info['eeg_packetread_timestamps']


def convert_to_edf(output_fpath,\
                   eeg_data, eeg_fs, eeg_channel_names, \
                   imu_data, imu_fs, imu_channel_names, \
                   ppg_data, ppg_fs, ppg_channel_names,
                   starttime=None):
    signals = []
    signal_headers = []
    max_data_duration = max(eeg_data.shape[-1]/eeg_fs, imu_data.shape[-1]/imu_fs, ppg_data.shape[-1]/ppg_fs)
    max_data_duration = int(np.ceil(max_data_duration))
    for i, ch_name in enumerate(eeg_channel_names):
        channel_data = np.zeros(max_data_duration*eeg_fs)
        channel_data[:eeg_data.shape[-1]] = np.array(eeg_data[i,:])
        signal_header = highlevel.make_signal_header(ch_name,\
                                                     dimension='uV',\
                                                     sample_rate=eeg_fs,\
                                                     physical_min=np.min(channel_data),\
                                                     physical_max=np.max(channel_data),\
                                                     digital_min=min(-32768,np.min(channel_data)),\
                                                     digital_max=max(32768,np.max(channel_data)))
        signal_headers.append(signal_header)
        signals.append(channel_data)


    for i, ch_name in enumerate(imu_channel_names):
        channel_data = np.zeros(max_data_duration*imu_fs)
        channel_data[:imu_data.shape[-1]] = np.array(imu_data[i,:])
        signal_header = highlevel.make_signal_header(ch_name,\
                                                     dimension='m/s^2',\
                                                     sample_rate=imu_fs,\
                                                     physical_min=np.min(channel_data),\
                                                     physical_max=np.max(channel_data),\
                                                     digital_min=min(-32768,np.min(channel_data)),\
                                                     digital_max=max(32768,np.max(channel_data)))
        signal_headers.append(signal_header)
        signals.append(channel_data)

    for i, ch_name in enumerate(ppg_channel_names):
        channel_data = np.zeros(max_data_duration*ppg_fs)
        channel_data[:ppg_data.shape[-1]] = np.array(ppg_data[i,:])
        signal_header = highlevel.make_signal_header(ch_name,\
                                                     dimension='a.u.',\
                                                     sample_rate=ppg_fs,\
                                                     physical_min=np.min(channel_data),\
                                                     physical_max=np.max(channel_data),\
                                                     digital_min=min(-32768,np.min(channel_data)),\
                                                     digital_max=max(32768,np.max(channel_data)))
        signal_headers.append(signal_header)
        signals.append(channel_data)

    startdate = None
    if starttime is not None:
        startdate = datetime.datetime.fromtimestamp(starttime)
    header = highlevel.make_header(startdate=startdate)
    return highlevel.write_edf(output_fpath, signals, signal_headers, header)

eeg_channel_names = ['ch1_LF5-FpZ','ch2_OTE_L-FpZ','ch3_BE_L-FpZ','ch4_RF6-FpZ','ch5_OTE_R-FpZ','ch6_BE_R-FpZ']
imu_channel_names = ['imu_x','imu_y','imu_z']
ppg_channel_names = ['Green', 'IR', 'Red']

if __name__ == '__main__':
    experiment_data_path = sys.argv[1]
    if len(sys.argv) > 2:
        output_fpath = os.path.join(experiment_data_path, sys.argv[2])
    else:
        output_fpath = os.path.join(experiment_data_path, 'recording_data.edf')
    eeg_data, eeg_fs, imu_data, imu_fs, ppg_data, ppg_fs, eeg_timestamps = get_study_data(experiment_data_path)
    edf_export_successful = convert_to_edf(output_fpath,\
                                           eeg_data, eeg_fs, eeg_channel_names,\
                                           imu_data, imu_fs, imu_channel_names,\
                                           ppg_data, ppg_fs, ppg_channel_names,\
                                           starttime=eeg_timestamps[0])
    print('Successful data export? {}'.format(edf_export_successful))
    
    