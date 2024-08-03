from RPi import GPIO
from rpi_lcd import LCD
from streamaudio import *
from RadioSettingsTracker import *
import time
import datetime
import traceback

# Purpose: Bundles menu titles and the functions to shoot off when that item 
#          is selected
class LCDMenuItem():
    def __init__(self, title = "No Title", action = lambda : "No action"):
        self.title = title
        self.action = action

    def set_action(self, lam):
        self.action = lam
    
    def set_title(self, title):
        self.title = title

    def __str__(self):
        return self.title

'''
   7654 3210
|  0000.0000 MHz |
|     ^          |

'''
def print_freq_menu(lcd, settings):
    lcd.text("  %09.4f MHz" %(settings.cf / 1e6), 1)
    lcd.text("  " + " " * ((7 + (settings.cfStepCol < 4)) - settings.cfStepCol) + "^", 2)

def freq_tune_menu(lcd, settings, clk, dt, sw, clk2, dt2, sw2):
    lcd.clear()
    
    print_freq_menu(lcd, settings)
    
    LlastSWstate = GPIO.input(sw)
    RturnDir = 0
    LturnDir = 0

    while True:
        time.sleep(0.01)
        LswState  = GPIO.input(sw)
        LclkState = GPIO.input(clk)
        LdtState  = GPIO.input(dt)
        RclkState = GPIO.input(clk2)
        RdtState  = GPIO.input(dt2)

        # Look for pushing in rotary encoder, return on release
        if LswState == 0 and LlastSWstate != 0:
            return
            LlastSWstate = 0
        elif(LswState == 1 and LlastSWstate == 0):
            LlastSWstate = 1
                
        # Check for turning left rotary encoder
        if (LclkState == 1 and LdtState == 1):
            if(LturnDir):
                settings.nudge_cf(LturnDir)
                LturnDir = 0
                print_freq_menu(lcd, settings)
        elif(not LturnDir):
            if (not LclkState and LdtState):
                LturnDir = 1
            elif(LclkState and not LdtState):
                LturnDir = -1

        # Check for turning right rotary encoder
        if (RclkState == 1 and RdtState == 1):
            if(RturnDir):
                settings.nudge_cf_step(-1 * RturnDir)
                RturnDir = 0
                print_freq_menu(lcd, settings)
        elif(not RturnDir):
            if (not RclkState and RdtState):
                RturnDir = 1
            elif(RclkState and not RdtState):
                RturnDir = -1

'''
    543 210
|   000.000 kHz  |
|     ^          |

'''
def print_bw_menu(lcd, settings):
    lcd.text("   %07.3f kHz" %(settings.bw / 1e3), 1)
    
    lcd.text("   " + " " * (5 - settings.bwStepCol + (settings.bwStepCol < 3)) + "^", 2)

def bw_menu(lcd, settings, clk, dt, sw, clk2, dt2, sw2):
    lcd.clear()

    print_bw_menu(lcd, settings)
    
    LlastSWstate = GPIO.input(sw)
    RturnDir = 0
    LturnDir = 0

    while True:
        time.sleep(0.01)
        LswState  = GPIO.input(sw)
        LclkState = GPIO.input(clk)
        LdtState  = GPIO.input(dt)
        RclkState = GPIO.input(clk2)
        RdtState  = GPIO.input(dt2)

        # Look for pushing in rotary encoder, return on release
        if LswState == 0 and LlastSWstate != 0:
            return
            LlastSWstate = 0
        elif(LswState == 1 and LlastSWstate == 0):
            LlastSWstate = 1
                
        # Check for turning left rotary encoder
        if (LclkState == 1 and LdtState == 1):
            if(LturnDir):
                settings.nudge_bw(LturnDir)
                LturnDir = 0
                print_bw_menu(lcd, settings)
        elif(not LturnDir):
            if (not LclkState and LdtState):
                LturnDir = 1
            elif(LclkState and not LdtState):
                LturnDir = -1

        # Check for turning right rotary encoder
        if (RclkState == 1 and RdtState == 1):
            if(RturnDir):
                settings.nudge_bw_step(-1 * RturnDir)
                RturnDir = 0
                print_bw_menu(lcd, settings)
        elif(not RturnDir):
            if (not RclkState and RdtState):
                RturnDir = 1
            elif(RclkState and not RdtState):
                RturnDir = -1

# Demodulation options
def set_fm_radio(settings):
    settings.set_demod_profile(override = decode_fm)
    settings.set_filter_from_KB(settings.filtFMRadio)
def set_aircom(settings):
    settings.set_demod_profile(override = decode_am)
    settings.set_filter_from_KB(settings.filtAIRCOM)
