from RPi import GPIO
from rpi_lcd import LCD
from streamaudio import *
from RadioSettingsTracker import *
import time
import traceback

# Purpose: Bundles menu titles and the functions to shoot off 
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

def freq_tune_menu(lcd, settings, clk, dt, sw, clk2, dt2, sw2):
    lcd.clear()
    lcd.text("%6.3f MHz" %(settings.get_cf()[1] / 1e6), 1)
    lcd.text("Step:%6.3f MHz" %(settings.get_cf_step() / 1e6), 2)
    
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

        # Look for pushing in rotary encoder, activate fx on release
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
                lcd.text("%6.3f MHz" %(settings.get_cf()[1] / 1e6), 1)
        elif(not LturnDir):
            if (not LclkState and LdtState):
                LturnDir = 1
            elif(LclkState and not LdtState):
                LturnDir = -1

        # Check for turning right rotary encoder
        if (RclkState == 1 and RdtState == 1):
            if(RturnDir):
                settings.nudge_cf_step(RturnDir)
                RturnDir = 0
                lcd.text("Step:%6.3f MHz" %(settings.get_cf_step() / 1e6), 2)
        elif(not RturnDir):
            if (not RclkState and RdtState):
                RturnDir = 1
            elif(RclkState and not RdtState):
                RturnDir = -1


def bw_menu(lcd, settings, clk, dt, sw, clk2, dt2, sw2):
    lcd.clear()
    lcd.text("%6.3f kHz" %(settings.get_bw() / 1e3), 1)
    lcd.text("Step:%6.3f kHz" %(settings.get_bw_step() / 1e3), 2)
    
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
                lcd.text("%6.3f kHz" %(settings.get_bw() / 1e3), 1)
        elif(not LturnDir):
            if (not LclkState and LdtState):
                LturnDir = 1
            elif(LclkState and not LdtState):
                LturnDir = -1

        # Check for turning right rotary encoder
        if (RclkState == 1 and RdtState == 1):
            if(RturnDir):
                settings.nudge_bw_step(RturnDir)
                RturnDir = 0
                lcd.text("Step:%6.3f kHz" %(settings.get_bw_step() / 1e3), 2)
        elif(not RturnDir):
            if (not RclkState and RdtState):
                RturnDir = 1
            elif(RclkState and not RdtState):
                RturnDir = -1

# Demodulation options
def set_am_radio(settings):
    settings.set_demod_profile(override = decode_am)
    settings.set_filter_from_KB(settings.filtAMRadio)
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
    amRadProf  = LCDMenuItem(title = "AM Radio", action = set_am_radio)
    aircomProf = LCDMenuItem(title = "AIRCOM",   action = set_aircom)
    autoProf   = LCDMenuItem(title = "AUTO",     action = set_auto)
    menu = [fmRadProf,
            amRadProf,
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
        

def print_hammer_menu(lcd, settings, selection):
    s1 = "Yes"
    s2 = "No"

    print(f"Selection: {selection}")
    print(f"Setting: {settings.doHammer}")

    if (selection):
        s1 = ">" + s1
        s2 = " " + s2
    else:
        s1 = " " + s1
        s2 = ">" + s2

    if (settings.doHammer):
        s1 = s1 + "*"
        s2 = s2 + " "
    else:
        s1 = s1 + " "
        s2 = s2 + "*"

    lcd.text(f" {s1}    {s2}", 2)


def hammer_menu(lcd, settings, clk, dt, sw, clk2, dt2, sw2):
    lcd.clear()
    lcd.text("Hammer Audio?", 1)
    
    LlastSWstate = GPIO.input(sw)
    RlastSWstate = GPIO.input(sw)
    LturnDir = 0

    selection = True

    print_hammer_menu(lcd, settings, selection)
    
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
                selection = not selection
                print_hammer_menu(lcd, settings, selection)
                LturnDir = 0    
        elif(not LturnDir):
            if (not LclkState and LdtState):
                LturnDir = 1
            elif(LclkState and not LdtState):
                LturnDir = -1
                
        # Look for pushing in right rotary encoder, write to settings on release
        if RswState == 0 and RlastSWstate != 0:
            settings.doHammer = selection
            RlastSWstate = 0
            print_hammer_menu(lcd, settings, selection)
        elif(RswState == 1 and RlastSWstate == 0):
            RlastSWstate = 1
