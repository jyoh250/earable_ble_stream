import numpy as np
from utils.signal_processing import *

gaze_window_len_s = 4
gaze_window_stride_s = 0.5

lf5_rf6_gaze_params = {'min_dist_from_prev': 0.75,
                       'min_duration': 0.25,
                       'max_duration': 3.0,
                       'min_threshold_amp': 30,
                       'max_threshold_amp': 100,
                       'soft_zc_threshold': 0}

EYE_GAZE_MAPPING = {'Leftward Gaze': 1, 'Rightward Gaze': -1, 'Unknown Gaze': 0}
REVERSE_EYE_GAZE_MAPPING = {value: key for key, value in EYE_GAZE_MAPPING.items()}
def get_lateral_gaze_direction(eogl, eogr):
    '''
    Infers direction of a lateral eye gaze based on initial EOG-L
    and EOG-R deflections.
    
    input:
        eog_l: Left EOG Channel
        eog_r: Right EOG Channel
    output:
        gaze_ID: Integer ID of gaze direction
    '''
    peak_idx = np.argmax(-1*eogl*eogr)
    
    eogl_deflection = np.sign(eogl[peak_idx])
    eogr_deflection = np.sign(eogr[peak_idx])
    
    gaze_ID = EYE_GAZE_MAPPING['Unknown Gaze']
    if (eogl_deflection > 0) and (eogr_deflection < 0):
        gaze_ID = EYE_GAZE_MAPPING['Leftward Gaze']
    elif (eogl_deflection < 0) and (eogr_deflection > 0):
        gaze_ID = EYE_GAZE_MAPPING['Rightward Gaze']
    return gaze_ID

def get_candidate_eye_movements(eogl_seg, eogr_seg, fs, window_start=0, min_duration=0.25, max_duration=3.0, \
                                min_threshold_amp=50, max_threshold_amp=250, soft_zc_threshold=0):
    '''
    Gets start and end timestamps of candidate eye movements.
    
    input:
        eogl_seg: Segment of EOG-L signal data
        eogr_seg: Segment of EOG-R signal data
        fs: sampling rate of signal data
        window_time_offset: Timestamp of window
        min_duration: Minimum duration of candidate eye movement (seconds)
        max_duration: Maximum duration of candidate eye movement (seconds)
        min_threshold_amp: Minimum amplitude of EOG deflection (uV)
        max_threshold_amp: Maximum amplitude of EOG deflection (uV)
        soft_zc_threshold: Zero crossing amplitude threshold for identifying EOG deflections (uV)
    output:
        candidate_endpoints: List of start and end timestamps of candidate eye movements 
    '''
    candidate_endpoints = []
    
    virtual_seg = -1*(eogl_seg*eogr_seg) # Virtual EOG segment capturing opposite polarity deflections
    virtutal_min_threshold_amp = min_threshold_amp**2
    virtutal_max_threshold_amp = max_threshold_amp**2

    zero_crossing_points = np.where(np.diff(np.sign(eogl_seg-soft_zc_threshold)))[0]
    for zc_idx in range(len(zero_crossing_points)-1):
        # For each segment between zero crossings, validate the signal characteristics for eye movements
        zc0, zc1 = zero_crossing_points[zc_idx], zero_crossing_points[zc_idx+1]
        region_duration = (zc1-zc0)/fs

        amp_ratio_threshold = 0.5
        amp_ratio = np.max(np.abs(eogl_seg[zc0:zc1])) / np.max(np.abs(eogr_seg[zc0:zc1]))

        if (region_duration < min_duration) or (region_duration > max_duration):
            # Eye movement duration constraints not satisfied
            continue
        elif ((np.max(np.abs(eogl_seg[zc0:zc1])) < min_threshold_amp) or (np.max(np.abs(eogr_seg[zc0:zc1])) < min_threshold_amp)) \
              and ((amp_ratio < amp_ratio_threshold) or (amp_ratio > (1/amp_ratio_threshold))):
            # Ratio of EOG-L to EOG-R ampltitudes is too low/high (signals are asymetric and likely influenced by noise)
            continue
        elif (np.max(virtual_seg[zc0+1:zc1-1]) < virtutal_min_threshold_amp) or (np.max(virtual_seg[zc0+1:zc1-1]) > virtutal_max_threshold_amp):
            # Opposite polarity deflection amplitude constraints not satisfied
            continue
        elif (np.max(np.abs(eogl_seg[zc0+1:zc1-1])) < min_threshold_amp) or (np.max(np.abs(eogl_seg[zc0+1:zc1-1])) > max_threshold_amp) or \
             (np.max(np.abs(eogr_seg[zc0+1:zc1-1])) < min_threshold_amp) or (np.max(np.abs(eogr_seg[zc0+1:zc1-1])) > max_threshold_amp):
            # EOG deflection amplitude constraints not satisfied
            continue
        elif np.corrcoef(eogl_seg[zc0+1:zc1-1], eogr_seg[zc0+1:zc1-1])[0,1] > -0.5:
            # EOG-L and EOG-R signal segments do not have strong enough negative correlation
            continue
        start, stop = (zc0/fs)+window_start, (zc1/fs)+window_start

        candidate_endpoints.append([start, stop])
        
    return np.array(candidate_endpoints)


