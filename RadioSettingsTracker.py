from rtlsdr import RtlSdr
import scipy.signal as sp
import numpy as np


# Functions that define how we decode data.
def decode_fm(iqData):
    # obtain the frequency at each point in time 
    return np.diff(np.angle(iqData))

def decode_am(iqData):
    # obtain mag at each point in time 
    return np.abs(iqData)

# Purpose: A threadsafe spot for settings regarding how we rx / process data
#          is handled 
class RadioSettingsTracker:

    def __init__(self, sdr, cf, spb, filtLock, demodLock):
        self.sdr = sdr

        self.cfStepArr  = [5e3, 25e3, 1e5, 1e6, 10e6]
        self.currCfStep = 2
        self.cf         = cf

        # configure device
        self.sdr.sample_rate = 1e6      # Hz
        self.sdr.center_freq = cf
        self.sdr.freq_correction = 60   # PPM
        self.sdr.gain = 'auto'
        print("gain = ", sdr.get_gain())
        print("bw = ", sdr.get_bandwidth())
        print("cf = ", self.get_cf())

        self.filtLock = filtLock
        self.demodLock = demodLock

        # Default Filters
        self.filtFMRadio = sp.firwin(51, 150e3/2, fs=self.sdr.sample_rate)
        self.filtAMRadio = sp.firwin(51, 10e3/2, fs=self.sdr.sample_rate)
        self.filtAIRCOM  = sp.firwin(51, 20e3/2, fs=self.sdr.sample_rate)

        # Demod order [fmrad, amrad, aircom, auto]
        self.currDemod = 3

        self.bw = 150e3
        self.bwStepArr  = [1e3, 5e3, 25e3, 50e3]
        self.currBwStep = 0
        
        self.ordemodFunc = False
        self.demodFunc   = lambda x : np.abs(x)
        self.set_demod_profile()

        self.doHammer = True

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
    
    def nudge_cf_step(self, dir):
        newCfStep = self.currCfStep + dir
        if (0 <= newCfStep and newCfStep < len(self.cfStepArr)):
            self.currCfStep = newCfStep

    def get_cf_step(self):
        return self.cfStepArr[self.currCfStep]
    
    def get_cf(self):
        return self.cf, self.sdr.get_center_freq()
    
    def nudge_cf(self, dir):
        self.cf += self.cfStepArr[self.currCfStep] * dir
        self.sdr.set_center_freq(self.cf)
        if not self.ordemodFunc:
            self.set_demod_profile()

    def set_cf(self, newCF):
        self.sdr.set_center_freq(newCF)
        self.cf = newCF
        if not self.ordemodFunc:
            self.set_demod_profile()

    def get_samp_rate(self):
        return self.sdr.sample_rate

    # Purpose: Set the filter we use when sampling
    # Params:  taps     -- Number of taps the filter has
    #          bw       -- The bandwidth that the filter accepts
    #          samprate -- the sample rate of the signal we will filter
    def set_filter(self, taps, bw, samprate):
        with self.filtLock:
            self.filter = sp.firwin(taps, bw/2, fs=samprate)

    def set_filter_from_KB(self, filt):
        with self.filtLock:
            self.filter = filter

    def get_filter(self):
        with self.filtLock:
            return self.filter
    
    # Automatic Decoding Setups
    def set_demod_profile(self, override = None):
        if override is not None:
            self.ordemodFunc = True
            self.demodFunc = override
            return

        if not self.ordemodFunc:
            freq = self.cf
            # FM RADIO
            if (88.0e6 <= freq and freq < 108.0e6):
                self.demodFunc = decode_fm
                self.bw = 150e3
                with self.filtLock:
                    self.filter = self.filtFMRadio
            # AIRCOM/NAV
            elif (108.0e6 <= freq and freq <= 137.0e6):
                self.demodFunc = decode_am
                self.bw = 25e3
                with self.filtLock:
                    self.filter = self.filtFMRadio      
            # AM RADIO
            elif (540.0e5 <= freq and freq <= 1700.0e5):
                self.demodFunc = decode_am
                self.bw = 10e3
                with self.filtLock:
                    self.filter = self.filtFMRadio
            
            else: # Band not in KB, Use AM
                self.demodFunc = lambda x : np.abs(x)

        print(f"Set Demod to: {self.demodFunc}")

    def reset_demod_profile(self):
        self.ordemodFunc = False
        self.set_demod_profile()

    def get_demod_func(self):
        with self.demodLock:
            return self.demodFunc

    def get_bw(self):
        return self.bw
    
    def get_bw_step(self):
        return self.bwStepArr[self.currBwStep]
        
    def nudge_bw_step(self, dir):
        newBwStep = self.currBwStep + dir
        if (0 <= newBwStep and newBwStep < len(self.bwStepArr)):
            self.currBwStep = newBwStep

    def nudge_bw(self, dir):
        newBw = self.bw + self.bwStepArr[self.currBwStep] * dir 
        if (0 < newBw) and (newBw < 1e6):
            self.bw = newBw
            self.set_filter(51, newBw, 1e6)        

    def cycle_bw_step(self):
        self.currBwStep = (self.currBwStep + 1) % len(self.bwStepArr)   
