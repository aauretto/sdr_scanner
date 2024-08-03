from rtlsdr import RtlSdr
import scipy.signal as sp
import numpy as np
import collections

# Functions that define how we decode data.
# Should always return audio in range [-1,1]
def decode_fm(iqData, settings):

    # obtain the frequency at each point in time
    freq = np.diff(np.angle(iqData))

    # Correct for jumping over the -X axis
    # always take the smaller step in phase between points
    # otherwise we introduce large jumps in freq where there
    # are none.
    freq[freq < -1 * np.pi] += 2 * np.pi
    freq[freq > np.pi] -= 2 * np.pi
    
    return freq / np.pi

def decode_am(iqData, settings):
    # obtain mag at each point in time 
    amp = np.abs(iqData)
    dB  = 10 * np.log10(amp ** 2)

    # print(f"AMP = {np.mean(amp)}")
    # print(f"PWR = {np.mean(amp) ** 2}")
    settings.lastDBMean = np.mean(dB)
    if settings.doSquelch:
        settings.lastDBMax  = np.max(dB)
        settings.lastDBMin  = np.min(dB)
        if (np.mean(dB) < settings.squelch):
            return (np.zeros(amp.size, dtype=np.float32))
        # amp[dB <= settings.squelch] = 0 
        # print(np.mean(dB))
    
    normFact = np.max(amp)
    if (normFact):
        return amp / normFact
    return amp 

    


# Purpose: A threadsafe spot for settings regarding how we rx / process data
#          is handled 
class RadioSettingsTracker:

    def __init__(self, sdr, cf, spb, filtLock, demodLock):
        self.sdr = sdr

        self.cfStepCol = 4
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
        self.bwStepCol = 2

        self.ordemodFunc = False
        self.demodFunc   = lambda x : np.abs(x)
        self.set_demod_profile()

        self.doSquelch = False
        self.squelch  = -25.0  #dB
        self.squelchIdx = 2
        self.curDb      = 0 

        self.volMode = 1
        self.volModes = ["OFF","AVG","MAX"]
        self.vol  = 0.8
        self.volStepArr = [0.01, 0.05, 0.1, 0.25]
        self.volIdx = 1
        # Circular buffer we use for automatic normalization of signal to about
        # 0.8 of max
        self.rollingThresh = collections.deque(maxlen=100)
        self.rollingThreshFuncs = [None, np.mean, np.max]

        self.spb = spb

        self.stopSignal = False

        self.lastDBMean = collections.deque(maxlen=10)
        self.lastDBMax  = collections.deque(maxlen=10)
        self.lastDBMin  = collections.deque(maxlen=10)

        self.lastDBMin.append(0)
        self.lastDBMax.append(0)
        self.lastDBMean.append(0)

        self.audioFilt = sp.firwin(38, 10e3, fs=44100, window=("kaiser", 4))


    def get_spb(self):
        return self.spb

    def get_sdr(self):
        return self.sdr

    def call_stop(self):
        self.stopSignal = True

    def stop_called(self):
        return self.stopSignal

    def get_samp_rate(self):
        return self.sdr.sample_rate

    def nudge_cf_step(self, dir):
        newCfStep = self.cfStepCol + dir
        if (0 <= newCfStep and newCfStep < 8):
            self.cfStepCol = newCfStep
    
    def nudge_cf(self, dir):
        newCf = self.cf +  np.round(10**(self.cfStepCol + 2)) * dir
        if newCf < 24e6:
            newCf = 24e6
        elif newCf > 1766e6:
            newCf = 1766e6

        self.cf = newCf
        self.sdr.set_center_freq(self.cf)
        if not self.ordemodFunc:
            self.set_demod_profile()

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
        
    def nudge_bw_step(self, dir):
        newBwStep = self.bwStepCol + dir
        if (0 <= newBwStep and newBwStep < 6):
            self.bwStepCol = newBwStep
        
    def nudge_bw(self, dir):
        newBw = self.bw +  np.round(10**(self.bwStepCol)) * dir
        if newBw <= 1e3:
            newBw = 1e3
        elif newBw >= 999e3:
            newBw = 999e3

        self.bw = newBw
        self.set_filter(51, newBw, self.sdr.sample_rate)

    def nudge_squelch(self, dir):
        newSquelch = self.squelch + 10**(self.squelchIdx - 2) * dir
        if (newSquelch < -99.9):
            newSquelch = -99.9
        elif (newSquelch > 99.9):
            newSquelch = 99.9
        self.squelch = newSquelch

    def nudge_squelch_step(self, dir):
        newSquelchIdx = self.squelchIdx + dir * 1
        if (0 <= newSquelchIdx and newSquelchIdx < 4):
            self.squelchIdx = newSquelchIdx

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