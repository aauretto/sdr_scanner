from matplotlib import pyplot as plt

from rtlsdr import RtlSdr
import scipy.signal as sp

# Purpose: A threadsafe spot for settings regarding how we rx / process data
#          is handled 
class RadioSettingsTracker:

    def __init__(self, sdr, cf, spb, filtLock):
        self.sdr = sdr

        self.cfStepArr  = [1e6, 1e5, 25e3]
        self.currCfStep = 0
        self.cf         = cf

        # configure device
        self.sdr.sample_rate = 1e6      # Hz
        self.sdr.center_freq = cf
        self.sdr.freq_correction = 60   # PPM
        self.sdr.gain = 'auto'
        print("gain = ", sdr.get_gain())
        print("bw = ", sdr.get_bandwidth())
        print("cf = ", self.get_cf())

        # 51 tap 1D low-pass FIR filter that keeps ~150kHZ at 1MHz sample rate
        self.filter = sp.firwin(51, 150000/2, fs=1000000)

        self.filtLock = filtLock

        self.spb = spb

        self.stopSignal = False

    def get_spb(self):
        return self.spb

    def get_sdr(self):
        return self.sdr

    def call_stop(self):
        self.stopSignal = True

    def stop_called(self):
        return self.stopSignal

    def cycle_cf_step(self):
        self.currCfStep = (self.currCfStep + 1) % 3

    def get_cf_step(self):
        return self.cfStepArr[self.currCfStep]
    
    def get_cf(self):
        return self.cf, self.sdr.get_center_freq()
    
    def nudge_cf(self, dir):
        self.cf += self.cfStepArr[self.currCfStep] * dir
        self.sdr.set_center_freq(self.cf)

    def set_cf(self, newCF):
        self.sdr.set_center_freq(newCF)
        self.cf = newCF

    # Purpose: Set the filter we use when sampling
    # Params:  taps     -- Number of taps the filter has
    #          bw       -- The bandwidth that the filter accepts
    #          samprate -- the sample rate of the signal we will filter
    def set_filter(self, taps, bw, samprate):
        with self.filtLock:
            self.filter = sp.firwin(taps, bw/2, fs=samprate)

    def get_filter(self):
        with self.filtLock:
            return self.filter
        
    
    
def task(id, settings, numtaps):
    
    settings.set_filter(taps=numtaps, bw=150000, samprate=1000000)
    print(f"ID {id}: set filter:({numtaps} taps)")
    print(f"ID {id}: filter len: {len(settings.get_filter())}")

# sdr = RtlSdr()

# # initialize some locks we will use
# cfLock = threading.Lock()
# filterLock = threading.Lock()
# myDude = RadioSettingsTracker(sdr, filterLock, cfLock)

# for i in range(4):
#     threading.Thread(target=task, args=(i, myDude, 51 + 10 * i)).start()


# print(myDude.get_cf_step())
# myDude.cycle_cf_step()
# print(myDude.get_cf_step())
# myDude.cycle_cf_step()
# print(myDude.get_cf_step())
# myDude.cycle_cf_step()
# print(myDude.get_cf_step())