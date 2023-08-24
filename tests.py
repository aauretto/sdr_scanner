import numpy as np
import matplotlib.pyplot as plt
from rtlsdr import RtlSdr
import asyncio
import struct

def decimate_and_hammer(sig, to_rate, from_rate, cap,  ):

    buffer_time = len(sig) / from_rate

    print(f"Signal length {buffer_time}s")

    new_stamps = np.linspace(0, buffer_time, int(to_rate * buffer_time), False)

    print(f"Set {len(new_stamps)} timestamps")

    buff_out = np.empty(shape=(int(buffer_time * to_rate)), dtype=np.float32)

    print(f"made buff_out arr of size {len(buff_out)}")

    idx = 0
    for t in new_stamps:
        print(f"time: {t} = idx:{idx}") 
        fromIdx = round(t * from_rate)
        while ((fromIdx > -1 * len(sig)) and abs(sig[fromIdx]) > cap):
            fromIdx -= 1
        if (fromIdx == -1 * len(sig)):
            buff_out[idx] = cap * np.sign(sig[fromIdx])
        else:
            buff_out[idx] = sig[fromIdx]

        print(f"set buffout[{idx}] to {sig[fromIdx]}")
        idx += 1

    print("after decimation")
    print(buff_out)
    return buff_out

freqBuff = np.array([0.1, 0.2, 0.3, 0.2, 0.1, 0.2, 0.3, 0.2, 0.1, 0.2, 0.1, 0.2, 0.1, 0.2])
# x1 = np.linspace(0, 6,1000)
# freqBuff = np.ones(1000)
# freqBuff *= -1


# cap = 0.40
# fromrate = 20
# torate   = 10
# newArr = decimate_and_hammer(freqBuff, 10, 20, cap)

# ax1 = plt.subplot(2,1,1)
# ax1.plot(freqBuff, '.-')

# ax2 = plt.subplot(2,1,2, sharex=ax1, sharey=ax1)

# x2 = np.linspace(0, len(freqBuff), len(newArr)).astype(np.int_)
# ax2.plot(x2, newArr, '.-')

# plt.show() 

sdr = RtlSdr()

# configure device
sdr.sample_rate = 1e6  # Hz
sdr.center_freq = 88.3e6     # Hz
sdr.freq_correction = 60   # PPM
sdr.gain = 'auto'
sdr.bandwidth = 1e6
print("bw = ", sdr.get_bandwidth())
print("cf = ", sdr.get_center_freq())

nsamps = 2**20
print(nsamps)

sig = sdr.read_samples(nsamps)

sig = np.append(sig, sdr.read_samples(nsamps))
sig = np.append(sig, sdr.read_samples(nsamps))
sig = np.append(sig, sdr.read_samples(nsamps))
sig = np.append(sig, sdr.read_samples(nsamps))
sig = np.append(sig, sdr.read_samples(nsamps))
sig = np.append(sig, sdr.read_samples(nsamps))
sig = np.append(sig, sdr.read_samples(nsamps))
sig = np.append(sig, sdr.read_samples(nsamps))
sig = np.append(sig, sdr.read_samples(nsamps))
sig = np.append(sig, sdr.read_samples(nsamps))
sig = np.append(sig, sdr.read_samples(nsamps))
sig = np.append(sig, sdr.read_samples(nsamps))

file = open("testIQ.bin", 'wb')

sig /= max(abs(sig))

sig *= 2**15 - 1

print(len(sig))

for samp in sig:
    file.write(struct.pack('h', int(samp.real)))
    file.write(struct.pack('h', int(samp.imag)))

file.close()