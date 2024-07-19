import numpy as np
import scipy
from scipy import signal
from scipy.fft import fft, fftfreq
from scipy.integrate import simps
from utils.signal_processing import *

MIN_FFT_MAG = 1e-7

def extract_spectrogram(datum, fs, window_len=1.28,overlapping_len=0.28, return_f_t=False, truncate_to_50hz=True):
    '''
    extract spectrogram
    @input: datum: 1-dimentional array
            fs (Hz): sampling rate in Hz
            window_len (seconds): length of each segment in seconds
            overlapping_len (seconds): overlapping between 2 consecutive segments in seconds
    @output: f : frequency axis
             t : time axis
             mag: magitude of spectrogram, shape of (t,f)
    '''
    npoints = int(window_len*fs)
    noverlap = int(overlapping_len*fs)
    f, t, Zxx = signal.stft(datum.squeeze(),fs=fs,nperseg=npoints,noverlap=noverlap,window='hann')
    mag = np.flipud(np.abs(Zxx).transpose(1,0))
    if truncate_to_50hz:
        mag = mag[:,:65]
    mag = mag/mag.sum(axis=1)[:,None]
    # mag = np.log10(mag)
    if return_f_t:
        return f, t[::-1], mag
    else:
        return mag


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
        else:
            power = max(power, MIN_FFT_MAG)
            power = 10*np.log10(power)
        bp.append(power)

    return bp


def compute_band_power_ratios(datum, fs):
    '''
    Computes ratios of the common EEG bands.
    
    input:
        datum - 1-dimentional array
        fs - sampling rate in Hz
    output:
        ratios: an array of EEG bandpower ratios
        
    '''
    band = [2,4,8,12,16,20]

    freq_low = band[0]
    freq_high = band[-1]
    f_datum = butter_bandpass_filter(datum,freq_low,freq_high,fs)

    fft_datum = np.abs(fft(f_datum))
    freqs = fftfreq(len(f_datum),1/fs)
    indice = np.bitwise_and(freqs<=(fs/2.), freqs>=0)
    fft_datum = fft_datum[indice]
    freqs = freqs[indice]
    total_pow = simps(fft_datum,freqs)

    bp = []
    for idx in range(1,len(band)):
        indice = np.bitwise_and(freqs<=band[idx], freqs>=band[idx-1])
        power = simps(fft_datum[indice],freqs[indice])/total_pow
        bp.append(power)

    delta, theta, alpha, sigma, beta = bp

    ratios = [delta/theta, delta/alpha, delta/sigma, delta/beta, theta/alpha, \
              theta/sigma, theta/beta, alpha/sigma, alpha/beta, sigma/beta]
    return np.asarray(ratios)
    

def compute_psd_windows(datum, fs, window_length=10, window_stride=5, bands=[0.5,4,8,13], normalize=True):
    '''
    Computes PSD for EEG frequency bands over each interval of duration `window_length`.
    
    inputs:
        signal - a single channel of signal data
        fs - sampling frequency of signal data
        window_length - length of sliding window to analyze (in seconds)
        window_stride - stride of sliding window (in seconds)
        bands - array of frequency band boundaries
        normalize - If true, PSDs will be scaled by total signal power.
        
    outputs:
        bandpower - 2D array of bandpower computations.  bandpower[i,j] gives the
        normalized PSD of the jth frequency band in signal interval i.
    '''
    samples_per_window = int(fs*window_length)
    stride = int(fs*window_stride)
    
    i = 0
    bandpower = []
    for i in range(0,len(datum),stride):
        if i+samples_per_window > len(datum):
            break
        signal_segment = datum[i:i+samples_per_window]
        psds = compute_band_powers(signal_segment, fs, bands, normalize)
        bandpower.append(psds)
        
    return np.asarray(bandpower)


