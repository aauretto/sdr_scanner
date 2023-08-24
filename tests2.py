# SuperFastPython.com
# example of an asynchronous iterator with async for loop
import asyncio
 
# define an asynchronous iterator
class AsyncIterator():
    # constructor, define some state
    def __init__(self):
        self.counter = 0
 
    # create an instance of the iterator
    def __aiter__(self):
        return self
 
    # return the next awaitable
    async def __anext__(self):
        # check for no further items
        if self.counter >= 10:
            raise StopAsyncIteration
        # increment the counter
        self.counter += 1
        # simulate work
        await asyncio.sleep(1)
        # return the counter value
        return self.counter0
 
# main coroutine
async def main():
    # loop over async iterator with async for loop
    async for item in AsyncIterator():
        print(item)
 
# execute the asyncio program
asyncio.run(main())


# (0, 'Microsoft Sound Mapper - Input', 2)
# (1, 'Microphone Array (IntelÂ® Smart ', 6)
# (2, 'Stereo Mix (Realtek(R) Audio)', 2)
# (3, 'Microphone (EpocCam Camera Audi', 2)
# (4, 'Microsoft Sound Mapper - Output', 0)
# (5, 'Speakers (Realtek(R) Audio)', 0)
# (6, 'Primary Sound Capture Driver', 2)
# (7, 'Microphone Array (IntelÂ® Smart Sound Technology for Digital Microphones)', 6)
# (8, 'Stereo Mix (Realtek(R) Audio)', 2)
# (9, 'Microphone (EpocCam Camera Audio)', 2)
# (10, 'Primary Sound Driver', 0)
# (11, 'Speakers (Realtek(R) Audio)', 0)
# (12, 'Speakers (Realtek(R) Audio)', 0)
# (13, 'Stereo Mix (Realtek(R) Audio)', 2)
# (14, 'Microphone Array (IntelÂ® Smart Sound Technology for Digital Microphones)', 4)
# (15, 'Microphone (EpocCam Camera Audio)', 2)
# (16, 'MIDI (EpocCam Audio)', 2)
# (17, 'Output (EpocCam Audio)', 0)
# (18, 'Microphone (Realtek HD Audio Mic input)', 2)
# (19, 'Stereo Mix (Realtek HD Audio Stereo input)', 2)
# (20, 'Speakers 1 (Realtek HD Audio output with SST)', 0)
# (21, 'Speakers 2 (Realtek HD Audio output with SST)', 0)
# (22, 'PC Speaker (Realtek HD Audio output with SST)', 2)
# (23, 'Headphones 1 (Realtek HD Audio 2nd output with SST)', 0)
# (24, 'Headphones 2 (Realtek HD Audio 2nd output with SST)', 0)
# (25, 'PC Speaker (Realtek HD Audio 2nd output with SST)', 2)
# (26, 'Headphones ()', 0)
# (27, 'Speakers ()', 0)
# (28, 'Microphone Array 1 (IntelÂ® Smart Sound Technology DMIC Microphone)', 4)
# (29, 'Microphone Array 2 (IntelÂ® Smart Sound Technology DMIC Microphone)', 4)
# (30, 'Microphone Array 3 (IntelÂ® Smart Sound Technology DMIC Microphone)', 6)
# (31, 'Microphone Array 4 (IntelÂ® Smart Sound Technology DMIC Microphone)', 6)