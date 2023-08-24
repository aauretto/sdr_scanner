import numpy as np
import pyaudio as pa
from matplotlib import pyplot as plt
import asyncio
from rtlsdr import RtlSdr

def decimate_and_hammer(sig, to_rate, from_rate, cap):

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
def get_freq_plot(IQin):
        # get phase at each point in signal
        phaseBuff = np.arctan(IQin.imag / IQin.real)

        # take deriv for frequency
        freqBuff = np.diff(phaseBuff)

        # normalize
        freqBuff *= (1/max(abs(freqBuff)))

        return freqBuff

async def IQ_to_audio(samples, filter): 
    # apply filter to isolate just fm channel we want
    IQin = np.convolve(samples, filter, mode='same')

    # obtain the frequency at each point in time 
    # (this is our decoded audio)
    freqBuff = get_freq_plot(IQin)

    # decimation step so we can listen at correct sample rate
    # we will also hammer down spikes that will add unneeded noise to our waveform
    audio = decimate_and_hammer(freqBuff, 96000, 1e6, 0.4)

    return audio

async def audioStreaming(settings):

    sdr = settings.get_sdr()
    
    async for samples in sdr.stream(num_samples_or_bytes=settings.get_spb(), format='samples'):
        if (settings.stop_called()):
            print("Shutting down async stream")
            await sdr.stop()
            break
        
        getWfm = asyncio.create_task(IQ_to_audio(samples, settings.get_filter()))
        yield await getWfm
        
global queue
queue = asyncio.Queue()

async def radio_handler(settings):
    p = pa.PyAudio()
    global queue
    
    loop = asyncio.get_event_loop()

    def get_next_chunk(*args, **kwargs):

        # dummy coroutine that lets us get the next value in the queue as a future
        async def extract_next(*args, **kwargs):
            global queue
            print(f"queuesize {queue.qsize()}")
            while(queue.qsize() < 1):
               print("sleeping")
               await asyncio.sleep(0.1)
            chunk = await queue.get()
            return chunk

        nonlocal loop
        fut = asyncio.run_coroutine_threadsafe(extract_next(), loop)
        res = np.zeros(shape=(1, settings.get_spb()), dtype=np.float32)
        while (not fut.done()):
            res = fut.result()

        return (res.tobytes() , pa.paContinue)

    audioStream = p.open(format=pa.paFloat32,
                         channels=1,
                         rate=96000,
                         output=True,
                         frames_per_buffer=int(settings.get_spb()/1000000 * 96000),
                         stream_callback=get_next_chunk
                        )

    audioStream.start_stream()

    async for chunk in audioStreaming(settings):  
        if (settings.stop_called()):
            break
        queue.put_nowait(chunk.astype(np.float32))
        
    audioStream.close() 
    loop.close() 
    p.terminate()