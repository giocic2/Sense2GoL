import re
import itertools
import numpy as np
import matplotlib.pyplot as plt
from scipy import signal
from scipy.fft import fftshift
import easygui

SAMPLING_FREQUENCY = 3e3 #Hz
time_resolution = 1/SAMPLING_FREQUENCY # s

filename = None
while filename == None:
    filename = easygui.fileopenbox(title = "Choose *.txt file to analyse...", default = "*.txt")
print(filename)

# Extract raw samples from txt file
text_file = open(filename, 'rb')
temp_line = text_file.readline()
done = False
I_samples = []
Q_samples = []
# Locate I samples
temp_line = text_file.readline()
temp_line = temp_line.decode('ascii')
while temp_line != '  ------------- I raw samples ------------- \n':
    temp_line = text_file.readline()
    temp_line = temp_line.decode('ascii')

while not done:
    if temp_line == '  ------------- I raw samples ------------- \n':
        temp_line = text_file.readline()
        temp_line = temp_line.decode('ascii')
        while temp_line != '  ------------- Q raw samples ------------- \n':
            temp_line_int = list(map(int, re.findall(r'\d+', temp_line)))
            if temp_line_int != '\r\n':
                I_samples = list(itertools.chain(I_samples, temp_line_int))
            temp_line = text_file.readline()
            temp_line = temp_line.decode('ascii')
            if temp_line == '':
                done = True
                break
        if temp_line == '  ------------- Q raw samples ------------- \n':
            temp_line = text_file.readline()
            temp_line = temp_line.decode('ascii')
    temp_line_int = list(map(int, re.findall(r'\d+', temp_line)))
    if temp_line_int != '\r\n' and temp_line != '':
        Q_samples = list(itertools.chain(Q_samples, temp_line_int))
    temp_line = text_file.readline()
    temp_line = temp_line.decode('ascii')
    if temp_line == '':
        done = True
print("Raw data extracted from .txt file.")
print("Number of IFI samples: ", len(I_samples))
print("Number of IFQ samples: ", len(Q_samples))

array_length = min(len(I_samples), len(Q_samples))
print("Processed signals length: ", array_length)

# Seems that Q and I needs to be inverted
Q_array = np.array(I_samples[0:array_length])
I_array = np.array(Q_samples[0:array_length])

complexSignal_mV = np.array(array_length)
complexSignal_mV = np.add(I_array, 1j*Q_array)

timeAxis = np.linspace(start=0, num=array_length, stop=array_length, endpoint=False)

plt.plot(timeAxis, I_array)
plt.ylabel('Voltage (ADC level)')
plt.xlabel('Time [sample number]')
plt.grid(True)
plt.title("IFI")
plt.show()

plt.plot(timeAxis, Q_array)
plt.ylabel('Voltage (ADC level)')
plt.xlabel('Time [sample number]')
plt.grid(True)
plt.title("IFQ")
plt.show()

# Spectrogram computation
# f, t, Sxx = signal.spectrogram(complexSignal_mV, fs = SAMPLING_FREQUENCY, nperseg = 256, nfft = 256, scaling = 'spectrum', mode='complex')
f, t, Sxx = signal.spectrogram(complexSignal_mV, fs=SAMPLING_FREQUENCY, nfft=2048, nperseg=64, noverlap=16, return_onesided=False)
plt.pcolormesh(t, fftshift(f), fftshift(Sxx, axes=0), shading='gouraud')
plt.ylabel('Frequency [Hz]')
plt.xlabel('Time index')
##plt.axis([0, 2, 0, 1000])
plt.show()