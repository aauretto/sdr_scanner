import numpy as np
import pyaudio as pa
import asyncio
from rtlsdr import RtlSdr
import time

# Purpose: Clean up audio we get from demodulation step
def hammer(sig, cap):
    # preallocate output array
    newSig = np.empty(shape=sig.shape, dtype=np.float32)

    # Iterate over signal.
    # If we encounter a sample that has greater magnitude that cap, we find the
    # most recent sample lower than cap and set it to that value instead.
    # If we cannot find a sample lower than cap then we set this sample to cap.
    idx = 0
    for s in sig:
        runnerIdx = idx
        while ((runnerIdx > -1 * len(sig)) and abs(sig[runnerIdx]) > cap):
            runnerIdx -= 1
        if (runnerIdx == -1 * len(sig)):
            print("Hammer got greedy")
            newSig[idx] = cap * np.sign(sig[runnerIdx])
        else:
            newSig[idx] = sig[runnerIdx]
        idx += 1
    return newSig

# Purpose: Decimate signal sig down to rate toRate
# Notes:   toRate and fromRate need not be integers 
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

async def IQ_to_audio(samples, settings): 
    # apply filter to isolate channel we want
    filtIQ = np.convolve(samples, settings.get_filter(), mode='same')
    
    # Decode based where we are tuned to
    decodedChunk = settings.get_demod_func()(filtIQ)

    # Decimation step so we can listen at correct sample rate
    audio = nonint_decimate(decodedChunk, 44100, settings.get_samp_rate()) 

    settings.rollingThresh.append(audio.max())
    audio /= 5/4 * np.mean(settings.rollingThresh)

    # Hammer down spikes in recovered waveform
    # Makes up for lower recovery rates by correcting values above cap
    # to be near the values around them
    if settings.doHammer:
        audio = hammer(audio, settings.hammerCap)
    
    # Squelch
    if settings.doSquelch:
        audio[audio < settings.squelch] = 0

    return audio

async def audioStreaming(settings):

    sdr = settings.get_sdr()
    
    async for samples in sdr.stream(num_samples_or_bytes=settings.get_spb(), format='samples'):
        if (settings.stop_called()):
            print("Shutting down async stream")
            await sdr.stop()
            break
        yield await IQ_to_audio(samples, settings)
        
global queue
queue = asyncio.Queue()
global lasttime
lasttime = 0

async def radio_handler(settings):
    p = pa.PyAudio()
    global queue
    
    loop = asyncio.get_event_loop()

    def get_next_chunk(*args, **kwargs):

        # dummy coroutine that lets us get the next value in the queue as a future
        async def extract_next(*args, **kwargs):
            global queue
            while(queue.qsize() < 1):
               await asyncio.sleep(1)
            chunk = queue.get_nowait()
            return chunk

        nonlocal loop
        fut = asyncio.run_coroutine_threadsafe(extract_next(), loop)
        res = np.zeros(shape=(1, settings.get_spb()), dtype=np.float32)
        while (not fut.done()):
            res = fut.result()

        return (res.tobytes() , pa.paContinue)

    audioStream = p.open(format=pa.paFloat32,
                         channels=1,
                         rate=44100,
                         output=True,
                         frames_per_buffer=int(settings.get_spb()/1000000 * 44100),
                         stream_callback=get_next_chunk
                        )

    audioStream.start_stream()


    async for chunk in audioStreaming(settings):  
        if (settings.stop_called()):
            break
        queue.put_nowait(chunk.astype(np.float32))
        # print("queue len: ", queue.qsize())
        
    audioStream.close() 
    loop.close() 
    p.terminate()
