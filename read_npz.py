from numpy import load

data = load('/home/user/band/Earable/earable_ble_stream-main/experiment_data/5m-music-5m-typing/recording_data.npz', allow_pickle=True)
all = []
lst = data.files
for item in lst:
    print(item)
    print(data[item])
    all.append(data[item])

# find the maximum and minimum values in the data
# max_val = 0
# min_val = 0
# for i in range(len(all)):
#     if max(all[i]) > max_val:
#         max_val = max(all[i])
#     if min(all[i]) < min_val:
#         min_val = min(all[i])
# print(max_val)
# print(min_val)

    