def set_auto(settings):
    settings.reset_demod_profile()

def print_demod_menu(lcd, settings, menu, currItem, nextItem):
    if settings.currDemod == currItem:
        lcd.text(">" + menu[currItem].title + "*", 1)
        lcd.text(" " + menu[nextItem].title, 2)
    elif settings.currDemod == nextItem:
        lcd.text(">" + menu[currItem].title, 1)
        lcd.text(" " + menu[nextItem].title + "*", 2)
    else:
        lcd.text(">" + menu[currItem].title, 1)
        lcd.text(" " + menu[nextItem].title, 2)

def demod_menu(lcd, settings, clk, dt, sw, clk2, dt2, sw2):
    lcd.clear()

    fmRadProf  = LCDMenuItem(title = "FM Radio", action = set_fm_radio)
    aircomProf = LCDMenuItem(title = "AIRCOM",   action = set_aircom)
    autoProf   = LCDMenuItem(title = "AUTO",     action = set_auto)
    menu = [fmRadProf,
            aircomProf, 
            autoProf]

    currItem = 0
    nextItem = 1

    print_demod_menu(lcd, settings, menu, currItem, nextItem)
    
    LlastSWstate = GPIO.input(sw)
    RlastSWstate = GPIO.input(sw)
    LturnDir = 0

    while True:
        time.sleep(0.01)
        LswState  = GPIO.input(sw)
        LclkState = GPIO.input(clk)
        LdtState  = GPIO.input(dt)
        RswState  = GPIO.input(sw2)

        # Look for pushing in left rotary encoder, return on release
        if LswState == 0 and LlastSWstate != 0:
            return
            LlastSWstate = 0
        elif(LswState == 1 and LlastSWstate == 0):
            LlastSWstate = 1

        # Check for turning left rotary encoder
        if (LclkState == 1 and LdtState == 1):
            if(LturnDir):
                currItem = (currItem + LturnDir) % len(menu)
                nextItem = (nextItem + LturnDir) % len(menu)
                print_demod_menu(lcd, settings, menu, currItem, nextItem)
                LturnDir = 0    
        elif(not LturnDir):
            if (not LclkState and LdtState):
                LturnDir = 1
            elif(LclkState and not LdtState):
                LturnDir = -1
                
        # Look for pushing in right rotary encoder, set demod on release
        if RswState == 0 and RlastSWstate != 0:
            menu[currItem].action(settings)
            settings.currDemod = currItem
            RlastSWstate = 0
            print_demod_menu(lcd, settings, menu, currItem, nextItem)
        elif(RswState == 1 and RlastSWstate == 0):
            RlastSWstate = 1
        
'''
----------------|
-00.00    -00.00|
 [ONF]     ^^ ^^|
----------------|
'''

def print_squelch_menu(lcd, settings, ct):  
    # Only update current power in every 1s so you have time to read it
    if ct == 0:
        settings.curDb = np.mean(settings.lastDBMean)
    
    if (settings.curDb < 0):
        curDb = "%06.2f" % settings.curDb
    else:
        curDb = "+%05.2f" % settings.curDb
    
    if settings.squelch < 0:
        sqlDb = "%06.2f" % settings.squelch
    else:
        sqlDb = "+%05.2f" % settings.squelch
    
    s1 = " "*(6 - len(curDb)) + curDb + "    " + " "*(6 - len(sqlDb)) + sqlDb 
    
    if settings.doSquelch:
        s2 = " [ON]      " + " " * (3 - settings.squelchIdx + (settings.squelchIdx < 2)) + "^"
    else:
        s2 = " [OFF]     " + " " * (3 - settings.squelchIdx + (settings.squelchIdx < 2)) + "^"
    
    lcd.text(s1, 1)
    lcd.text(s2, 2)

