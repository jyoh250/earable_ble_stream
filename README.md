# earable_ble_stream

Environment Setup:
A requirements file has been added to enable easy isntallation of all required python modules for this application.  These can be installed via
```
pip install -r requirements.txt
```

Additionally, a directory, named experiment_data should be created.  This is where all epxerimental data will be saved:
```
cd experiment_data
```

To run basic visualization application: 
```
sudo python BLEApp.py --device_id device_name
```

For example:
```
sudo python BLEApp.py --device_id EB_DEV584b
```

Notes:
- `sudo` must be used to enable logging of keystrokes that define user events
- There may be lag in the real time visualization.  This can be reduced by decreasing the size of the visualiztion window.  Lag in the visualization does not impact the streaming data (all of this is recorded asynchronously in a separate thread)

___

# Data Collection

## MRT Test

The data collected in this test will be used in the development of the Earable Focus algorithm.  Throughout this test, you will be asked to respond to a metronome tone as quickly and accurately as possible using the spacebar on your keyboard.  Throughout the test, a series of questions will be asked about your level of focus during the task.  Please answer the questions to the best of your ability via your keyboard.  Music will be played periodically in attempt to distract you.  
The task will last 20 minutes.  Please remain as still as possible throughout the duration of the test to ensure reliable data quality.  Before starting the test, please confirm that the volume on you PC is turned on loud enough to hear music that will be played during the test.

**Part 1: Device Setup and Signal Quality Assurance**
1. Turn the device on.
2. Run `python list_ble_devices.py` to obtain a list of the available Bluetooth Low Energy devices nearby.  Find the name of your device in this list, for example, *EB_DEV574d*.  In the next steps, we will refer to this name as *device_name*.
3. Put the device on your head.  To obtain better data quality, please confirm that the headband is worn snuggly around your head.
4. Run the BLEApp.py app to visualize the signals being received at each of the 6 channels.  You can cycle through the channels by pressing the **CH** button on the visualization.  Adjust the headband until you obtain good quality signals at each of the 6 channels.  Note: If the visualization is running slowly, try resizing the visualization window so that it is smaller.  This step is run with `sudo python BLEApp.py --device_id device_name`.
5. Once good signal quality has been established at all channels, exit the BLEApp program by entering `CTRL+C` on your keyboard.  This will disconnect the band from the computer.  If you observe “Client Closed” in the system output, and the program still has not stopped, enter `CTRL+C` once more.
6. Turn the device off but do not remove from head.


**Part 2: MRT Test**
1. Select an experiment name (for example, name-of-subject_trial-number_date.  We will call this selected name *experiment_name* in the following steps.
2. Turn the device on.
3. Start the MRT test with `sudo python BLEApp.py --device_id device_name --experiment_id experiment_name --mrt --no_visualization`.  This will open a new window with the MRT test available.
4. Before starting the test, the subject should sit still, resting comfortably for one minute with their eyes closed.  The subject should then sit still and relaxed for one minute with their eyes opened.
5. The subject may now start the test by following the instructions on the MRT UI. Follow the instructions of the MRT test and perform it. Focus on achieving quick and accurate responses to the metronome signal.
6. Once the MRT test has completed, the MRT UI should exit automatically. Exit the BLEApp program by entering `CTRL+C` on your keyboard.  This will disconnect the headband from the computer.  If you observe “Client Closed” in the system output, and the program still has not stopped, enter `CTRL+C` once more.
7. Turn the device off.
8. Navigate to the google drive folder [linked here](https://drive.google.com/drive/folders/1ZV7KdyuUp7Wcxz8h05wFhHhl09fK6NGy?usp=sharing) and create a new folder called *experiment_name*.  Upload the sub-folders named `./experiment_data/experiment_name` and `./focus/MRT/data/experiment_name` to this google drive folder that you created.

___

## Binaural Beats Test

The data collected in this test will be used in the development of the Smart Alarm algorithm.  Throughout this test, you will simply need to sit still, relaxed with your eyes closed.  The test will last approximately 10 minutes.  During the first 5 minutes, there will be no audio played.  During the last 5 minutes, binaural beats audio will be played.  Please remain as still as possible throughout the duration of the test to ensure reliable data quality.  Before starting the test, please confirm that the volume on you PC is turned on loud enough to hear music that will be played during the test.  Headphones will be needed (i.e., not a speakers) for this test since the binaural beats are left/right ear specific

**Part 1: Device Setup and Signal Quality Assurance**
1. Turn the device on.
2. Run `python list_ble_devices.py` to obtain a list of the available Bluetooth Low Energy devices nearby.  Find the name of your device in this list, for example, *EB_DEV574d*.  In the next steps, we will refer to this name as *device_name*.
3. Put the device on your head.  To obtain better data quality, please confirm that the headband is worn snuggly around your head.
4. Run the BLEApp.py app to visualize the signals being received at each of the 6 channels.  You can cycle through the channels by pressing the **CH** button on the visualization.  Adjust the headband until you obtain good quality signals at each of the 6 channels.  Note: If the visualization is running slowly, try resizing the visualization window so that it is smaller.  This step is run with `sudo python BLEApp.py --device_id device_name`.
5. Once good signal quality has been established at all channels, exit the BLEApp program by entering `CTRL+C` on your keyboard.  This will disconnect the computer from the computer.  If you observe “Client Closed” in the system output, and the program still has not stopped, enter `CTRL+C` once more.
6. Turn the device off but do not remove from head.


**Part 2: Binaural Beats Test**
1. Select an experiment name (for example, name-of-subject_trial-number_date.  We will call this selected name *experiment_name* in the following steps.
2. Turn the device on.
3. Start the test with `sudo python BLEApp.py --device_id device_name --experiment_id experiment_name --binaural_freq 6 --no_visualization`.
4. Remain still and relaxed with your eyes closed until the audio had been played and has stopped.
5. Once the audio has stopped (After about 10 minues) exit the BLEApp program by entering `CTRL+C` on your keyboard.  This will disconnect the headband from the computer.  If you observe “Client Closed” in the system output, and the program still has not stopped, enter `CTRL+C` once more.
6. Turn the device off.
7. Navigate to the google drive folder [linked here](https://drive.google.com/drive/folders/163ig2cgi4M_2Zg5PwqKazGIrM3FtHaoG?usp=sharing) and create a new folder called *experiment_name*.  Upload the sub-folder named `./experiment_data/experiment_name` to this google drive folder that you created.
