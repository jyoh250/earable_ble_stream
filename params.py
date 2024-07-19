visualization_timescale = 15
data_save_frequency = 15
eeg_display_amplitudes = [-200, 200]
VISUALIZATION_ON = True
max_streaming_time_s=int(60*60*1)

event_ids = {'generic_event': -1,
             'left_eye_gaze': 0,
             'right_eye_gaze': 1,
             'blink': 2,
             'jaw_clench': 3,
	     'movement': 4}
event_key_bindings = {'space': -1, 
                      'l': 0, 
                      'r': 1, 
                      'b': 2, 
                      'j': 3,
		      'm': 4}
event_colors = {-1: 'grey',
                0: 'green',
                1: 'blue',
                2: 'black',
                3: 'red',
		4: 'purple'}

num_eeg_channels = 6
eeg_sampling_rate = 125
eeg_channel_names = ['ch1_LF5-FpZ','ch2_OTE_L-FpZ','ch3_BE_L-FpZ','ch4_RF6-FpZ','ch5_OTE_R-FpZ','ch6_BE_R-FpZ']

num_imu_channels = 3
imu_sampling_rate = 50
imu_channel_names = ['imu_x','imu_y','imu_z']

num_ppg_channels = 3
ppg_sampling_rate = 25

all_params = {'visualization_timescale':visualization_timescale, \
              'data_save_frequency':data_save_frequency, \
              'eeg_display_amplitudes':eeg_display_amplitudes, \
              'visualization_on':VISUALIZATION_ON, \
              'max_streaming_time_s':max_streaming_time_s, \
              'event_ids':event_ids, \
              'event_key_bindings':event_key_bindings, \
              'event_colors':event_colors, \
              'num_eeg_channels':num_eeg_channels, \
              'eeg_sampling_rate':eeg_sampling_rate, \
              'num_imu_channels': num_imu_channels, \
              'imu_sampling_rate': imu_sampling_rate, \
              'num_ppg_channels': num_ppg_channels, \
              'ppg_sampling_rate': ppg_sampling_rate}
