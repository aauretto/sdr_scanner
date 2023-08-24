import numpy as np
from matplotlib import pyplot as plt
import asyncio
from rtlsdr import RtlSdr
from RadioSettingsTracker import *
from streamaudio import *
import sys
import os
import time
import threading

def launch_radio_rx(settings):
    asyncio.run(radio_handler(settings))


def main():

    filtLock = threading.Lock()

    sdr = RtlSdr()
    
    settings = RadioSettingsTracker(sdr, 106.3e6, 2**18, filtLock)

    threading.Thread(target=launch_radio_rx, args=([settings])).start()

    # main loop for checking sensors goes here
    while (not settings.stop_called()):

        print(f"Current CF is: {settings.get_cf()}")
        time.sleep(10)
        settings.set_cf(88.3e6)
        print(f"Current CF is: {settings.get_cf()}")


    # done - close streams
    settings.get_sdr().close()


# makes us run main when this file is run
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(130)
        except SystemExit:
            os._exit(130)