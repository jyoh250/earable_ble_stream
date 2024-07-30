import numpy as np
import scipy.signal
from utils.feature_extraction import *
from utils.channel_selection import *
from utils.signal_processing import butter_highpass_filter
from sleep_scoring.model_files.Sleep_Staging_Models import Sleep_Stage_Model_TFLite

from pyedflib.highlevel import read_edf


class AutoSleepScoring():
    NUM_CHANNELS = 6
    model_path = './sleep_scoring/model_files/auto_sleep_scoring_model_ep_rnn_v2.6.2.tflite'
    feature_means_fpath = './sleep_scoring/model_files/feature_train_means.npy'
    feature_stds_fpath = './sleep_scoring/model_files/feature_train_stds.npy'
    # may be changed 30 to 10 according to the BLEApp.py file
    epoch_length = 10
    rnn_seq_len = 8
    SLEEP_STAGE_MAP = {0: 'Wake', 1: 'Light Sleep', 2: 'Deep Sleep', 3: 'REM', -1: 'Unknown'}
    num_sleep_stages = 4
    highpass_filter = True
    
    def __init__(self):
        self.model = Sleep_Stage_Model_TFLite(self.model_path, self.feature_means_fpath, self.feature_stds_fpath)
        
        # sleep_stage_confs[i] is a 4 element array, where
        # sleep_stage_confs[i][j] is the probability of sleep stage j at epoch i.
        # Sleep Stage Mappings: 0: Wake, 1: Light Sleep, 2: Deep Sleep, 3: REM
        self.sleep_stage_confs = []
        self.inferred_stages = []

        # Initialize a buffer for sequences of feature vectors for each channel.  
        # Each buffer will contain the rnn_seq_len most recent feature vectors.
        # When populated, feature_buffers will be of shape 
        # num_channels x rnn_seq_len x num_features
        self.feature_buffers = [None for ch in range(self.NUM_CHANNELS)]

        # Intializing variables for EMG feature calculations.
        self.bp_prevs = [None for ch in range(self.NUM_CHANNELS)]
        
        self.lf5_fpz_hist = []
        self.otel_fpz_hist = []
        self.bel_fpz_hist = []
        self.rf6_fpz_hist = []
        self.oter_fpz_hist = []
        self.ber_fpz_hist = []
        
        self.current_epoch = 0
        # the number of data collected in the buffer for each channel is 4*epoch_length, 4*10 = 40 seconds
        self.epochs_per_emg_window = 4
        
        
    def process_raw_epoch_samples(self, lf5_fpz, otel_fpz, bel_fpz, rf6_fpz, oter_fpz, ber_fpz, fs):
        # epoch_length = 30 seconds, fs = 125 Hz => num_samples_expected = 30*125 = 3750
        # chaned epoch_length to 10 to match the BLEApp.py file, 10*125 = 1250samples
        num_samples_expected = int(self.epoch_length*fs)
        
        # Get the last 10 seconds and 40 seconds of data for each channel (or, if data has only
        # been acquired for X minutes,  and X is less than 40sec, then use X minutes of data).
        # Resample the data to the expected number of samples
        lf5_epoch_data = scipy.signal.resample(lf5_fpz, num=num_samples_expected)
        # If the historical data buffer is not full, append the resampled data to the buffer.
        # Otherwise, shift the buffer by one epoch and replace the last epoch with the resampled data.
        # This way, the buffer always contains the last 40sec of data.
        # The buffer is used to calculate the EMG features.
        # The EMG features are used to determine if the EMG data is noisy.
        # epochs_per_emg_window = 4, so the buffer will contain the last 40sec of data.
        if len(self.lf5_fpz_hist) < self.epochs_per_emg_window:
            self.lf5_fpz_hist.append(np.array(lf5_epoch_data))
        else:
            self.lf5_fpz_hist[:-1] = self.lf5_fpz_hist[1:]
            self.lf5_fpz_hist[-1] = np.array(lf5_epoch_data)
            
        # OTEL
        otel_epoch_data = scipy.signal.resample(otel_fpz, num=num_samples_expected)
        if len(self.otel_fpz_hist) < self.epochs_per_emg_window:
            self.otel_fpz_hist.append(np.array(otel_epoch_data))
        else:
            self.otel_fpz_hist[:-1] = self.otel_fpz_hist[1:]
            self.otel_fpz_hist[-1] = np.array(otel_epoch_data)
            
        # BEL
        bel_epoch_data = scipy.signal.resample(bel_fpz, num=num_samples_expected)
        if len(self.bel_fpz_hist) < self.epochs_per_emg_window:
            self.bel_fpz_hist.append(np.array(bel_epoch_data))
        else:
            self.bel_fpz_hist[:-1] = self.bel_fpz_hist[1:]
            self.bel_fpz_hist[-1] = np.array(bel_epoch_data)
            
        # RF6
        rf6_epoch_data = scipy.signal.resample(rf6_fpz, num=num_samples_expected)
        if len(self.rf6_fpz_hist) < self.epochs_per_emg_window:
            self.rf6_fpz_hist.append(np.array(rf6_epoch_data))
        else:
            self.rf6_fpz_hist[:-1] = self.rf6_fpz_hist[1:]
            self.rf6_fpz_hist[-1] = np.array(rf6_epoch_data)
            
        # OTER
        oter_epoch_data = scipy.signal.resample(oter_fpz, num=num_samples_expected)
        if len(self.oter_fpz_hist) < self.epochs_per_emg_window:
            self.oter_fpz_hist.append(np.array(oter_epoch_data))
        else:
            self.oter_fpz_hist[:-1] = self.oter_fpz_hist[1:]
            self.oter_fpz_hist[-1] = np.array(oter_epoch_data)
            
        # BER
        ber_epoch_data = scipy.signal.resample(ber_fpz, num=num_samples_expected)
        if len(self.ber_fpz_hist) < self.epochs_per_emg_window:
            self.ber_fpz_hist.append(np.array(ber_epoch_data))
        else:
            self.ber_fpz_hist[:-1] = self.ber_fpz_hist[1:]
            self.ber_fpz_hist[-1] = np.array(ber_epoch_data)
            
            
    def dynamic_reference_data(self, lf5_epoch_data, lf5_window_data, \
                               otel_epoch_data, otel_window_data, \
                               bel_epoch_data, bel_window_data, \
                               rf6_epoch_data, rf6_window_data, \
                               oter_epoch_data, oter_window_data, \
                               ber_epoch_data, ber_window_data, fs):
        # lf5_noisy = 1
        # otel_noisy = 1
        # bel_noisy = 1
        # rf6_noisy = 1
        # oter_noisy = 1
        # ber_noisy = 1
        lf5_noisy = 0
        otel_noisy = 0
        bel_noisy = 0
        rf6_noisy = 0
        oter_noisy = 0
        ber_noisy = 0
        
        # Determine if the BE channels are suitable for re-referencing.
        bel_noisy = is_epoch_signal_bad(bel_epoch_data, fs)
        ber_noisy = is_epoch_signal_bad(ber_epoch_data, fs)

        # added for testing
        bel_noisy = 0
        ber_noisy = 0
       
        # If A1/A2 re-reference locations (i.e., BE-L/BE-R) are noisy, do not perform
        # re-referencing, otherwise, proceed with re-referencing.
        if not bel_noisy:
            rf6_epoch_data = rf6_epoch_data-bel_epoch_data
            rf6_window_data = rf6_window_data-bel_window_data

            oter_epoch_data = oter_epoch_data-bel_epoch_data
            oter_window_data = oter_window_data-bel_window_data
            
            bel_epoch_data = -1*bel_epoch_data
            bel_window_data = -1*bel_window_data

        if not ber_noisy:
            lf5_epoch_data = lf5_epoch_data-ber_epoch_data
            lf5_window_data = lf5_window_data-ber_window_data
            
            otel_epoch_data = otel_epoch_data-ber_epoch_data
            otel_window_data = otel_window_data-ber_window_data
            
            ber_epoch_data = -1*ber_epoch_data
            ber_window_data = -1*ber_window_data
            
        lf5_noisy = is_epoch_signal_bad(lf5_epoch_data, fs)
        otel_noisy = is_epoch_signal_bad(otel_epoch_data, fs)
        rf6_noisy = is_epoch_signal_bad(rf6_epoch_data, fs)
        oter_noisy = is_epoch_signal_bad(oter_epoch_data, fs)
        #  added to skip noisy channel testing
        lf5_noisy = 0
        otel_noisy = 0
        rf6_noisy = 0
        oter_noisy = 0
        
        rereferenced_epochs = [lf5_epoch_data, otel_epoch_data, bel_epoch_data, \
                               rf6_epoch_data, oter_epoch_data, ber_epoch_data]
        rereferenced_windows = [lf5_window_data, otel_window_data, bel_window_data, \
                                rf6_window_data, oter_window_data, ber_window_data]
        noisy_channels = [lf5_noisy, otel_noisy, bel_noisy, \
                          rf6_noisy, oter_noisy, ber_noisy]
            
        return rereferenced_epochs, rereferenced_windows, noisy_channels
        
        
    def score_epoch(self, lf5_fpz, otel_fpz, bel_fpz, rf6_fpz, oter_fpz, ber_fpz, fs):
        # Resample and record historical window data
        self.process_raw_epoch_samples(lf5_fpz, otel_fpz, bel_fpz, rf6_fpz, oter_fpz, ber_fpz, fs)
        
        lf5_epoch_data = np.array(self.lf5_fpz_hist[-1])
        lf5_window_data = np.hstack(self.lf5_fpz_hist)
        otel_epoch_data = np.array(self.otel_fpz_hist[-1])
        otel_window_data = np.hstack(self.otel_fpz_hist)
        bel_epoch_data = np.array(self.bel_fpz_hist[-1])
        bel_window_data = np.hstack(self.bel_fpz_hist)
        rf6_epoch_data = np.array(self.rf6_fpz_hist[-1])
        rf6_window_data = np.hstack(self.rf6_fpz_hist)
        oter_epoch_data = np.array(self.oter_fpz_hist[-1])
        oter_window_data = np.hstack(self.oter_fpz_hist)
        ber_epoch_data = np.array(self.ber_fpz_hist[-1])
        ber_window_data = np.hstack(self.ber_fpz_hist)
        
        # Perform channel selection and dynamic rereferencing
        rereferenced_epochs, rereferenced_windows, noisy_channels = self.dynamic_reference_data(lf5_epoch_data, lf5_window_data, \
                                                                                                otel_epoch_data, otel_window_data, \
                                                                                                bel_epoch_data, bel_window_data, \
                                                                                                rf6_epoch_data, rf6_window_data, \
                                                                                                oter_epoch_data, oter_window_data, \
                                                                                                ber_epoch_data, ber_window_data, fs)
        
        epoch_sleep_stage_probs = []
        for ch_idx, (channel_epoch_data, channel_window_data) in enumerate(zip(rereferenced_epochs, rereferenced_windows)):
            if self.highpass_filter:
                channel_epoch_data = butter_highpass_filter(channel_epoch_data, 0.3, fs, order=1)
                channel_window_data = butter_highpass_filter(channel_window_data, 0.3, fs, order=1)
            # amplitude clippping, max amplitude = 500 uV, min amplitude = -500 uV
            epoch_data = clip_signal(channel_epoch_data)
            window_data = clip_signal(channel_window_data)

            # preprocessing iir bandpass filter frequency band [1,20] Hz
            # frequency band [0.3,10] Hz for eog, notch filter 60, and butter_highpass_filter 20 Hz for emg
            eeg = preprocess_eeg(epoch_data, fs)
            eog = preprocess_eog(epoch_data, fs)
            emg = preprocess_emg(epoch_data, fs)
            emg_window = preprocess_emg(window_data, fs)

            # feature_extraction.py, compute_sleep_scoring_eeg_features
            # compute_psd_windows, compute_band_power_ratios, median, mean, std, min, max, mean absolute value, z-ratio, entropy
            # features = bp_features + bp_ratio_features + statistical_features + z_ratio_features + entropy_features
            # compute_eog_features: compute psd windws and 60% and 90% percentile of the power in the 0.3-10 Hz band
            # features = max_deflection + percentile_features + velocity_features...
            # compute_emg_features: compute psd windows and 60% and 90% percentile of the power in the 10-100 Hz band
            eeg_features = list(compute_sleep_scoring_eeg_features(eeg, fs))
            eog_features = list(compute_eog_features(eog, fs))
            emg_features, bp_curr = get_emg_epoch_features(emg, emg_window, self.bp_prevs[ch_idx], fs)

            # If bp_prev was never set for the channel (i.e., is None), only update it if the signal quality was OK
            if not noisy_channels[ch_idx] or self.bp_prevs[ch_idx] is not None:
                self.bp_prevs[ch_idx] = bp_curr

            # time_embedding is a 6 element array, where
            # time_embedding[0] = current_epoch/1200,  time_embedding[1] = cos((current_epoch*pi)/30) ...
            # what is this process for? what is the purpose of this time_embedding?
            # time_embedding is used to embed the current epoch number into a 6-dimensional feature vector
            # to provide the model with information about the time of day.
            # The model uses this information to help predict sleep stages.
            # what is divisor number, such as 1200, 30,60,90,120,150?
            # time_embedding[0] = current_epoch/1200, 1200 is the number of epochs in 2 hours
            # time_embedding[1] = cos((current_epoch*pi)/30), 30 is the number of epochs in 1 minute
            # time_embedding[2] = cos((current_epoch*pi)/60), 60 is the number of epochs in 2 minutes
            # time_embedding[3] = cos((current_epoch*pi)/90), 90 is the number of epochs in 3 minutes
            # time_embedding[4] = cos((current_epoch*pi)/120), 120 is the number of epochs in 4 minutes
            # time_embedding[5] = cos((current_epoch*pi)/150), 150 is the number of epochs in 5 minutes
            time_embedding = [self.current_epoch/1200, np.cos((self.current_epoch*np.pi)/30), np.cos((self.current_epoch*np.pi)/60), \
                              np.cos((self.current_epoch*np.pi)/90), np.cos((self.current_epoch*np.pi)/120), np.cos((self.current_epoch*np.pi)/150)]

            concat_feature_vector = np.concatenate((eeg_features, eog_features, emg_features, time_embedding))
            # extract_spectrogram, compute spectrogram of the signal, truncate to 50 Hz
            spectrogram = extract_spectrogram(eeg, fs, truncate_to_50hz=True)

            # Update the sequential feature buffer in FIFO fashion
            if self.feature_buffers[ch_idx] is None:
                # First epoch: we do not have feature history so use repetitions of current feature vector
                self.feature_buffers[ch_idx] = np.tile(concat_feature_vector, self.rnn_seq_len).reshape(self.rnn_seq_len,-1)
            else:
                # Pop oldest feature vector from the buffer, and append new to end
                self.feature_buffers[ch_idx][:-1] = self.feature_buffers[ch_idx][1:]
                self.feature_buffers[ch_idx][-1] = concat_feature_vector

            # Epoch data for this channel was noisy, do not use it for inference
            if noisy_channels[ch_idx] == 1:
                continue

            channel_sleep_stage_probabilities = self.model.predict(spectrogram, self.feature_buffers[ch_idx])
            epoch_sleep_stage_probs.append(channel_sleep_stage_probabilities)

        if len(epoch_sleep_stage_probs) > 0:
            aggregated_sleep_stage_confs = np.median(epoch_sleep_stage_probs, axis=0)
            inferred_sleep_stage = np.argmax(aggregated_sleep_stage_confs, axis=0)
        else:
            # All channels were noisy
            aggregated_sleep_stage_confs = np.zeros(self.num_sleep_stages)
            inferred_sleep_stage = -1

        self.inferred_stages.append(inferred_sleep_stage)
        self.sleep_stage_confs.append(aggregated_sleep_stage_confs)
        self.current_epoch += 1
        
        return inferred_sleep_stage, aggregated_sleep_stage_confs
