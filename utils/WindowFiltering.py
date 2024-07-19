import numpy as np
import scipy.signal

class WindowIIRNotchFilter():
    '''
    Class for real time IIR notch filtering.
    '''
    def __init__(self, w0, Q, fs):
        '''
        Arguments:
            w0: Center frequency of notch filter.
            Q: Quality factory of notch filter.
            fs: Sampling rate of signal that filtering will be performed on.
        '''
        self.w0 = w0
        self.Q = Q
        self.fs = fs
        self.initialize_filter_params()
        
    def initialize_filter_params(self):
        '''
        Initialize IIR notch filter parameters.
        '''
        self.b, self.a = scipy.signal.iirnotch(self.w0, self.Q, self.fs)
    
    def filter_data(self, x):
        '''
        Apply notch filter to signal sample x.
        
        input:
            x: Window of signal data
        output:
            result: Filtered signal data
        '''
        x = np.reshape(x, (-1,))
        result = scipy.signal.filtfilt(self.b, self.a, x)
        return result
    
class WindowButterBandpassFilter():
    '''
    Class for real time Butterworth Bandpass filtering.
    '''
    def __init__(self, order, low, high, fs):
        '''
        Arguments:
            order: Bandpass filter order.
            low: Lower cutoff frequency (Hz).
            high: Higher cutoff frequency (Hz).
            fs: Sampling rate of signal that filtering will be performed on.
        '''
        self.order = order
        self.low = low
        self.high = high
        self.fs = fs
        self.initialize_filter_params()
        
    def initialize_filter_params(self):
        '''
        Initialize filter parameters.
        '''
        self.b, self.a = scipy.signal.butter(self.order, [self.low, self.high], btype='band',fs=self.fs)
        self.z = scipy.signal.lfilter_zi(self.b, self.a)
        
    def filter_data(self, x):
        '''
        Apply bandpass filter to signal sample x.
        
        input:
            x: Window of signal data
        output:
            result: Filtered signal data
        '''
        x = np.reshape(x, (-1,))        
        filtered_data = np.zeros_like(x)
        for i in range(x.shape[0]):
            result, z = scipy.signal.lfilter(self.b, self.a, [x[i]], zi=self.z)
            filtered_data[i] = result.item()
            self.z = z
        return np.array(filtered_data)


class WindowFilter():
    '''
    Sliding window filtering class for de-noising slow wave data in deep sleep epochs.
    '''
    def __init__(self, filters):
        '''
        Arguments:
            filters: list of RealTime filter objects
        '''
        self.filters = filters
        
    def initialize_filter_params(self):
        '''
        Initializes RealTime filter object parameters.
        '''
        for filt in self.filters:
            filt.initialize_filter_params()
    
    def filter_data(self, x):
        '''
        Apply RealTime filters to signal sample x.
        
        input:
            x: Window of signal data
        output:
            result: Filtered signal data
        '''
        for filt in self.filters:
            x = filt.filter_data(x)
        return x