# Hive temp/humidity/weight monitoring with time or timestamps using Pico Lipo.
from picographics import PicoGraphics, DISPLAY_INKY_PACK
import am2320
from hx711 import HX711
import time
from pimoroni import Button
from machine import I2C, Pin

WTCF = 22339 #Scales Calibration Factor

# Display Setup
display = PicoGraphics(display=DISPLAY_INKY_PACK)

# Inky Pack Buttons
button_a = Button(12)
button_b = Button(13)
button_c = Button(14)

i2c = I2C(0,scl=Pin(5), sda=Pin(4),freq=400000)
sensor = am2320.AM2320(i2c)
          
class Scales(HX711):
    def __init__(self, d_out, pd_sck):
        super(Scales, self).__init__(d_out, pd_sck)
        self.offset = 0

    def reset(self):
        self.power_off()
        self.power_on()

    def tare(self):
        self.offset = self.read()

    def raw_value(self):
        return self.read() - self.offset

    def stable_value(self, reads=10, delay_us=500):
        values = []
        for _ in range(reads):
            values.append(self.raw_value())
            sleep_us(delay_us)
        return self._stabilizer(values)

    @staticmethod
    def _stabilizer(values, deviation=10):
        weights = []
        for prev in values:
            weights.append(sum([1 for current in values if prev == current == 0 or prev != 0 and abs(prev - current) / (abs(prev) / 100) <= deviation]))
        return sorted(zip(values, weights), key=lambda x: x[1]).pop()[0]

scales = Scales(d_out=10, pd_sck=9)

# Display setup Inky Pack
BLACK = 0
display.set_update_speed(2)
display.set_font("bitmap6")#

def measure():
    dtdisp = time.gmtime()
    sensor.measure()
    temp = sensor.temperature()
    val = (scales.stable_value()/WTCF) # stable value divide by correction factor to display in kg
    dispval=(f'{val:.2f}')
    clear()
    display.set_pen(BLACK)
    display.text('Tare',17,115,240,2)
    display.text('Update',122,115,240,2)
    display.text('Date = {:02d}/{:02d}/{:04d} {:02d}:{:02d}'.format(dtdisp[2], dtdisp[1], dtdisp[0], dtdisp[3], dtdisp[4]),5,5,240,2)
    display.text('Temp = '+ str(sensor.temperature()) + ' C',5, 25, 240, 3)
    display.text('Humidity = '+ str(sensor.humidity()) + ' %',5, 50, 240, 3)
    display.text('Weight = '+ str(dispval) + ' kg',5, 80, 240, 3)
    display.update()

def clear():
    display.set_pen(15)
    display.clear()

while True:
    measure()
#     if display.pressed(badger2040.BUTTON_A):
#         print("Tare")
#         scales.tare()
#     elif display.pressed(badger2040.BUTTON_B):
#         print("B")
#         measure()
#     display.halt()
#     badger2040.sleep_for(2)
    time.sleep(120)