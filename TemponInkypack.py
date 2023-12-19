# Temp on picow with inky pack display

from picographics import PicoGraphics, DISPLAY_INKY_PACK
from pimoroni import Button
from onewire import OneWire
from ds18x20 import DS18X20
import time
from machine import Pin
import _thread


display = PicoGraphics(display=DISPLAY_INKY_PACK)
ds = DS18X20(OneWire(Pin(22)))
sensor_id = ds.scan()[0]

# Inky Pack Buttons
button_a = Button(12)
#button_a = machine.Pin(12, machine.Pin.IN, pull=machine.Pin.PULL_UP)
button_b = Button(13)
#button_a = machine.Pin(13, machine.Pin.IN, pull=machine.Pin.PULL_UP)
button_c = Button(14)
#button_a = machine.Pin(14, machine.Pin.IN, pull=machine.Pin.PULL_UP)

# Display setup Inky Pack
BLACK = 0
display.set_update_speed(2)
display.set_font("bitmap6")#

#counter of how many updates since start - useful when datetime not available. ie on battery but not RTC
ct = 0

def clear():
    display.set_pen(15)
    display.clear()

def buttons():
    while True:
        if button_a.read():
            print("Tare")
    #             scales.tare()
    #             measure()
        elif button_b.read():
            pupdate()
            ct += 1
            print('Updated')
        elif button_c.read():
            print("Button C")
    sleep(0.5)

def measure():
    dtdisp = time.gmtime()
    tnow = ('Date = {}/{}/{} {}:{}'.format(dtdisp[2], dtdisp[1], dtdisp[0], dtdisp[3], dtdisp[4]))
    ds.convert_temp()
    time.sleep(0.75)
    temp = ds.read_temp(sensor_id)
#     print("temp = " + str(temp) + " count = " + str(ct))
    clear()
    display.set_pen(BLACK)
    display.text('But A',240,15,240,2)
    display.text('Update',225,55,240,2)
    display.text('But C',240,95,240,2)
    display.text('Date = {:02d}/{:02d}/{:04d} {:02d}:{:02d}'.format(dtdisp[2], dtdisp[1], dtdisp[0], dtdisp[3], dtdisp[4]),5,5,240,2)
    display.text('Temp = '+ str(temp) + ' °C',5, 40, 240, 2)
    display.text('Count = ' + str(ct),5,110,120,2)
    display.update()
#    counter += 1    
    
def pupdate():
    dtdisp = time.gmtime()
    tnow = ('Date = {}/{}/{} {}:{}'.format(dtdisp[2], dtdisp[1], dtdisp[0], dtdisp[3], dtdisp[4]))
    ds.convert_temp()
    time.sleep(0.75)
    temp = ds.read_temp(sensor_id)
    print("temp = " + str(temp))
    display.text('Date = {:02d}/{:02d}/{:04d} {:02d}:{:02d}'.format(dtdisp[2], dtdisp[1], dtdisp[0], dtdisp[3], dtdisp[4]),5,5,240,2)
    display.text('Temp = '+ str(temp) + ' °C',5, 40, 240, 2)
    display.text('Count = ' + int(ct),5,115,100,2)
#    display.partial_update(5,5,100,40)
    display.update()
#    ct += 1
    
_thread.start_new_thread(buttons,())
    
while True:
    measure()
    ct +=1
    time.sleep(600)