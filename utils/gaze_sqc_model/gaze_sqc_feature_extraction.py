import numpy as np
import scipy
from scipy import signal, stats
from scipy.fft import fft, fftfreq
from scipy.integrate import simps
import antropy

sqc_window_len_s = 3
sqc_window_stride_s = 1
MIN_FFT_MAG = 1e-7

def compute_band_powers(datum, fs, bands=[0.1,2,4,8,13,20,60], normalize=True):
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


def extract_sqc_features(data, fs):
    bp_features = list(compute_band_powers(data, fs, bands=[0.2,2,4,8,13,20,60], normalize=False))
    bp_features_normed = list(compute_band_powers(data, fs, bands=[0.2,2,4,8,13,20,60], normalize=True))
    bp_features = bp_features + bp_features_normed
    statistical_features = [np.max(data), np.mean(np.abs(data))]
    entropy_features = [scipy.stats.entropy(np.abs(data)), antropy.higuchi_fd(data)]
    features = bp_features + statistical_features + entropy_features
    return np.array(features)