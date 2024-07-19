import numpy
import pandas
import sounddevice as sd
from datetime import datetime

class AudioStimulation:
	def __init__(self):
		print("An entity of Audio Stimulation module")

	# def audio_play(self, fPath):
	# 	winsound.PlaySound(fPath, winsound.SND_ASYNC + winsound.SND_LOOP)
	
	# def audio_stop(self):
	# 	winsound.PlaySound(None, winsound.SND_PURGE)

	# Generate a pure tone
	def PureTone_generate(self, duration, fs, Am, fa):
		t = numpy.arange(0, duration, 1/fs)
		y = Am * numpy.sin(2*numpy.pi*fa*t)

		return y

	# Generate a tone with amplitude modulation
	def AMTone_generate(self, duration, fs, Am, m, fa, fc):
		t = numpy.arange(0, duration, 1/fs)
		Ac = Am/m
		
		y = numpy.multiply(Ac*(1+m*numpy.sin(2*numpy.pi*fa*t)), numpy.sin(2*numpy.pi*fc*t))

		return y

	# Generate a tone with frequency modulation
	def FMTone_generate(self, duration, fs, Am, m, fa, fc):
		t = numpy.arange(0, duration, 1/fs)
		Ac = Am

		y = Ac * numpy.cos(2*numpy.pi*fc*t + m*numpy.sin(2*numpy.pi*fa*t))

		return y

	def voss(self, duration, fs):
		# Generate the pink noise using the Voss-McCartney algorithm
		nrows = duration*fs
		ncols = 16

		y = numpy.empty([nrows, ncols])
		y.fill(numpy.nan)
		y[0,:] = numpy.random.random(ncols)
		y[:,0] = numpy.random.random(nrows)

		# The total number of changes is nrows
		n = nrows
		cols = numpy.random.geometric(0.5, n)
		cols[cols >= ncols] = 0
		rows = numpy.random.randint(nrows, size=n)
		y[rows, cols] = numpy.random.random(n)

		df = pandas.DataFrame(y)
		df.fillna(method='ffill', axis=0, inplace=True)
		total = df.sum(axis=1)

		return total.values

	def fftnoise(self, f):
		f = numpy.array(f, dtype='complex')
		Np = (len(f) - 1) // 2
		phases = numpy.random.rand(Np) * 2 * numpy.pi
		phases = numpy.cos(phases) + 1j * numpy.sin(phases)
		f[1:Np+1] *= phases
		f[-1:-1-Np:-1] = numpy.conj(f[1:Np+1])

		return numpy.fft.ifft(f).real

	def band_limited_pink_noise_generate(self, min_freq, max_freq, duration, fs):
		number_of_samples = duration*fs
		freqs = numpy.abs(numpy.fft.fftfreq(number_of_samples, 1/fs))
		f = numpy.zeros(number_of_samples)
		idx = numpy.where(numpy.logical_and(freqs>=min_freq, freqs<=max_freq))[0]
		f[idx] = 1

		y = self.fftnoise(f)
		y = numpy.int16(y * (2**15 - 1))

		return y

	def white_noise_generate(self, duration, fs):
		state = numpy.random.RandomState()
		length = duration*fs
		y = state.randn(length)

		return y

	def binaural_beats_generate(self, duration, fs, AmL, faL, AmR, faR):
		left_channel = self.PureTone_generate(duration, fs, AmL, faL)
		right_channel = self.PureTone_generate(duration, fs, AmR, faR)
		y = numpy.column_stack([left_channel, right_channel])

		return y;

	def audio_play(self, audio, fs):
		sd.default.channels = 2

		start_time = datetime.now()
		sd.play(audio, fs, loop=True)

		start_time_str = start_time.strftime('%Y-%m-%d_%H-%M-%S.%f')[:-3]
		print(start_time_str)
	
	def audio_stop(self):
		start_time = datetime.now()
		sd.stop()

		start_time_str = start_time.strftime('%Y-%m-%d_%H-%M-%S.%f')[:-3]
		print(start_time_str)