import numpy as np
import asyncio
from rtlsdr import RtlSdr
from RadioSettingsTracker import *
from streamaudio import *
from menu import *
import time
import threading
from RPi import GPIO
from rpi_lcd import LCD
import sys
import traceback

def launch_radio_rx(settings):
    asyncio.run(radio_handler(settings))

def main():

    filtLock = threading.Lock()
    demodLock = threading.Lock()

    sdr = RtlSdr()
    
    lcd = LCD()
    
    settings = RadioSettingsTracker(sdr, 124.9e6, 2**18, filtLock, demodLock)

    threading.Thread(target=launch_radio_rx, args=([settings])).start()

    clk = 17
    dt  = 18
    sw  = 27
    
    clk2 = 11
    dt2  = 9
    sw2  = 10
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(clk, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(dt,  GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(sw,  GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    
    GPIO.setup(clk2, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(dt2,  GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(sw2,  GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    lcd = LCD()

    LCDMenuItem()

    lcd.clear()
    # Init Menu
    # Max title width:         |>_______________|
    menu = [
            LCDMenuItem(title = "Freq Tune",      action = freq_tune_menu),
            LCDMenuItem(title = "Volume",         action = vol_menu),
            LCDMenuItem(title = "Demod Profile",  action = demod_menu),
            LCDMenuItem(title = "Set Bandwidth",  action = bw_menu),
            LCDMenuItem(title = "Set Squelch",    action = squelch_menu),
            LCDMenuItem(title = "Live dB vals",   action = disp_live_dB),
            ]

    currItem = 0
    nextItem = 1

    lastSWstate = GPIO.input(sw)
    turnDir = 0

    lcd.text(">"+menu[currItem].title, 1)
    lcd.text(" "+menu[nextItem].title, 2)
    print(settings.sdr.sample_rate)

    try:
        while True:
            time.sleep(0.001)
            swState  = GPIO.input(sw)
            clkState = GPIO.input(clk)
            dtState  = GPIO.input(dt)
            swState  = GPIO.input(sw)

            # Look for pushing in rotary encoder, activate fx on release
            if swState == 0 and lastSWstate != 0:
                        # Call curr item
                        menu[currItem].action(lcd, settings, clk, dt, sw, clk2, dt2, sw2)
                        lcd.text(">" + menu[currItem].title, 1)
                        lcd.text(" " + menu[nextItem].title, 2)
                        lastSWstate = 0
            elif(swState == 1 and lastSWstate == 0):
                lastSWstate = 1
                    
            # Check for turning rotary encoder
            if (clkState == 1 and dtState == 1):
                if(turnDir):
                    currItem = (currItem + turnDir) % len(menu)
                    nextItem = (nextItem + turnDir) % len(menu)
                    
                    lcd.text(">" + menu[currItem].title, 1)
                    lcd.text(" " + menu[nextItem].title, 2)
                    turnDir = 0
            elif(not turnDir):
                if (not clkState and dtState):
                    turnDir = 1
                elif(clkState and not dtState):
                    turnDir = -1
    except Exception as e:
        print(e)
        print(traceback.format_exc())
    finally:        
        settings.call_stop()
        print("flag raaised")
        GPIO.cleanup()
        print("GPIO handled")
        sys.exit(0)
        os.exit(0)
        settings.get_sdr().close()
        print("sdr closed")
        lcd.clear()
        print("lcd Cleared")
        exit()


# makes us run main when this file is run
if __name__ == "__main__":
    
    main() 
