"""
MIT License

Copyright (c) 2021 giocic2

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import serial
from datetime import datetime
import os.path
import re
import itertools
import numpy as np
import matplotlib.pyplot as plt
from scipy import signal
from scipy.fft import fftshift

SAMPLING_FREQUENCY = 3e3 #Hz
time_resolution = 1/SAMPLING_FREQUENCY # s
ACQUISITION_TIME = 6
SAMPLES_PER_FRAME = 128
frames = round(ACQUISITION_TIME * SAMPLING_FREQUENCY / SAMPLES_PER_FRAME)
overhead = 100
lines_read = (frames * 8 + 1 + 1) * 2 + overhead

# ANALYSIS SETTINGS
FFT_RESOL = 1 # Hz
SMOOTHING_WINDOW = 10 # Hz
BANDWIDTH_THRESHOLD = 6 # dB
ZERO_FORCING = True # Enable forcing FFT to zero, everywhere except between FREQUENCY_MIN and FREQUENCY_MAX
FREQUENCY_MIN = -1_000 # Hz
FREQUENCY_MAX = 1_000 # Hz

# FFT bins and resolution
freqBins_FFT = int(2**np.ceil(np.log2(abs(SAMPLING_FREQUENCY/2/FFT_RESOL))))
print('FFT resolution: ' + str(SAMPLING_FREQUENCY / freqBins_FFT) + ' Hz')
print('FFT bins: ' + str(freqBins_FFT))
smoothingBins = int(round(SMOOTHING_WINDOW / (SAMPLING_FREQUENCY / freqBins_FFT)))
print('Size of smoothing window (moving average): ' + str(smoothingBins) + ' bins')
minBin = int(freqBins_FFT/2 + np.round(FREQUENCY_MIN / (SAMPLING_FREQUENCY/freqBins_FFT)))
FREQUENCY_MIN = -SAMPLING_FREQUENCY/2 + minBin * SAMPLING_FREQUENCY/freqBins_FFT
print("Minimum frequency of interest: {:.1f} Hz".format(FREQUENCY_MIN))
maxBin = int(freqBins_FFT/2 + np.round(FREQUENCY_MAX / (SAMPLING_FREQUENCY/freqBins_FFT)))
FREQUENCY_MAX = -SAMPLING_FREQUENCY/2 + maxBin * SAMPLING_FREQUENCY/freqBins_FFT
print("Maximum frequency of interest: {:.1f} Hz".format(FREQUENCY_MAX))

# Boolean variable that will represent 
# whether or not the Sense2GoL is connected
connected = False

# establish connection to the serial port that your Sense2GoL 
# is connected to.

LOCATIONS=['COM6']

for device in LOCATIONS:
    try:
        print("Trying...",device)
        S2GL = serial.Serial(device, 128000)
        break
    except:
        print("Failed to connect on ",device)

# loop until the Sense2GoL tells us it is ready
while not connected:
    serin = S2GL.read()
    connected = True

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
samplesFileName = timestamp + ".txt"
completeFileName = os.path.join('S2GL_raw-data',samplesFileName)
# open text file to store the current   
text_file = open(completeFileName, 'wb')
# read serial data and write it to the text file
index = 0
print("Acquisition started...")
while index <= lines_read:
    if S2GL.inWaiting():
        x=S2GL.readline()
        text_file.write(x)
        if x=="\n":
             text_file.seek(0)
             text_file.truncate()
        text_file.flush()
    index += 1
print("Raw data acquisition completed.")
# close the serial connection and text file
text_file.close()
S2GL.close()

# Extract raw samples from txt file
text_file = open(completeFileName, 'rb')
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

# plt.plot(timeAxis, I_array)
# plt.ylabel('Voltage (ADC level)')
# plt.xlabel('Time [sample number]')
# plt.grid(True)
# plt.title("IFI")
# plt.show()

# plt.plot(timeAxis, Q_array)
# plt.ylabel('Voltage (ADC level)')
# plt.xlabel('Time [sample number]')
# plt.grid(True)
# plt.title("IFQ")
# plt.show()

# Spectrogram computation
f, t, Sxx = signal.spectrogram(complexSignal_mV, fs=SAMPLING_FREQUENCY, nfft=512, nperseg=128, noverlap=16, return_onesided=False, detrend='constant', scaling='spectrum')
plt.pcolormesh(t, fftshift(f), fftshift(Sxx, axes=0), shading='flat')
plt.ylabel('Frequency [Hz]')
plt.xlabel('Time index')
plt.ylim([-400, 400])
plt.show()