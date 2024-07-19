import os
import sys
import numpy as np
sys.path.append('..')
from signal_processing import *
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import signal
from scipy.integrate import simps

sns.set_style('darkgrid')

def basic_eeg_filter(data, fs):
    '''
    Apply base filters to EEG data.
    
    input:
        data: numpy array of shape (m channels X n samples)
        fs: sampling rate of data (Hz)
    output:
        filtered_data: filtered data
    '''
    num_eeg_channels = data.shape[0]
    filtered_data = np.zeros_like(data)
    for channel_i in range(num_eeg_channels):
        filtered_data[channel_i,:] = butter_highpass_filter(data[channel_i,:], 0.3, fs, order=5)
        filtered_data[channel_i,:] = notch_filter(filtered_data[channel_i,:], fs, 60, 12)
        filtered_data[channel_i,:] = notch_filter(filtered_data[channel_i,:], fs, 50, 10)
        filtered_data[channel_i,:] = butter_bandpass_filter(filtered_data[channel_i,:], 1, 35, fs, order=1)
    return filtered_data


def calculate_band_power(data, lowerband, upperband, fs):
    n = data.shape[0]
    freqs, psd = signal.welch(data, fs, nperseg=n)
    idx_band = np.logical_and(freqs >= lowerband, freqs <= upperband)
    freq_res = freqs[1] - freqs[0]
    band_power = simps(psd[idx_band], dx=freq_res)
    return band_power


def plot_eeg(filter_eeg_data, eeg_data, begin, end):
    # Sample visualization of 30 seconds of EEG data
    if filter_eeg_data:
        eeg_data = basic_eeg_filter(eeg_data, eeg_fs)
    eeg_sample_segment = eeg_data[:, int(begin * eeg_fs):int(end * eeg_fs)]  # Samples from time t=30 to t=60 seconds
    # eeg_sample_segment = eeg_data
    fig, ax = plt.subplots(num_eeg_channels, figsize=(12, 8))
    for channel_i in range(num_eeg_channels):
        ax[channel_i].plot(eeg_sample_segment[channel_i, :], lw=1)
        ax[channel_i].set_xlim([0, eeg_sample_segment.shape[-1]])
        ax[channel_i].set_xticklabels(np.array(ax[channel_i].get_xticks()) / eeg_fs)
        ax[channel_i].set_ylabel('uV')
        ax[channel_i].set_title('Channel {}'.format(channel_i + 1))
    ax[-1].set_xlabel('Time (s)')
    plt.tight_layout()
    plt.show()


def calculate_eeg_bandpower(eeg_data, begin, end):
    eeg_data = basic_eeg_filter(eeg_data, eeg_fs)
    eeg_sample_segment = eeg_data[:, int(begin * eeg_fs):int(end * eeg_fs)]
    alpha_power_F5 = calculate_band_power(eeg_sample_segment[0, :], 8, 12, eeg_fs)
    alpha_power_F6 = calculate_band_power(eeg_sample_segment[3, :], 8, 12, eeg_fs)
    beta_power_F5 = calculate_band_power(eeg_sample_segment[0, :], 12, 30, eeg_fs)
    beta_power_F6 = calculate_band_power(eeg_sample_segment[3, :], 12, 30, eeg_fs)
    return alpha_power_F5, alpha_power_F6, beta_power_F5, beta_power_F6



def plot_ppg(ppg_data, begin, end):
    ppg_sample_segment = ppg_data[:, int(begin * ppg_fs):int(end * ppg_fs)]  # Samples from time t=30 to t=60 seconds
    fig, ax = plt.subplots(num_ppg_channels, figsize=(12, 8))
    for channel_i in range(num_ppg_channels):
        ax[channel_i].plot(ppg_sample_segment[channel_i, :], lw=1)
        ax[channel_i].set_xlim([0, ppg_sample_segment.shape[-1]])
        ax[channel_i].set_xticklabels(np.array(ax[channel_i].get_xticks()) / ppg_fs)
        ax[channel_i].set_ylabel('?')
        ax[channel_i].set_title('Channel {}'.format(channel_i + 1))
    ax[-1].set_xlabel('Time (s)')
    plt.tight_layout()
    plt.show()




data_dir = '../experiment_data/5m-music-5m-typing'
filter_eeg_data = True

if __name__ == '__main__':
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

    #plot_eeg(filter_eeg_data, eeg_data, 300, 600)
    #plot_ppg(ppg_data, 0, 120)
    #plot_imu(filter_eeg_data, eeg_data, 60, 120)

    alpha_power_F5, alpha_power_F6, beta_power_F5, beta_power_F6 = calculate_eeg_bandpower(eeg_data, 10, 300)
    print("Relax with music, eye open (first 5 mins): ")
    print("beta_power_F5: ", beta_power_F5, "uV^2/Hz")
    print("beta_power_F6: ", beta_power_F6, "uV^2/Hz")

    alpha_power_F5, alpha_power_F6, beta_power_F5, beta_power_F6 = calculate_eeg_bandpower(eeg_data, 300, 610)
    print("Typing with music, eye open (last 5 mins): ")
    print("beta_power_F5: ", beta_power_F5, "uV^2/Hz")
    print("beta_power_F6: ", beta_power_F6, "uV^2/Hz")


    