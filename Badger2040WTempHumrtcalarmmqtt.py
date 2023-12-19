# Hive temp/humidity monitoring with timestamps using Badger2040W.
import badger2040
import badger_os
import am2320
import time
from utime import sleep_us
from machine import I2C, Pin
from pcf85063a import PCF85063A
from umqtt.simple import MQTTClient
from phew import connect_to_wifi
from khsecret import ssid,password

# Connect to wifi network
connect_to_wifi(ssid,password)

# Network values
MQTT_BROKER = "192.168.0.22"

# Hive specfic values
#PUBLISH_TOPIC = b"TestHivename"


# Display Setup
display = badger2040.Badger2040()
display.led(18)
display.set_update_speed(2)

time.localtime()
i2c = I2C(0,scl=Pin(5), sda=Pin(4),freq=400000)
sensor = am2320.AM2320(i2c)
rtc_pcf85063a = PCF85063A(i2c)
badger2040.pico_rtc_to_pcf()
# badger2040.pcf_to_pico_rtc()

print(rtc_pcf85063a.datetime())

# Display setup Inky Pack
BLACK = 0
display.set_update_speed(2)
display.set_font("bitmap6")#

oserror = 0

def measure():
    dtdisp = rtc_pcf85063a.datetime()
    sensor.measure()
    temp = sensor.temperature()
    hum = sensor.humidity()
    clear()
    display.set_pen(BLACK)
    display.text('OSerror = ' + str(oserror),17,115,240,2)
    display.text('Date = {:02d}/{:02d}/{:04d} {:02d}:{:02d}'.format(dtdisp[2], dtdisp[1], dtdisp[0], dtdisp[3], dtdisp[4]),5,5,240,2)
    display.text('Temp = '+ str(sensor.temperature()) + ' C',5, 25, 240, 3)
    display.text('Humidity = '+ str(sensor.humidity()) + ' %',5, 50, 240, 3)
    #display.text('Weight = '+ str(dispval) + ' kg',5, 80, 240, 3)
    display.update()
    c = MQTTClient("testumqtt",MQTT_BROKER)
    c.connect()
    c.publish(b'TestHivename/temp',str(temp),qos=1)
    c.publish(b'TestHivename/hum',str(hum),qos=1)
    c.disconnect()


def clear():
    display.set_pen(15)
    display.clear()

while True:
    try:
        measure()
        print('temp =',sensor.temperature(),'humidity =',sensor.humidity())
    except OSError:
        oserror +=1
        continue
#    time.sleep(3600)
    badger2040.sleep_for(60)
