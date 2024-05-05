from rtlsdr import RtlSdr
import scipy.signal as sp

# Purpose: A threadsafe spot for settings regarding how we rx / process data
#          is handled 
class RadioSettingsTracker:

    def __init__(self, sdr, cf, spb, filtLock):
        self.sdr = sdr

        self.cfStepArr  = [10e6, 1e6, 1e5, 25e3, 5e3]
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
        self.filter = sp.firwin(51, 150e3/2, fs=1000000)
        self.bw = 150e3
        self.bwStepArr  = [50e3, 25e3, 5e3, 1e3]
        self.currBwStep = 0

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
        self.currCfStep = (self.currCfStep + 1) % len(self.cfStepArr)

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
            print("filter changed")

    def get_filter(self):
        with self.filtLock:
            return self.filter
    
    def get_bw(self):
        return self.bw
    
    def get_bw_step(self):
        return self.bwStepArr[self.currBwStep]
        
    def nudge_bw(self, dir):
        self.bw += self.bwStepArr[self.currBwStep] * dir
        self.set_filter(51, self.bw, 1e6)        

    def cycle_bw_step(self):
        self.currBwStep = (self.currBwStep + 1) % len(self.bwStepArr)   