def compute_z_ratio(datum, fs):
    '''
    Computes the z-ratio of a given signal segment.
    
    input:
        datum: segment of biopotential signal data
        fs: sampling rate of datum
    output:
        z-ratio, a measure of relative slow wave activity in the EEG signal
    '''
    fft_datum = np.abs(fft(datum))
    freqs = fftfreq(len(datum),1/fs)
    indice = np.bitwise_and(freqs<=(20), freqs>=0.5)
    fft_datum = fft_datum[indice]
    freqs = freqs[indice]
    total_pow = simps(fft_datum,freqs)

    slow_indice = np.bitwise_and(freqs<=8, freqs>=0.5)
    slow_power = simps(fft_datum[slow_indice],freqs[slow_indice])/total_pow
    
    fast_indice = np.bitwise_and(freqs<=20, freqs>=8)
    fast_power = simps(fft_datum[fast_indice],freqs[fast_indice])/total_pow
    
    return (slow_power-fast_power)/(slow_power+fast_power)


def compute_fft(signal, fs, padding_duration=0):
    signal_frequency = fs
    signal_freq = np.fft.rfft(signal, n=len(signal))
    signal_freq = np.abs(signal_freq)
    x = signal_freq
    return x


def compute_sleep_scoring_eeg_features(datum, fs):
    '''
    Computes the EEG features used by the ML sleep scoring model.
    
    input:
        datum (array): single channel signal data
        fs (int): sampling rate of signal data [Hz]
    output:
        features: an array of EEG features (the EEG feature vector).
    '''
    bp_features = list(compute_psd_windows(datum, fs, window_length=30, window_stride=30, bands=[2,4,8,13,20]).flatten())
    bp_ratio_features = list(compute_band_power_ratios(datum, fs))
    statistical_features = [np.median(datum), np.mean(datum), np.std(datum), np.min(datum), np.max(datum), np.mean(np.abs(datum))]
    z_ratio_features = [compute_z_ratio(datum, fs)]
    entropy_features = [scipy.stats.entropy(np.abs(datum))]
    features = bp_features + bp_ratio_features + statistical_features + z_ratio_features + entropy_features
    return np.asarray(features)


def get_emg_epoch_features(emg_epoch_data, windowed_emg_data, bp_prev, fs):
    '''
    Computes EMG feature variables from a given segment of data and historical data.
    
    input:
        emg_epoch_data: Epoch of separated EMG signal data
        windowed_emg_data: Signal segment of historical separated EMG signal data
        bp_prev: mean EMG bandpower computed for historical data (used to detect changes)
        fs: sampling rate of signal data
    output:
        epoch_features: Array of EMG feature variables.
        bp_prev: Mean bandpower calculated for current data.
    '''
    
    # Compute mean and variance of 10-100Hz bandpower in windowed_emg_data
    emg_bp = compute_psd_windows(windowed_emg_data, fs, window_length=30, window_stride=30, bands=[10, fs/2], normalize=False)
    emg_bp_mean = np.mean(emg_bp)
    emg_bp_var = np.var(emg_bp)
    
    # Get change in bp features from previous time steps
    if bp_prev is not None:
        bp_change = (bp_prev - emg_bp_mean)/bp_prev
    else:
        bp_change = 0
    bp_prev = emg_bp_mean

    
    epoch_features = [emg_bp_var, bp_change]
    return np.asarray(epoch_features), bp_prev


def get_saccade_features(eog_data, fs):
    velocity = np.diff(eog_data)*fs
    acceleration = np.diff(velocity)*fs
    mean_vel = np.mean(velocity)
    max_vel = np.max(velocity)
    return [mean_vel, max_vel]


def compute_eog_features(eog_datum, fs):
    deflection = np.abs(eog_datum)
    max_deflection = np.max(deflection)
    percentile_60_deflection = np.percentile(deflection, 60)
    percentile_90_deflection = np.percentile(deflection, 90)
    low_power_eog, high_power_eog = list(compute_psd_windows(eog_datum, fs, window_length=30, window_stride=30, bands=[0.3,4,10]).flatten())

    features = []
    features += [max_deflection, percentile_60_deflection, percentile_90_deflection]
    features += list(get_saccade_features(eog_datum, fs))
    features += [low_power_eog, high_power_eog]
    features += [np.max(eog_datum)-np.min(eog_datum)]
    return np.asarray(features)

