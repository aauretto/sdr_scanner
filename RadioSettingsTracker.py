from rtlsdr import RtlSdr
import scipy.signal as sp
import numpy as np
import collections

# Functions that define how we decode data.
# Should always return audio in range [-1,1]
def decode_fm(iqData):
    # obtain the frequency at each point in time
    freq = np.diff(np.angle(iqData))
    
    # Correct for jumping over the -X axis
    # always take the smaller step in phase between points
    # otherwise we introduce large jumps in freq where there
    # are none.
    freq[freq < -1 * np.pi] += 2 * np.pi
    freq[freq > np.pi] -= 2 * np.pi
    
    return freq / np.pi

def decode_am(iqData):
    # obtain mag at each point in time 
    raw = np.abs(iqData)
    AMP = np.mean(raw)
    PWR = AMP ** 2
    dB  = 10 * np.log10(PWR)
    print(f"AMP = {np.mean(raw)}")
    print(f"PWR = {np.mean(raw) ** 2}")
    print(f"dB  = {10 * np.log10(np.mean(raw) ** 2)}")

    return raw / raw.max()


# Purpose: A threadsafe spot for settings regarding how we rx / process data
#          is handled 
class RadioSettingsTracker:

    def __init__(self, sdr, cf, spb, filtLock, demodLock):
        self.sdr = sdr

        self.cfStepArr  = [0.332e3, 1e3, 5e3, 25e3, 1e5, 1e6, 10e6]
        self.currCfStep = 2
        self.cf         = cf

        # configure device
        self.sdr.sample_rate = 1e6      # Hz
        self.sdr.center_freq = cf
        self.sdr.freq_correction = 60   # PPM
        self.sdr.gain = 'auto'

        self.filtLock = filtLock
        self.demodLock = demodLock

        # Default Filters
        self.filtFMRadio   = sp.firwin(51, 150e3/2, fs=self.sdr.sample_rate)
        self.filtAIRCOM    = sp.firwin(51, 20e3/2, fs=self.sdr.sample_rate)
        self.filtWholeBand = np.ones(51)

        # Demod order [fmrad, aircom, auto]
        self.currDemod = 2

        self.bw = 150e3
        self.bwStepArr  = [1e3, 5e3, 25e3, 50e3]
        self.currBwStep = 0

        self.ordemodFunc = False
        self.demodFunc   = lambda x : np.abs(x)
        self.set_demod_profile()

        # Audio postprocessing Settings
        self.doHammer = False
        self.hammer = 0.9
        self.hammerStepArr = [0.01, 0.05, 0.1, 0.25]
        self.hammerIdx = 1

        self.doSquelch = False
        self.squelch  = 0
        self.squelchStepArr = [0.01, 0.05, 0.1, 0.25]
        self.squelchIdx = 1

        self.doVol = True
        self.vol  = 0.8
        self.volStepArr = [0.01, 0.05, 0.1, 0.25]
        self.volIdx = 1

        self.spb = spb

        self.stopSignal = False

        # Circular buffer we use for automatic normalization of signal to about
        # 0.8 of max
        self.rollingThresh = collections.deque(maxlen=40)


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
            self.filter = filt

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
                self.bw = 20e3
                with self.filtLock:
                    self.filter = self.filtFMRadio      
            
            else: # Band not in Known Bands, Use AM on whole spectrum
                self.demodFunc = decode_am
                with self.filtLock:
                    self.filter = self.filtWholeBand

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
            self.set_filter(51, newBw, self.sdr.sample_rate)        

    def cycle_bw_step(self):
        self.currBwStep = (self.currBwStep + 1) % len(self.bwStepArr)   

    def nudge_squelch(self, dir):
        newSquelch = self.squelch + self.squelchStepArr[self.squelchIdx] * dir
        if (newSquelch < -1):
            newSquelch = -1
        elif (newSquelch > 1):
            newSquelch = 1
        self.squelch = newSquelch

    def nudge_squelch_step(self, dir):
        newSquelchIdx = self.squelchIdx + dir
        if (0 <= newSquelchIdx and newSquelchIdx < len(self.squelchStepArr)):
            self.squelchIdx = newSquelchIdx

    def nudge_hammer(self, dir):
        newHammer = self.hammer + self.hammerStepArr[self.hammerIdx] * dir
        if (newHammer < -1):
            newHammer = -1
        elif (newHammer > 1):
            newHammer = 1
        self.hammer = newHammer

    def nudge_hammer_step(self, dir):
        newHammerIdx = self.hammerIdx + dir
        if (0 <= newHammerIdx and newHammerIdx < len(self.hammerStepArr)):
            self.hammerIdx = newHammerIdx

    def nudge_vol(self, dir):
        newVol = self.vol + self.volStepArr[self.volIdx] * dir
        if (newVol < 0):
            newVol = 0
        elif (newVol > 1):
            newVol = 1        
        self.vol = newVol
    
    def nudge_vol_step(self, dir):
        newVolIdx = self.volIdx + dir
        if (0 <= newVolIdx and newVolIdx < len(self.volStepArr)):
            self.volIdx = newVolIdx