import pyaudio as pa
import numpy as np
import time
from signal import pause

from rpi_lcd import LCD


lcd = LCD()
try:
    lcd.text("HELLO %3.2f" %1.34 , 1)

    pause()
finally:
    lcd.clear()
