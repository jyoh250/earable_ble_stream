import os
import sys
import time
import numpy as np

class Experiment():
    def __init__(self, num_eeg_channels=6, eeg_sampling_rate=125, num_ppg_channels=3, ppg_sampling_rate=50, \
                 num_imu_channels=3, imu_sampling_rate=25, max_streaming_time_s=int(60*60*1), params={}, \
                 device_id='Unspecified Earable Device', experiment_id=None):
        
        if experiment_id is None:
            experiment_id = 'experiment_{}'.format(time.time())
        self.experiment_id = experiment_id
        self.device_id = device_id
        print('Creating data recording object for {}.  Data will be saved to ./{}'.format(self.experiment_id, self.experiment_id))
        if not os.path.isdir(self.experiment_id):
            os.mkdir(self.experiment_id)
        else:
            sys.exit('Datapath already exists. Exiting.')
            
        self.params = params
        
        self.eeg_sampling_rate = eeg_sampling_rate
        #self.eeg_data = np.empty((int(eeg_sampling_rate*max_streaming_time_s),num_eeg_channels))
        self.eeg_data = np.memmap(os.path.join(self.experiment_id, 'eeg.dat'), dtype=np.float64, mode='w+', \
                                  shape=(int(eeg_sampling_rate*max_streaming_time_s),num_eeg_channels))
        self.eeg_data_size = 0
        self.eeg_sampled_per_packet = []
        self.eeg_packetread_timestamps = []
        self.eeg_fw_packet_timestamps = []
        
        self.ppg_sampling_rate = ppg_sampling_rate
        self.ppg_data = np.memmap(os.path.join(self.experiment_id, 'ppg.dat'), dtype=np.float64, mode='w+', \
                                  shape=(int(ppg_sampling_rate*max_streaming_time_s),num_ppg_channels))
        self.ppg_data_size = 0
        self.ppg_packetread_timestamps = []
        
        self.imu_sampling_rate = imu_sampling_rate
        self.imu_data = np.memmap(os.path.join(self.experiment_id, 'imu.dat'), dtype=np.float64, mode='w+', \
                                  shape=(int(imu_sampling_rate*max_streaming_time_s),num_imu_channels))
        self.imu_data_size = 0
        self.imu_packetread_timestamps = []
        
        self.event_timestamps = []

    def add_eeg_data(self, data, pc_timestamp, timestamp):
        if self.eeg_data_size >= int(self.eeg_data.shape[0]*0.8):
            self.eeg_data.flush()
            old_length = self.eeg_data.shape[0]
            old_num_channels = self.eeg_data.shape[1]
            self.eeg_data = np.memmap(os.path.join(self.experiment_id, 'eeg.dat'), dtype=np.float64, mode='r+', \
                                      shape=(old_length*2,old_num_channels))
        new_data_size = self.eeg_data_size+data.shape[0]
        self.eeg_data[self.eeg_data_size:new_data_size,:] = np.array(data)
        self.eeg_data_size = new_data_size
        self.eeg_packetread_timestamps.append(pc_timestamp)
        self.eeg_fw_packet_timestamps.append(timestamp)
        self.eeg_sampled_per_packet.append(data.shape[0])
        
    def add_ppg_data(self, data, timestamp):
        if self.ppg_data_size >= int(self.ppg_data.shape[0]*0.8):
            self.ppg_data.flush()
            old_length = self.ppg_data.shape[0]
            old_num_channels = self.ppg_data.shape[1]
            self.ppg_data = np.memmap(os.path.join(self.experiment_id, 'ppg.dat'), dtype=np.float64, mode='r+', \
                                      shape=(old_length*2,old_num_channels))
        new_data_size = self.ppg_data_size+data.shape[0]
        self.ppg_data[self.ppg_data_size:new_data_size,:] = np.array(data)
        self.ppg_data_size = new_data_size
        self.ppg_packetread_timestamps.append(timestamp)
        
    def add_imu_data(self, data, timestamp):
        if self.imu_data_size >= int(self.imu_data.shape[0]*0.8):
            self.imu_data.flush()
            old_length = self.imu_data.shape[0]
            old_num_channels = self.imu_data.shape[1]
            self.imu_data = np.memmap(os.path.join(self.experiment_id, 'imu.dat'), dtype=np.float64, mode='r+', \
                                      shape=(old_length*2,old_num_channels))
        new_data_size = self.imu_data_size+data.shape[0]
        self.imu_data[self.imu_data_size:new_data_size,:] = np.array(data)
        self.imu_data_size = new_data_size
        self.imu_packetread_timestamps.append(timestamp)
        
    def add_event_timestamp(self, timestamp):
        self.event_timestamps.append(timestamp)
        
    def save_data(self):
        np.savez(os.path.join(self.experiment_id, 'recording_data.npz'), \
                 device_id=self.device_id, \
                 params=self.params, \
                 eeg_data_size=self.eeg_data_size, \
                 ppg_data_size=self.ppg_data_size, \
                 imu_data_size=self.imu_data_size, \
                 eeg_packetread_timestamps=np.array(self.eeg_packetread_timestamps), \
                 eeg_fw_packet_timestamps=np.array(self.eeg_fw_packet_timestamps), \
                 ppg_packetread_timestamps=np.array(self.ppg_packetread_timestamps), \
                 imu_packetread_timestamps=np.array(self.imu_packetread_timestamps), \
                 event_timestamps=np.array(self.event_timestamps))
        self.eeg_data.flush()
        self.ppg_data.flush()
        self.imu_data.flush()
