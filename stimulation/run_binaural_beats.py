import sys
import time
import numpy as np
import Stimulations
import sounddevice

if __name__ == '__main__':
    timestamp_save_fpath = sys.argv[2]
    binaural_audio_timestamps = np.zeros(2)
    audio_fs = 44100
    finVolume = 1
    carrier_frequency = 250
    frequency = int(sys.argv[1])
    duration_seconds = 330
    audio_stim = Stimulations.AudioStimulation()
    binaural_beats_audio = audio_stim.binaural_beats_generate(duration_seconds, audio_fs, finVolume, carrier_frequency, \
                                                              finVolume, carrier_frequency+frequency)
    binaural_audio_timestamps[0] = time.time()
    sounddevice.play(binaural_beats_audio, audio_fs)
    sounddevice.wait()
    binaural_audio_timestamps[1] = time.time()
    np.save(timestamp_save_fpath, binaural_audio_timestamps)
    sys.exit(0)
