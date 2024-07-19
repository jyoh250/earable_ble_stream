from numpy import load


#file_path = 'experiment_data/5m-music-5m-typing/eeg.dat'
file_path = 'experiment_data/1716587413.4813533/eeg.dat'
 
with open(file_path, 'r') as file:
    content = file.read()
    print(content)

# data = load('experiment_data/5m-music-5m-typing/eeg.dat' , allow_pickle=True)
# lst = data.files
# for item in lst:
#     print(item)
#     print(data[item])
