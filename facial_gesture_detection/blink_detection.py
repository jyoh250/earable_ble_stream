import numpy as np
import scipy
import scipy.signal

blink_window_len_s = 0.25 # Sliding window length in seconds
blink_window_stride_s = 0.25 # Sliding window stride in seconds
blink_search_region_size = 1 # Window length of proposed candidate regions

def candidate_blink_region(eogl, eogr, amplitude_std_dev_thresh=50):
    '''
    Determine if the signal segment has enough EOG fluctuation for a blink to have occurred.
    
    input:
        eogl: EOG-L signal segment
        eogr: EOG-R signal segment
        amplitude_std_dev_thresh: Singal amplitude deviation threshold
    output:
        Boolean indicating if the signal segment has enough EOG fluctuation 
        for a blink to have occurred (True) or not (False)
    '''
    virtual_channel = np.mean(np.array([eogl, eogr]), axis=0)
    if np.std(virtual_channel) >= amplitude_std_dev_thresh:
        return True
    return False

def get_consective_inds(inds):
    consecutive_inds = []
    if len(inds) == 0:
        return consecutive_inds
    sublist = [inds[0]]
    for i in range(1, len(inds)):
        if inds[i] == sublist[-1]+1:
            sublist.append(inds[i])
        else:
            if len(sublist) > 0:
                consecutive_inds.append(sublist)
            sublist = [inds[i]]
    if len(sublist) > 0:
        consecutive_inds.append(sublist)
    return consecutive_inds
    
def get_blink_peak_inds(eogl_seg, eogr_seg, fs, start_idx=0, min_blink_amp=100, \
                        max_blink_amp=400, min_blink_prominence=125, lr_correlation_thresh=0.6):
    '''
    Determine if the candidate signal segment contains any blink events and find the peak indices
    of these detected events.
    
    input:
        eogl_seg: EOG-L signal segment
        eogr_seg: EOG-R signal segment
        fs: Sampling rate of signal data
        start_idx: Sample index of signal segment start
        min_blink_amp: Minimum amplitude of blink event
        max_blink_amp: Maximum amplitude of blink event
        lr_correlation_thresh: EOG Left/Right Correlation Threhsold
        
    output:
        blink_peak_inds: List of peak indicies for detected blink events
    '''
    blink_peak_inds = []
    virtual_seg = np.mean(np.array([eogl_seg, eogr_seg]), axis=0)
    #peak_inds = scipy.signal.find_peaks(virtual_seg, prominence=min_blink_amp)[0]
    peak_inds = []
    threshold_amplitude_inds = np.where(virtual_seg >= min_blink_amp)[0]
    if len(threshold_amplitude_inds) > 0:
        consecutive_threshold_amplitude_inds = get_consective_inds(threshold_amplitude_inds)
        for i in range(len(consecutive_threshold_amplitude_inds)):
            inds = np.array(consecutive_threshold_amplitude_inds[i])
            candidate_peak = inds[np.argmax(virtual_seg[inds])]
            peak_inds.append(candidate_peak)
    # Evaluate peak prominences
    peak_inds = np.array(peak_inds)
    peak_prominences = scipy.signal.peak_prominences(virtual_seg, peak_inds)[0]
    peak_inds = peak_inds[peak_prominences >= min_blink_prominence]
    
    for peak_ind in peak_inds:
        if (eogl_seg[peak_ind] > max_blink_amp) or (eogr_seg[peak_ind] > max_blink_amp):
            continue
        if np.corrcoef(eogl_seg, eogr_seg)[0,1] < lr_correlation_thresh:
            continue
        peak_ind = start_idx+peak_ind
        blink_peak_inds.append(peak_ind)
    return blink_peak_inds
