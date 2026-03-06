import board
import busio
import time
from adafruit_pca9685 import PCA9685

# Initializes the PCA
i2c = busio.I2C(board.SCL, board.SDA)
pca = PCA9685(i2c)
pca.frequency = 50

# An array that correlates to each motor order is thumb, index, middle, ring, pinky
motors = [motorDuty(90), motorDuty(90), motorDuty(90), motorDuty(90), motorDuty(90)]

# Converts the deseried angle of the motor into the proper format
def motorDuty(angle):
	minUS = 1000
	maxUS = 2000
	periodUS = 20000

	pulseUS = minUS + (angle / 180.0) * (maxUS - minUS)
	duty = int((pulseUS / periodUS) * 65535)
	return duty

# Reads the signal recieved then finds the case that matches the signal,
# then sets the proper angles for the motors by calling the motorDuty function
def motorSignal(handSignal, motors):
	match handSignal:
		case "fist":
			motors = [motorDuty(0), motorDuty(0), motorDuty(0), motorDuty(0), motorDuty(0)]
		case "pinch":
			motors = [motorDuty(45), motorDuty(25), motorDuty(90), motorDuty(90), motorDuty(90)]
		case "index":
			motors = [motorDuty(90), motorDuty(0), motorDuty(90), motorDuty(90), motorDuty(90)]
		case "rest":
			motors = [motorDuty(90), motorDuty(90), motorDuty(90), motorDuty(90), motorDuty(90)]
	return motors

# This is just here to run our demonstration tests, it will go through each signal twice
def test(motors):
	# Test signal
	signals = ["fist", "pinch", "index", "rest"]
	for i in range(2):
		for handSignal in signals:
			motors = motorSignal(handSignal, motors)
			for i, motor in enumerate(motors):
				pca.channels[i].duty_cycle = motor
			time.sleep(5)

# It will set all motors to the default, wait 2 seconds, then run the test
for i, motor in enumerate(motors):
	pca.channels[i].duty_cycle = motor
time.sleep(2)
test(motors)