def detect_gaze(eogl, eogr, fs, group_endpoints, groupings, prev_endpoint_timestamp, window_time_offset=0, min_dist_from_prev=0.75, \
                min_duration=0.25, max_duration=3.0, min_threshold_amp=100, max_threshold_amp=250, soft_zc_threshold=0):
    eogl = eogl-np.mean(eogl)
    eogr = eogr-np.mean(eogr)
    
    eogl_base = base_filter(eogl, fs)
    eogr_base = base_filter(eogr, fs)
    
    eogl = butter_lowpass_filter(eogl, 10, fs)
    eogr = butter_lowpass_filter(eogr, 10, fs)
    
    eogl = butter_highpass_filter(eogl, 0.3, fs)
    eogr = butter_highpass_filter(eogr, 0.3, fs)
        
    #eogl_base, eogl = preprocess_eog_gaze_data(np.array(eogl), fs)
    #eogr_base, eogr = preprocess_eog_gaze_data(np.array(eogr), fs)
    window_start = window_time_offset-(len(eogl)/fs)
    candidate_endpoints = get_candidate_eye_movements(eogl, eogr, fs, window_start, min_duration=min_duration, max_duration=max_duration, \
                                                      min_threshold_amp=min_threshold_amp, max_threshold_amp=max_threshold_amp, \
                                                      soft_zc_threshold=soft_zc_threshold)
    eogl_deflection_data, eogr_deflection_data = None, None
    gaze_IDs = []
    if len(candidate_endpoints) > 0:
        for t0, t1 in candidate_endpoints:
            if ((t0-prev_endpoint_timestamp) >= min_dist_from_prev):
                if len(group_endpoints) > 0:
                    groupings.append([group_endpoints[0][0], group_endpoints[-1][1]])
                init_deflection_start = max(int(((t0-window_start))*fs), 0)
                init_deflection_stop = int(((t1-window_start))*fs)
                eogl_deflection_data = eogl_base[init_deflection_start:init_deflection_stop]
                eogr_deflection_data = eogr_base[init_deflection_start:init_deflection_stop]
                eogl_deflection_data = eogl_deflection_data-eogl_deflection_data[0]
                eogr_deflection_data = eogr_deflection_data-eogr_deflection_data[0]
                gaze_ID = get_lateral_gaze_direction(eogl_deflection_data, eogr_deflection_data)
                gaze_IDs.append(gaze_ID)
                #print('Time t={:.3f} to t={:.3f}: {}'.format(t0, t1, REVERSE_EYE_GAZE_MAPPING[gaze_ID]))
                group_endpoints = [[t0, t1]]
            else:
                if (len(group_endpoints) > 0) and (t1 <= group_endpoints[-1][-1]):
                    continue
                else:
                    group_endpoints.append([t0, t1])
            prev_endpoint_timestamp = t1
    #else:
    #    if len(group_endpoints) > 0:
    #        if (window_time_offset-group_endpoints[-1][1]) >= min_dist_from_prev:
    #            pass
    return gaze_IDs, group_endpoints, groupings, prev_endpoint_timestamp
    
