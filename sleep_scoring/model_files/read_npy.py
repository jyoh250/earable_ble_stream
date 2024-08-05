import numpy as np

data = np.load('./feature_train_means.npy')

print(data[0].size)
print(f"The size of the loaded array is: {data.size}")
