import numpy as np
import collections
import scipy.signal as sp
import pyaudio as pa
import time

import matplotlib.pyplot as plt

import pyaudio
p = pyaudio.PyAudio()
for i in range(p.get_device_count()):
    print(p.get_device_info_by_index(i))



print("=======================================================================")
print("                ^^^  Audio Init / Info Stuff   ^^^")
print("=======================================================================")

def nonint_decimate(sig, toRate, fromRate):
    # total length of time the input takes
    buffTime = sig.size / fromRate
    # timestamps of the samples we want to write to output
    newTimes = np.linspace(0, buffTime, int(toRate * buffTime), False)

    # Make mask with trues at indicies we want to keep
    idxs = np.round(newTimes * fromRate)

    mask = np.full(sig.size, False)
    for i in idxs:
        mask[int(i)] = True

    newSig = sig[mask]

    return newSig

raw = np.fromfile("./manch_atis.bin", dtype=np.int16)
iq = np.zeros(raw.size // 2, dtype = np.complex128)
iq = raw[0::2] + 1j * raw[1::2]
iq /= 2**15 - 1


amp = np.abs(iq)
db  = 10 * np.log10(amp ** 2)
print("Avg db pre gain: ", np.mean(db))

# Gain to simulate what we had at airpt
iq *= np.sqrt(10 ** ((1 - np.mean(db)) / 10))
amp = np.abs(iq)
db  = 10 * np.log10(amp ** 2)

rollingThresh = collections.deque(maxlen=100)

print("Avg db post gain: ", np.mean(db))

# chunk signal into sections
chunks = np.split(iq, iq.size // 2**20)

print("Chunked iq into", len(chunks), "sections of size", chunks[0].size)

audioFilt = sp.firwin(38, 10e3, fs=44100, window=("kaiser", 4))

plt.plot(np.abs(np.fft.fft(audioFilt)))
plt.show()

fs = 1000000.026490954
allAudio = np.empty(0, dtype=np.float32)
for chunk in chunks:
    # Filter
    filtIQ = np.convolve(chunk, sp.firwin(51, 20e3/2, fs=fs), mode='same')

    # Decode AM
    amp = np.abs(filtIQ)
    # normFact = np.max(amp)
    # if (normFact):
    #     amp /= normFact

    # Decimate
    audio = nonint_decimate(amp, 44100, fs)

    normFact = audio.max()
    if (normFact):
        rollingThresh.append(normFact)

    audio = np.convolve(audio, audioFilt, mode='same')

    audio /= np.mean(rollingThresh)
    audio *= 0.8

    allAudio = np.concatenate((allAudio, audio))


# from scipy.io.wavfile import write
# allAudio *= 2**15 - 1
# allAudio = allAudio.astype(np.int16)
# write("./logs/amTest.wav", 44100, allAudio.astype(np.int16))


print("MAX:  ", np.max(allAudio))
print("MEAN: ", np.mean(allAudio))

print(allAudio.dtype)

# plt.plot(allAudio)
# plt.show()

p = pa.PyAudio()

# def get_next_chunk(*args, **kwargs):
#     return allAudio
# audioStream = p.open(format=pa.paFloat32,
#                     channels=1,
#                     rate=44100,
#                     output=True,
#                     frames_per_buffer=int(allAudio.size),
#                     stream_callback=get_next_chunk
#                 )

# audioStream.start_stream()

# Open stream with correct settings
stream = p.open(format=pa.paFloat32,
                channels=1,
                rate=44100,
                output=True,
                output_device_index=0,
                frames_per_buffer=int(allAudio.size),
                )

print(f"{allAudio.size} Samples ({allAudio.size / 44100} s) to play")

print("Playing")
stream.write(allAudio.astype(np.float32).tobytes())
print("DONE")

stream.stop_stream()
stream.close()
p.terminate()
