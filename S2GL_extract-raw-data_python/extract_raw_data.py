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
ACQUISITION_TIME = 10 # s
SAMPLES_PER_FRAME = 128
frames = ACQUISITION_TIME * SAMPLING_FREQUENCY / SAMPLES_PER_FRAME
overhead =1000
lines_read = frames * 8 + 1 + 1 + overhead

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
while index <= 2_000:
    if S2GL.inWaiting():
        x=S2GL.readline()
        text_file.write(x)
        if x=="\n":
             text_file.seek(0)
             text_file.truncate()
        text_file.flush()
        print(index)
    index += 1

# close the serial connection and text file
text_file.close()
S2GL.close()
print("Raw data acquisition completed.")

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

Q_array = np.array(I_samples[0:array_length])
I_array = np.array(Q_samples[0:array_length])

complexSignal_mV = np.array(array_length)
complexSignal_mV = np.add(I_array, 1j*Q_array)

timeAxis_s = np.linspace(start=0, num=array_length, stop=array_length, endpoint=False) * time_resolution

plt.plot(timeAxis_s, I_array)
plt.ylabel('Voltage (mV)')
plt.xlabel('Time (s)')
plt.grid(True)
plt.title("IFI")
plt.show()

plt.plot(timeAxis_s, Q_array)
plt.ylabel('Voltage (mV)')
plt.xlabel('Time (s)')
plt.grid(True)
plt.title("IFQ")
plt.show()

SAMPLING_FREQUENCY = 3e3 # Hz

# Spectrogram computation
# f, t, Sxx = signal.spectrogram(complexSignal_mV, fs = SAMPLING_FREQUENCY, nperseg = 256, nfft = 256, scaling = 'spectrum', mode='complex')
f, t, Sxx = signal.spectrogram(complexSignal_mV, fs=SAMPLING_FREQUENCY, nfft=2048, nperseg=64, noverlap=16, return_onesided=False)
plt.pcolormesh(t, fftshift(f), fftshift(Sxx, axes=0), shading='gouraud')
plt.ylabel('Frequency')
plt.xlabel('Time')
##plt.axis([0, 2, 0, 1000])
plt.show()