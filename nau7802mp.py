"""
MicroPython nau7802 I2C driver
"""
import time
import machine
import struct

# Constants
DEVICE_ADDRESS = 0x2A

NAU7802_CTRL1 = 0x00
NAU7802_CTRL2 = 0x01
NAU7802_ADC = 0x02
NAU7802_ADCO_B2 = 0x12
NAU7802_PU_CTRL = 0x0C

NAU7802_PU_CTRL_CR = 0
NAU7802_PU_CTRL_RR = 1
NAU7802_PU_CTRL_PUD = 2
NAU7802_PU_CTRL_PUA = 3
NAU7802_PU_CTRL_PUR = 4

class NAU7802:
    """ Class to communicate with the NAU7802 """
    def __init__(self, i2c_bus=None):
        self._i2cPort = i2c_bus
        self._zeroOffset = 0
        self._calibrationFactor = 1.0

    def begin(self, wire_port=None, initialize=True):
        if wire_port is not None:
            self._i2cPort = machine.I2C(scl=wire_port[0], sda=wire_port[1])

        if not self.isConnected():
            if not self.isConnected():
                return False

        result = True

        if initialize:
            result &= self.reset()
            result &= self.powerUp()
            result &= self.setLDO(3)  # Set LDO to 3.3V
            result &= self.setGain(7)  # Set gain to 128
            result &= self.setSampleRate(3)  # Set samples per second to 80
            result &= self.setRegister(NAU7802_ADC, 0x30)
            result &= self.setBit(7, NAU7802_PU_CTRL)  # Enable 330pF decoupling cap on ch. 2
            result &= self.calibrateAFE()

        return result

    def isConnected(self):
        return DEVICE_ADDRESS in self._i2cPort.scan()

    def available(self):
        return self.getBit(NAU7802_PU_CTRL_CR, NAU7802_PU_CTRL)

    def getReading(self):
        value_list = self._i2cPort.readfrom(DEVICE_ADDRESS, 3)
        value = struct.unpack(">i", b'\x00' + value_list)[0]
        return value

    def getAverage(self, average_amount):
        total = 0
        samples_acquired = 0
        start_time = time.ticks_ms()

        while samples_acquired < average_amount:
            if self.available():
                total += self.getReading()
                samples_acquired += 1

            if time.ticks_ms() - start_time > 1000:
                return 0

            time.sleep_ms(1)

        total /= average_amount
        return total

    def calculateZeroOffset(self, average_amount=8):
        self.setZeroOffset(self.getAverage(average_amount))

    def setZeroOffset(self, new_zero_offset):
        self._zeroOffset = new_zero_offset

    def getZeroOffset(self):
        return self._zeroOffset

    def calculateCalibrationFactor(self, weight_on_scale, average_amount=8):
        onScale = self.getAverage(average_amount)
        newCalFactor = (onScale - self._zeroOffset) / weight_on_scale
        self.setCalibrationFactor(newCalFactor)

    def setCalibrationFactor(self, new_cal_factor):
        self._calibrationFactor = new_cal_factor

    def getCalibrationFactor(self):
        return self._calibrationFactor

    def getWeight(self, allow_negative_weights=True, samples_to_take=8):
        on_scale = self.getAverage(samples_to_take)

        if not allow_negative_weights:
            if on_scale < self._zeroOffset:
                on_scale = self._zeroOffset

        weight = (on_scale - self._zeroOffset) / self._calibrationFactor
        return weight

    def setGain(self, gain_value):
        if gain_value > 0b111:
            gain_value = 0b111

        value = self.getRegister(NAU7802_CTRL1)
        value &= 0b11111000
        value |= gain_value
        return self.setRegister(NAU7802_CTRL1, value)

    def setLDO(self, ldo_value):
        if ldo_value > 0b111:
            ldo_value = 0b111

        value = self.getRegister(NAU7802_CTRL1)
        value &= 0b11000111
        value |= ldo_value << 3
        self.setRegister(NAU7802_CTRL1, value)
        return self.setBit(7, NAU7802_PU_CTRL)

    def setSampleRate(self, rate):
        if rate > 0b111:
            rate = 0b111

        value = self.getRegister(NAU7802_CTRL2)
        value &= 0b10001111
        value |= rate << 4
        return self.setRegister(NAU7802_CTRL2, value)

    def calibrateAFE(self):
        self.beginCalibrateAFE()
        return self.waitForCalibrateAFE(1000)

    def beginCalibrateAFE(self):
        self.setBit(5, NAU7802_CTRL2)

    def waitForCalibrateAFE(self, timeout_ms=0):
        timeout_s = timeout_ms / 1000
        begin = time.time()
        cal_ready = self.calAFEStatus()

        while cal_ready == NAU7802_CAL_IN_PROGRESS:
            if (timeout_ms > 0) and ((time.time() - begin) > timeout_s):
                break
            time.sleep_ms(1)
            cal_ready = self.calAFEStatus()

        if cal_ready == NAU7802_CAL_SUCCESS:
            return True
        else:
            return False

    def calAFEStatus(self):
        if self.getBit(5, NAU7802_CTRL2):
            return NAU7802_CAL_IN_PROGRESS

        if self.getBit(6, NAU7802_CTRL2):
            return NAU7802_CAL_FAILURE

        return NAU7802_CAL_SUCCESS

    def reset(self):
        self.setBit(0, NAU7802_PU_CTRL)
        time.sleep_ms(1)
        return self.clearBit(0, NAU7802_PU_CTRL)

    def powerUp(self):
        self.setBit(1, NAU7802_PU_CTRL)
        self.setBit(2, NAU7802_PU_CTRL)
        counter = 0

        while not self.getBit(3, NAU7802_PU_CTRL):
            time.sleep_ms(1)
            if counter > 100:
                return False
            counter += 1

        return True

    def powerDown(self):
        self.clearBit(2, NAU7802_PU_CTRL)
        return self.clearBit(3, NAU7802_PU_CTRL)

    def setIntPolarityHigh(self):
        return self.clearBit(1, NAU7802_CTRL1)

    def setIntPolarityLow(self):
        return self.setBit(1, NAU7802_CTRL1)

    def getRevisionCode(self):
        revisionCode = self.getRegister(0x00)
        return revisionCode & 0x0F

    def setBit(self, bit_number, register_address):
        value = self.getRegister(register_address)
        value |= (1 << bit_number)
        return self.setRegister(register_address, value)

    def clearBit(self, bit_number, register_address):
        value = self.getRegister(register_address)
        value &= ~(1 << bit_number)
        return self.setRegister(register_address, value)

    def getBit(self, bit_number, register_address):
        value = self.getRegister(register_address)
        value &= (1 << bit_number)
        return bool(value)

    def getRegister(self, register_address):
        try:
            return self._i2cPort.readfrom_mem(DEVICE_ADDRESS, register_address, 1)[0]
        except OSError:
            return -1

    def setRegister(self, register_address, value):
        try:
            self._i2cPort.writeto_mem(DEVICE_ADDRESS, register_address, bytes([value]))
            return True
        except OSError:
            return False
