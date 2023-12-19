from phew import logging, server, access_point, dns,connect_to_wifi
from phew.template import render_template
from phew.server import redirect
#from pimoroni import Button
import am2320
import badger2040
import badger_os
import time
#import sleep
from machine import I2C, Pin
from pcf85063a import PCF85063A
import _thread
from shsecret import ssid,password
# Display Setup
display = badger2040.Badger2040()
display.led(18)
display.set_update_speed(2)
display.set_font("bitmap6")

#Sensor & RTC setup
i2c = I2C(0,scl=Pin(5), sda=Pin(4),freq=400000)
sensor = am2320.AM2320(i2c)
rtc_pcf85063a = PCF85063A(i2c)
#sleep(5)
#badger2040.pico_rtc_to_pcf()
badger2040.pcf_to_pico_rtc()

          
# def buttons():
#     while True:
#         if display.pressed(BUTTON_A):
#             print("Tare")
#             scale.tare()
#             measure()
#         elif display.pressed(badger2040.BUTTON_B):
#             print("Update")
#             measure()
#     sleep(0.5)        


def clear():
    display.set_pen(15)
    display.clear()

#_thread.start_new_thread(buttons,())

def measure():
    dtdisp = rtc_pcf85063a.datetime()
    sensor.measure()
    temp = sensor.temperature()
    hum = sensor.humidity()
    clear()
    display.set_pen(BLACK)
    display.text('Tare',17,115,240,2)
    display.text('Update',122,115,240,2)
    display.text('Date = {:02d}/{:02d}/{:04d} {:02d}:{:02d}'.format(dtdisp[2], dtdisp[1], dtdisp[0], dtdisp[3], dtdisp[4]),5,5,240,2)
    display.text('Temp = '+ str(sensor.temperature()) + ' C',5, 25, 250, 3)
    display.text('Humidity = '+ str(sensor.humidity()) + ' %',5, 50, 250, 3)
    display.update()

DOMAIN = "KHF Apiary"  # This is the address that is shown on the Captive Portal

@server.route("/", methods=["GET"])
def index(request):
#    dtdisp = rtc_pcf85063a.datetime()
    dtdisp=time.localtime()
    print(dtdisp)
    sensor.measure()
    tempr = sensor.temperature()
    print(tempr)
    humr = sensor.humidity()
    print(humr)
    return await render_template("index.html", temp=tempr, tnow=dtdisp, hum=humr)

@server.route("/update",methods=['GET','POST'])
def update():
    dtdisp = rtc_pcf85063a.datetime()
    sensor.measure()
    temp = sensor.temperature()
    hum = sensor.humidity()
    return render_template("index.html",temp=temp,tnow=dtdisp,hum=hum)


# microsoft windows redirects
@server.route("/ncsi.txt", methods=["GET"])
def hotspot(request):
    print(request)
    print("ncsi.txt")
    return "", 200


@server.route("/connecttest.txt", methods=["GET"])
def hotspot(request):
    print(request)
    print("connecttest.txt")
    return "", 200


@server.route("/redirect", methods=["GET"])
def hotspot(request):
    print(request)
    print("****************ms redir*********************")
    return redirect(f"http://{DOMAIN}/", 302)

# android redirects
@server.route("/generate_204", methods=["GET"])
def hotspot(request):
    print(request)
    print("******generate_204********")
    return redirect(f"http://{DOMAIN}/", 302)

# apple redir
@server.route("/hotspot-detect.html", methods=["GET"])
def hotspot(request):
    print(request)
    """ Redirect to the Index Page """
    return render_template("index.html")


@server.catchall()
def catch_all(request):
    print("***************CATCHALL***********************\n" + str(request))
    return redirect("http://" + DOMAIN + "/")

ip_address = connect_to_wifi(ssid,password)
print(f"Connected to wifi, IP address {ip_address}")

# Set to Accesspoint mode
# Change this to whatever Wifi SSID you wish
#ap = access_point("KHF Apiary Monitoring",password=None)
#ap = access_point("KHF")

# # Catch all requests and reroute them
#dns.run_catchall(ip)
server.run()                            # Run the server
logging.info("Webserver Started")