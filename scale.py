import nau7802mp
from time import sleep
from machine import I2C, Pin

i2c = I2C(0,scl=Pin(5), sda=Pin(4),freq=400000)
scale = nau7802mp.NAU7802(i2c)

if scale.isConnected():
    print("Connected!\n")
else:
    print("Can't find the scale, exiting ...\n")

# Calculate the zero offset
print("Calculating the zero offset...")
scale.calculateZeroOffset()
print("The zero offset is : {0}\n".format(scale.getZeroOffset()))
    
print("Put a known mass on the scale.")
cal = float(input("Mass in kg? "))

# Calculate the calibration factor
print("Calculating the calibration factor...")
scale.calculateCalibrationFactor(cal)
print("The calibration factor is : {0:0.3f}\n".format(scale.getCalibrationFactor()))

input("Press [Enter] to measure a mass. ")					
print("Mass is {0:0.3f} kg".format(scale.getWeight()))