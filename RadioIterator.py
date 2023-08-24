import asyncio
import numpy as np


# define an asynchronous iterator
class RadioIterator():

    # constructor, define some state
    def __init__(self, sdr, filterIn, chunkSize):
        self.stopCalled = False
        self.sampsRxd   = 0
        self.sdr        = sdr
        self.chunkSize  = chunkSize
        self.filter     = filterIn
        self.IQstream   = sdr.stream(num_samples_or_bytes=chunkSize, format='samples')
 
    # create an instance of the iterator
    def __aiter__(self):
        return self
 
    # return the next awaitable
    async def __anext__(self):
        if (self.stopCalled):

        async for chunk in self.IQstream:
            if (sampsRxd ):
                await self.sdr.cancel_read_async()
                break
            yield await self.IQ_to_audio(chunk)

        await self.sdr.stop()

    
    def change_filter(self, newFilter):
        self.filter = newFilter

    def decimate_and_hammer(self, sig, to_rate, from_rate, cap):

        # total length of time the input takes
        buffTime = len(sig) / from_rate
        # timestamps of the samples we want to write to output
        newTimes = np.linspace(0, buffTime, int(to_rate * buffTime), False)
        # preallocate output array
        newSig = np.empty(shape=(int(buffTime * to_rate)), dtype=np.float32)


        # Iterate over signal. Only write sample closest to each timestamp in newTimes.
        # If we encounter a sample that has greater magnitude that cap, we find the
        # most recent sample lower than cap and take that one instead.
        # If we cannot find a sample lower than cap then we set this sample to cap.
        idx = 0
        for t in newTimes:
            fromIdx = round(t * from_rate)
            while ((fromIdx > -1 * len(sig)) and abs(sig[fromIdx]) > cap):
                fromIdx -= 1
            if (fromIdx == -1 * len(sig)):
                newSig[idx] = cap * np.sign(sig[fromIdx])
            else:
                newSig[idx] = sig[fromIdx]
            idx += 1

        return newSig

    # get_freq_plot
    # Purpose: Obtain instantaneous frequency at each sample from a buffer of IQ data
    # Params:  IQin - a buffer of complex iq samples
    # Returns: A vector representing the frequency at each point in the input (indexed by samples)
    def get_freq_plot(self, IQin):
            # get phase at each point in signal
            phaseBuff = np.arctan(IQin.imag / IQin.real)

            # take deriv for frequency
            freqBuff = np.diff(phaseBuff)

            # normalize
            freqBuff *= (1/max(abs(freqBuff)))

            return freqBuff

    # converts some raw IQ data to an audio waveform at 96kHz
    async def IQ_to_audio(self, samples, filter): 
        print("starting Processing...", end="")
        # apply filter to isolate just fm channel we want
        IQin = np.convolve(samples, filter, mode='same')

        # obtain the frequency at each point in time 
        # (this is our decoded audio)
        freqBuff = self.get_freq_plot(IQin)

        # decimation step so we can listen at correct sample rate
        # we will also hammer down spikes that will add unneeded noise to our waveform
        audio = self.decimate_and_hammer(freqBuff, 96000, 1e6, 0.4)

        # # convert to 16-bit data
        # audio *= 32767 # / np.max(np.abs(audio))
        # audio = audio.astype(np.int16)

        print("done")
        return audio
