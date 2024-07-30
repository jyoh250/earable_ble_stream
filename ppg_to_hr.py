# pip install numpy scipy matplotlib pyserial
#   1.	Serial Connection: The script sets up a serial connection to read raw PPG data from the sensor.
# 	2.	Filtering: A bandpass filter is applied to the raw data to remove noise. The butter_bandpass function designs a Butterworth bandpass filter, and bandpass_filter applies it to the data.
# 	3.	Peak Detection: The find_peaks function from the SciPy library is used to detect peaks in the filtered signal, which correspond to heartbeats.
# 	4.	Heart Rate Calculation: The time intervals between consecutive peaks are used to calculate the heart rate in beats per minute (bpm).
# 	5.	Plotting: The raw data, filtered data, and calculated heart rates are plotted in real-time using Matplotlib.
#  This example assumes that the raw PPG data from the sensor is a simple integer value sent over the serial connection. 
#  May need to adjust the code if the data format is different.
#  to make more accurate, refer to below link
#  https://github.com/ElliotY-ML/Heart_Rate_Estimation_PPG_Acc/blob/master/Part%20I%20Pulse%20Rate%20Algorithm/pulse_rate_EY_completed.ipynb
#  https://python-heart-rate-analysis-toolkit.readthedocs.io/en/latest/
#  https://neuropsychology.github.io/NeuroKit/functions/ppg.html

import serial
import time
import numpy as np
from scipy.signal import butter, filtfilt, find_peaks
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# Serial connection setup (update 'COM3' to your Arduino's serial port)
ser = serial.Serial('COM3', 115200)
time.sleep(2)

# Filtering parameters
fs = 100  # Sampling frequency (Hz)
lowcut = 0.5  # Lower cutoff frequency (Hz)
highcut = 3.0  # Upper cutoff frequency (Hz)

def butter_bandpass(lowcut, highcut, fs, order=5):
    nyquist = 0.5 * fs
    low = lowcut / nyquist
    high = highcut / nyquist
    b, a = butter(order, [low, high], btype='band')
    return b, a

def bandpass_filter(data, lowcut, highcut, fs, order=5):
    b, a = butter_bandpass(lowcut, highcut, fs, order=order)
    y = filtfilt(b, a, data)
    return y

def read_data():
    if ser.in_waiting > 0:
        line = ser.readline().decode('utf-8').rstrip()
        if line.isdigit():
            return int(line)
    return None

# Data storage
raw_data = []
filtered_data = []
heart_rates = []
timestamps = []

# Peak detection parameters
distance = fs * 0.6  # Minimum distance between peaks in samples (assuming heart rate <= 100 bpm)

def update(frame):
    raw = read_data()
    if raw is not None:
        raw_data.append(raw)
        if len(raw_data) > fs * 10:  # Keep only the last 10 seconds of data
            raw_data.pop(0)
        
        filtered = bandpass_filter(raw_data, lowcut, highcut, fs)
        filtered_data.append(filtered[-1])
        if len(filtered_data) > fs * 10:
            filtered_data.pop(0)
        
        if len(filtered_data) > distance:
            peaks, _ = find_peaks(filtered_data, distance=distance)
            if len(peaks) > 1:
                peak_intervals = np.diff(peaks) / fs  # Convert to seconds
                heart_rate = 60.0 / np.mean(peak_intervals)  # Convert to bpm
                heart_rates.append(heart_rate)
                timestamps.append(time.time())
                if len(heart_rates) > 20:  # Keep only the last 20 heart rate readings
                    heart_rates.pop(0)
                    timestamps.pop(0)

        # Plotting
        plt.cla()
        plt.subplot(2, 1, 1)
        plt.plot(raw_data, label='Raw Data')
        plt.legend(loc='upper right')
        
        plt.subplot(2, 1, 2)
        plt.plot(timestamps, heart_rates, label='Heart Rate (bpm)', color='r')
        plt.xlabel('Time (s)')
        plt.ylabel('Heart Rate (bpm)')
        plt.legend(loc='upper right')

# Set up the plot
fig, ax = plt.subplots(2, 1)
ani = FuncAnimation(fig, update, interval=1000)  # Update every second

plt.show()

ser.close()