def squelch_menu(lcd, settings, clk, dt, sw, clk2, dt2, sw2):
    lcd.clear()

    print_squelch_menu(lcd, settings, 0)    
    LlastSWstate = GPIO.input(sw)
    RturnDir = 0
    LturnDir = 0
    RlastSWstate = GPIO.input(sw2)

    ct = 0

    while True:
        ct = (ct + 1) % 100
        if (ct == 0):
            print_squelch_menu(lcd, settings, 0)

        time.sleep(0.01)
        LswState  = GPIO.input(sw)
        LclkState = GPIO.input(clk)
        LdtState  = GPIO.input(dt)
        RclkState = GPIO.input(clk2)
        RdtState  = GPIO.input(dt2)
        RswState  = GPIO.input(sw2)

        # Look for pushing in left rotary encoder, return on release
        if LswState == 0 and LlastSWstate != 0:
            return
            LlastSWstate = 0
        elif(LswState == 1 and LlastSWstate == 0):
            LlastSWstate = 1
                
        # Check for turning left rotary encoder
        if (LclkState == 1 and LdtState == 1):
            if(LturnDir):
                settings.nudge_squelch(LturnDir)
                LturnDir = 0
                print_squelch_menu(lcd, settings, 0)    
                
        elif(not LturnDir):
            if (not LclkState and LdtState):
                LturnDir = 1
            elif(LclkState and not LdtState):
                LturnDir = -1
        
        # Look for pushing in right rotary encoder, toggle on release
        if RswState == 0 and RlastSWstate != 0:
            settings.doSquelch = not settings.doSquelch
            print_squelch_menu(lcd, settings, 0)
            RlastSWstate = 0
        elif(RswState == 1 and RlastSWstate == 0):
            RlastSWstate = 1

        # Check for turning right rotary encoder
        if (RclkState == 1 and RdtState == 1):
            if(RturnDir):
                settings.nudge_squelch_step(-1 * RturnDir)
                RturnDir = 0
                print_squelch_menu(lcd, settings, ct)
        elif(not RturnDir):
            if (not RclkState and RdtState):
                RturnDir = 1
            elif(RclkState and not RdtState):
                RturnDir = -1

'''
----------------|
Volume Norm 100%|
  [AVG]   +/-00%|
----------------|
'''

def print_vol_menu(lcd, settings):  
    s1 = "Volume Norm %3d" % int(settings.vol * 100)
    s1 += "%"

    s2 = f"   [{settings.volModes[settings.volMode]}]" + "  +/-%2d" % int(settings.volStepArr[settings.volIdx] * 100)
    s2 += "%"

    lcd.text(s1, 1)
    lcd.text(s2, 2)

def vol_menu(lcd, settings, clk, dt, sw, clk2, dt2, sw2):
    lcd.clear()

    print_vol_menu(lcd, settings)    
    LlastSWstate = GPIO.input(sw)
    RturnDir = 0
    LturnDir = 0
    RlastSWstate = GPIO.input(sw2)

    while True:
        time.sleep(0.01)
        LswState  = GPIO.input(sw)
        LclkState = GPIO.input(clk)
        LdtState  = GPIO.input(dt)
        RclkState = GPIO.input(clk2)
        RdtState  = GPIO.input(dt2)
        RswState  = GPIO.input(sw2)

        # Look for pushing in left rotary encoder, return on release
        if LswState == 0 and LlastSWstate != 0:
            return
            LlastSWstate = 0
        elif(LswState == 1 and LlastSWstate == 0):
            LlastSWstate = 1
                
        # Check for turning left rotary encoder
        if (LclkState == 1 and LdtState == 1):
            if(LturnDir):
                settings.nudge_vol(LturnDir)
                LturnDir = 0
                print_vol_menu(lcd, settings)    
                
        elif(not LturnDir):
            if (not LclkState and LdtState):
                LturnDir = 1
            elif(LclkState and not LdtState):
                LturnDir = -1
        
        # Look for pushing in right rotary encoder, toggle on release
        if RswState == 0 and RlastSWstate != 0:
            settings.volMode = (settings.volMode + 1) % len(settings.volModes)
            print_vol_menu(lcd, settings)
            RlastSWstate = 0
        elif(RswState == 1 and RlastSWstate == 0):
            RlastSWstate = 1

        # Check for turning right rotary encoder
        if (RclkState == 1 and RdtState == 1):
            if(RturnDir):
                settings.nudge_vol_step(RturnDir)
                RturnDir = 0
                print_vol_menu(lcd, settings)
        elif(not RturnDir):
            if (not RclkState and RdtState):
                RturnDir = 1
            elif(RclkState and not RdtState):
                RturnDir = -1

def disp_live_dB(lcd, settings, clk, dt, sw, clk2, dt2, sw2):
    lcd.clear()

    LlastSWstate = GPIO.input(sw)
    #        |________________|
    lcd.text("Min   Mean   Max", 1)
    while True:
        time.sleep(2)
        LswState  = GPIO.input(sw)

        lcd.text("%4.1f %4.1f %4.1f"% (np.mean(settings.lastDBMin), np.mean(settings.lastDBMean), np.mean(settings.lastDBMax)), 2)      

        # Look for pushing in left rotary encoder, return on release
        if LswState == 0 and LlastSWstate != 0:
            return
            LlastSWstate = 0
        elif(LswState == 1 and LlastSWstate == 0):
            LlastSWstate = 1