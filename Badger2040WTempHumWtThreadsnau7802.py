# Hive temp/humidity/weight monitoring with time or timestamps using Badger2040W.
import badger2040
import badger_os
import am2320
import nau7802mp
from time import sleep
from utime import sleep_us
from machine import I2C, Pin
from pcf85063a import PCF85063A
import _thread

WTCF = 22339 #Scales Calibration Factor

# Display Setup
display = badger2040.Badger2040()
display.led(18)
display.set_update_speed(2)
# sleep(5)
# Connects to the wireless network. Ensure you have entered your details in WIFI_CONFIG.py :).
# display.connect()

# ntptime.settime()
# time.localtime()
i2c = I2C(0,scl=Pin(5), sda=Pin(4),freq=400000)
sensor = am2320.AM2320(i2c)
scale = nau7802mp.NAU7802(i2c)
rtc_pcf85063a = PCF85063A(i2c)
sleep(5)
badger2040.pico_rtc_to_pcf()
# badger2040.pcf_to_pico_rtc()
# sleep(5)

#check scale is connected and working
scalecon = scale.isConnected()
print("Scale available:", scalecon)
avail = scale.begin()
# if avail() = False:
#     scale.reset
#     print("Scale resetting:", avail)
# elif avail =True
print("Scale Avail:", avail)

# Display setup Inky Pack
BLACK = 0
display.set_update_speed(2)
display.set_font("bitmap6")#

def buttons():
    while True:
        if display.pressed(badger2040.BUTTON_A):
#             print("Tare")
            scale.tare()
            measure()
        elif display.pressed(badger2040.BUTTON_B):
#             print("Update")
            measure()
    sleep(0.5)        
    
def measure():
    dtdisp = rtc_pcf85063a.datetime()
    sensor.measure()
    temp = sensor.temperature()
#    val = (scale.getWeight()/WTCF) # stable value divide by correction factor to display in kg
    val = (scale.getWeight()) # stable value divide by correction factor to display in kg
    dispval=(f'{val:.2f}')
    print(dispval)
    clear()
    display.set_pen(BLACK)
    display.text('Tare',17,115,240,2)
    display.text('Update',122,115,240,2)
    display.text('Date = {:02d}/{:02d}/{:04d} {:02d}:{:02d}'.format(dtdisp[2], dtdisp[1], dtdisp[0], dtdisp[3], dtdisp[4]),5,5,240,2)
    display.text('Temp = '+ str(sensor.temperature()) + ' C',5, 25, 250, 3)
    display.text('Humidity = '+ str(sensor.humidity()) + ' %',5, 50, 250, 3)
    display.text('Weight = '+ str(dispval) + ' kg',5, 80, 250, 3)
#     display.text('Weight = ' + ' kg',5, 80, 240, 3)
    display.update()

def clear():
    display.set_pen(15)
    display.clear()

_thread.start_new_thread(buttons,())

while True:
#     sleep(5)
    measure()
    sleep(6)