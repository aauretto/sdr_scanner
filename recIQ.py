from rtlsdr import RtlSdr
import numpy as np

# Function to normalize complex numbers and pack them as int16 values
def pack_complex_numbers(complex_array):
    print("packing")
    max_magnitude = np.max(np.abs(complex_array))
    # Normalize the magnitude of complex numbers to [0, 1]
    normalized_complex_array = complex_array / max_magnitude
    
    # Pack as int16 values
    normalized_complex_array *= 32767
    rpt = np.real(normalized_complex_array)
    ipt = np.imag(normalized_complex_array)
    dovetailed_arr = []
    i = 0
    while i < len (normalized_complex_array):
        dovetailed_arr.append(rpt[i])
        dovetailed_arr.append(ipt[i])
        i += 1

    packed_array = (np.array(dovetailed_arr)).astype(np.int16)
    return packed_array

cf = 133.2 * 1e6

sdr = RtlSdr()

sdr.sample_rate = 1e6 
sdr.center_freq = cf

sdr.freq_correction = 60 
sdr.gain = 'auto'

print("SDR center at: ", sdr.get_center_freq() / 1e6, " MHz")
print("SDR gain  at: ", sdr.get_gain(), " Db")

packed_array = pack_complex_numbers(np.array(sdr.read_samples(2**20)))

print("writing file")

with open("nash_twr.bin", "wb") as file:
    packed_array.tofile(file)
