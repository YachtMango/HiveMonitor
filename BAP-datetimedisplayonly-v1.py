# Hive temp/humidity/weight monitoring no time or timestamps- pico and inkypack display version
from pimoroni import Button
from picographics import PicoGraphics, DISPLAY_INKY_PACK
import am2320
from hx711 import HX711
import time
from utime import sleep_us
from machine import I2C, Pin
import uasyncio 

WTCF = 22339 #Scales Calibration Factor

# time.localtime()
i2c = I2C(0,scl=Pin(5), sda=Pin(4),freq=400000)
sensor = am2320.AM2320(i2c) #  Temperature and Humidiaty sensor
display = PicoGraphics(display=DISPLAY_INKY_PACK) # Pimoroni e-ink display
button_a = Button(12)
# button_b = Button(13)
# button_c = Button(14)
          
class Scales(HX711): # curtesy of https://github.com/SergeyPiskunov/micropython-hx711
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

scales = Scales(d_out=10, pd_sck=9) # instance of Scales Class with relevent pins

async def dispbuttons(): # coroutine for buttons on inky pack display
    while True:
        if button_a.read():
            print("A")
            scales.tare()
#         elif button_b.read():
#             print("B")
#             dispvals()
#         elif button_c.read():
#             print('C')  
        await uasyncio.sleep_ms(50)
        

# Display setup 
BLACK = 0
display.set_update_speed(2)
display.set_font("bitmap6")

def clear():
    display.set_pen(15)
    display.clear()

async def dispvals():
    sensor.measure()
    temp = sensor.temperature()
    val = (scales.stable_value()/WTCF) # stable value divide by correction factor to display in kg
    dispval=(f'{val:.2f}')
    clear()
    display.set_pen(BLACK)
    display.text('Tare',250,15,240,2)
    display.text('Temp = '+ str(sensor.temperature()) + ' C',5, 25, 240, 3)
    display.text('Humidity = '+ str(sensor.humidity()) + ' %',5, 55, 240, 3)
    display.text('Weight loss = '+ str(dispval) + ' kg',5, 80, 240, 3)
    print(dispval)
    display.update()
    await uasyncio.sleep_ms(50)
    
async def main():
    uasyncio.create_task(dispbuttons())
    while True:
        uasyncio.create_task(dispvals())
        await uasyncio.sleep_ms(5000)
        
uasyncio.run(main())