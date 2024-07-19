import numpy as np
import scipy
from scipy import signal
from scipy.signal import butter
from scipy.fft import fft, fftfreq

EPOCH_LENGTH = 30

STAGE_LABEL_MAP = {'Sleep stage W': 0, 'Sleep stage N1': 1, 'Sleep stage N2': 2, \
                   'Sleep stage N3': 3, 'Sleep stage R': 4, 'Sleep stage ?': -1}

STAGE_LABEL_MAP_4_STAGE = {'Sleep stage W': 0, 'Sleep stage Light Sleep': 1, 'Sleep stage Deep Sleep': 2, \
                           'Sleep stage R': 3, 'Sleep stage ?': -1}

notch_filter_fc = 50
notch_filter_q = 10

def notch_filter(data, fs, stop_fs=notch_filter_fc, Q=notch_filter_q):
    b, a = scipy.signal.iirnotch(stop_fs, Q, fs)
    y = scipy.signal.filtfilt(b, a, data)
    return y

def butter_bandpass_filter(data, lowcut, highcut, fs, order=1):
    b, a = butter(order, [lowcut, highcut], btype='band',fs=fs)
    y = signal.filtfilt(b, a, data)
    return y

def iir_bandpass_filter(data, fs, frequency_band=[1,20], order=4):
    '''
    IIR Bandpass filter

    Derived from:
    https://github.com/Dreem-Organization/dreem-learning-open/blob/632a84c7e412f69f51c407ecb2ea91403f0d26c3/dreem_learning_open/preprocessings/signal_processing.py#L52
    '''
    b, a = signal.iirfilter(order, [ff * 2. / fs for ff in frequency_band], btype='bandpass', ftype='butter')
    y = signal.lfilter(b, a, data)
    return y

def butter_bandpass_lfilter(data, lowcut, highcut, fs, order=5):
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = scipy.signal.butter(order, [low, high], btype='band')
    y = scipy.signal.lfilter(b, a, data)
    return y

def butter_lowpass_filter(data, cutoff_fs, fs, order=1):
    b, a = butter(order, cutoff_fs, btype='low',fs=fs)
    y = signal.filtfilt(b, a, data)
    return y

def butter_highpass_filter(data, cutoff_fs, fs, order=1):
    b, a = butter(order, cutoff_fs, btype='high',fs=fs)
    y = signal.filtfilt(b, a, data)
    return y

def clip_signal(data, clipping_amplitude=500):
    data = np.clip(data, -1*clipping_amplitude, clipping_amplitude)
    return data

def base_filter(data, fs):
    data = notch_filter(data, fs, stop_fs=60, Q=12)
    data = notch_filter(data, fs, stop_fs=50, Q=10)
    data = notch_filter(data, fs, stop_fs=25, Q=5)
    return data

def preprocess_sqc_data(data, fs):
    data = butter_bandpass_lfilter(data, 0.5, 35, fs, order=1)
    return data

def preprocess_eeg(data, fs):
    data = iir_bandpass_filter(base_filter(data, fs), fs, frequency_band=[1,20], order=2)
    return data

def preprocess_eog(data, fs):
    data = iir_bandpass_filter(base_filter(data, fs), fs, frequency_band=[0.3,10], order=2)
    return data

def preprocess_eog_gaze_data(data, fs):
    base_data = base_filter(data, fs)
    data = butter_bandpass_lfilter(base_data, 0.5, 10, fs, order=2)
    return base_data, data

#def preprocess_emg(data, fs):
#    data = butter_highpass_filter(base_filter(data, fs), 10, fs)
#    return data

def preprocess_emg(data, fs):
    '''
    Filter mixed signal data to include primiarily EMG data.
    
    input:
        data: Mixed signal data
        fs: sampling rate of signal data
    output:
        data: Filtered data
    '''
    data = notch_filter(data, fs, stop_fs=60, Q=12)
    data = butter_highpass_filter(data, 20, fs, order=2)
    return data

def preprocess_alpha(data, fs):
    '''
    Filter mixed signal data to include primiarily EMG data.
    
    input:
        data: Mixed signal data
        fs: sampling rate of signal data
    output:
        data: Filtered data
    '''
    data = notch_filter(data, fs, stop_fs=60, Q=12)
    data = butter_highpass_filter(data, 5, fs, order=2)
    return data

import scipy
from scipy import signal
from scipy.fft import fft, fftfreq
from scipy.integrate import simps
def compute_band_powers(datum, fs, bands=[0.5,4,8,13], normalize=True):
    '''
    Computes PSD for frequency bands for a given signal segment.
    
    inputs:
        signal - a single channel of signal data
        fs - sampling frequency of signal data
        bands - array of frequency band boundaries
        normalize - if true, PSDs will be scaled by total signal power.
        
    outputs:
        bp - list of normalized bandpower for each frequency band
    '''
    freq_low = bands[0]
    freq_high = bands[-1]

    fft_datum = np.abs(fft(datum))
    freqs = fftfreq(len(datum),1/fs)
    indice = np.bitwise_and(freqs<=(fs/2.), freqs>=0)
    fft_datum = fft_datum[indice]
    freqs = freqs[indice]
    total_pow = simps(fft_datum,freqs)

    bp = []
    for idx in range(1,len(bands)):
        indice = np.bitwise_and(freqs<=bands[idx], freqs>=bands[idx-1])
        power = simps(fft_datum[indice],freqs[indice])
        if normalize:
            power = power/total_pow
        bp.append(power)

    return bp
