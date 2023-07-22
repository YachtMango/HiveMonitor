from phew import logging, server, access_point, dns
from phew.template import render_template
from phew.server import redirect
from pimoroni import Button
from picographics import PicoGraphics, DISPLAY_INKY_PACK
import am2320
from hx711 import HX711
import time
from utime import sleep_us
# import ntptime
from machine import I2C, Pin
import uasyncio 

WTCF = 22339 #Scales Calibration Factor

time.localtime()
i2c = I2C(0,scl=Pin(5), sda=Pin(4),freq=400000)
sensor = am2320.AM2320(i2c)
display = PicoGraphics(display=DISPLAY_INKY_PACK)
button_a = Button(12)
button_b = Button(13)
button_c = Button(14)
          
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

async def dispbuttons():
    while True:
        if button_a.read():
            print("A")
            scales.tare()
        elif button_b.read():
            print("B")
            dispvals()
        elif button_c.read():
            print('C')  
        await uasyncio.sleep_ms(50)
        

# Display setup 
BLACK = 0
display.set_update_speed(2)
display.set_font("bitmap6")

def clear():
    display.set_pen(15)
    display.clear()

DOMAIN = "KHF Apiary"  # This is the address that is shown on the Captive Portal

@server.route("/", methods=["GET"])
def index(request):
async def dispvals():
    dtdisp = time.gmtime()
    dtdata = time.time()
    tnow = ('Date = {}/{}/{} {}:{}'.format(dtdisp[2], dtdisp[1], dtdisp[0], dtdisp[3], dtdisp[4]))
#     sensor.measure()
#     temp = sensor.temperature()
#     val = (scales.stable_value()/WTCF) # stable value divide by correction factor to display in kg
#     dispval=(f'{val:.2f}')
    clear()
    display.set_pen(BLACK)
    display.text('Timestamp = ' + str(dtdata),5,5,240,2)
    display.text('Date = {}/{}/{} {}:{}'.format(dtdisp[2], dtdisp[1], dtdisp[0], dtdisp[3], dtdisp[4]),5,20,240,2)
    display.text('Temp = '+ str(sensor.temperature()) + ' C',5, 50, 240, 3)
    display.text('Humidity = '+ str(sensor.humidity()) + ' %',5, 75, 240, 3)
#     display.text('Weight = '+ str(dispval) + ' kg',5, 100, 240, 3)
#     print(dispval)
    display.update()
    await uasyncio.sleep_ms(5000)
    
async def main():
    uasyncio.create_task(dispbuttons())
    while True:
#         print("running")
        uasyncio.create_task(dispvals())
        await uasyncio.sleep_ms(5000)
        
uasyncio.run(main())
    
    return render_template("index.html",temp=temp,dtdisp=tnow,val=dispval)

@server.route("/update",methods=['GET','POST'])
def update():
    dtdisp = time.gmtime()
    dtdata = time.time()
    sensor.measure()
    clear()
    display.set_pen(BLACK)
    display.text('Timestamp = ' + str(dtdata),5,5,240,2)
    display.text('Date = {}/{}/{} {}:{}'.format(dtdisp[2], dtdisp[1], dtdisp[0], dtdisp[3], dtdisp[4]),5,20,240,2)
    display.text('Temp = '+ str(sensor.temperature()) + ' C',5, 50, 240, 3)
    display.text('Humidity = '+ str(sensor.humidity()) + ' %',5, 75, 240, 3)
    display.text('Weight = '+ str(val)+' kg',5, 100, 240, 3)
    display.update()
    return render_template("index.html",dtdisp=dtdata,)


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


# Set to Accesspoint mode
# Change this to whatever Wifi SSID you wish
ap = access_point("KHF Apiary Monitoring", password="khf")
ip = ap.ifconfig()[0]
# Grab the IP address and store it
logging.info(f"starting DNS server on {ip}")
# # Catch all requests and reroute them
dns.run_catchall(ip)
server.run()                            # Run the server
logging.info("Webserver Started")