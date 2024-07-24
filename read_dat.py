# mmap file reading and convert to csv
# Jaeyoung

from numpy import load
import numpy as np
import mmap
import csv

#file_path = 'experiment_data/5m-music-5m-typing/eeg.dat'
file_path = 'experiment_data/1716587413.4813533/eeg.dat'
 
with open(file_path, 'r') as file:
    mm = np.memmap(file,  dtype=np.float64,mode = 'r')
    # content = mm.read().decode()
    # lines = mm.read().decode('utf-8').splitlines()
    # data = [line.split(',') for line in lines]
    # with open('output.csv', 'w', newline='') as f:
    #     writer = csv.writer(f)
    #     writer.writerows(data)
    # content = file.read()
    # display data size and type of mm
    print(mm.shape)
    print(mm.size)
    print(mm)
    

# data = load('experiment_data/5m-music-5m-typing/eeg.dat' , allow_pickle=True)
# lst = data.files
# for item in lst:
#     print(item)
#     print(data[item])
