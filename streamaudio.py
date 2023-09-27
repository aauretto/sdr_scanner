import numpy as np
import pyaudio as pa
import asyncio
from rtlsdr import RtlSdr
import time

def decimate(sig, to_rate, from_rate):

    # total length of time the input takes
    buffTime = len(sig) / from_rate
    # timestamps of the samples we want to write to output
    newTimes = np.linspace(0, buffTime, int(to_rate * buffTime), False)
    # preallocate output array
    newSig = np.empty(shape=(int(buffTime * to_rate)), dtype=np.float32)

    # Iterate over signal. Only write sample closest to each timestamp in newTimes.
    idx = 0
    for t in newTimes:
        fromIdx = round(t * from_rate)
        [idx] = sig[fromIdx]

    return newSig


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

async def IQ_to_audio(samples, filter): 
    # apply filter to isolate just fm channel we want
    
    IQin = np.convolve(samples, filter, mode='same')

    
    # obtain the frequency at each point in time 
    # (this is our decoded audio)
    freqBuff = np.diff(np.arctan(IQin.imag / IQin.real))

    
    
    # freqBuff *= (1/max(abs(freqBuff)))
    

    # decimation step so we can listen at correct sample rate
    # we will also hammer down spikes that will add unneeded noise to our waveform
    audio = decimate_and_hammer(freqBuff, 44100, 1e6, 0.9) 
    
    return audio

async def audioStreaming(settings):

    sdr = settings.get_sdr()
    
    async for samples in sdr.stream(num_samples_or_bytes=settings.get_spb(), format='samples'):
        if (settings.stop_called()):
            print("Shutting down async stream")
            await sdr.stop()
            break
        
        yield await IQ_to_audio(samples, settings.get_filter())
        
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
               print("filling queue")
               await asyncio.sleep(3)
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

    print(f"latency {audioStream.get_input_latency()}", end = '\n\n\n')



    async for chunk in audioStreaming(settings):  
        if (settings.stop_called()):
            break
        queue.put_nowait(chunk.astype(np.float32))
        
    audioStream.close() 
    loop.close() 
    p.terminate()
