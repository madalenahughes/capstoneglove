import board
import busio
import time
import serial
from adafruit_pca9685 import PCA9685

# Initializes the PCA
i2c = busio.I2C(board.SCL, board.SDA)
pca = PCA9685(i2c)
pca.frequency = 50

# Initialize UART as the serial on GPIO 15
uart = serial.Serial(
    port='/dev/serial0',
    baudrate=9600,        # TODO: Make sure the baud rate is the same as the one on the esp
    timeout=0.1           # Non-blocking: returns after 0.1s if no data
)

# Converts the deseried angle of the motor into the proper format
def motorDuty(angle):
	minUS = 500
	maxUS = 3000
	periodUS = 20000

	pulseUS = minUS + (angle / 180.0) * (maxUS - minUS)
	duty = int((pulseUS / periodUS) * 65535)
	return duty

# Reads the signal recieved then finds the case that matches the signal,
# then sets the proper angles for the motors by calling the motorDuty function
def motorSignal(handSignal, motors):
	match handSignal:
		case "rest":
			print("rest")
			motors = [motorDuty(90), motorDuty(90), motorDuty(90), motorDuty(90), motorDuty(90)]
		case "fist":
			print("fist")
			motors = [motorDuty(0), motorDuty(0), motorDuty(0), motorDuty(0), motorDuty(0)]
		case "index pinch":
			print("index pinch")
			motors = [motorDuty(45), motorDuty(45), motorDuty(90), motorDuty(90), motorDuty(90)]
		case "middle pinch":
			print("middle pinch")
			motors = [motorDuty(45), motorDuty(90), motorDuty(45), motorDuty(90), motorDuty(90)]
		case "thumbs up":
			print("thumbs up")
			motors = [motorDuty(180), motorDuty(0), motorDuty(0), motorDuty(0), motorDuty(0)]
		case "index point":
			print("index point")
			motors = [motorDuty(0), motorDuty(180), motorDuty(0), motorDuty(0), motorDuty(0)]
		case "peace":
			print("peace")
			motors = [motorDuty(0), motorDuty(180), motorDuty(180), motorDuty(0), motorDuty(0)]
		case "thumb flex":
			print("thumb flex")
			motors = [motorDuty(0), motorDuty(90), motorDuty(90), motorDuty(90), motorDuty(90)]
		case "index flex":
			print("index flex")
			motors = [motorDuty(90), motorDuty(0), motorDuty(90), motorDuty(90), motorDuty(90)]
		case "middle flex":
			print("middle flex")
			motors = [motorDuty(90), motorDuty(90), motorDuty(0), motorDuty(90), motorDuty(90)]
		case "ring flex":
			print("ring flex")
			motors = [motorDuty(90), motorDuty(90), motorDuty(90), motorDuty(0), motorDuty(90)]
		case "pinky flex":
			print("pinky flex")
			motors = [motorDuty(90), motorDuty(90), motorDuty(90), motorDuty(90), motorDuty(0)]
	return motors

# This is just here to run our demonstration tests, it will go through each signal twice
def test(motors):
	# Test signal
	signals = ["rest", "fist", "index pinch", "middle pinch", "thumbs up", "index point", "peace", "thumb flex", "index flex", "middle flex", "ring flex", "pinky flex"]
	for j in range(2):
		for handSignal in signals:
			motors = motorSignal(handSignal, motors)
			for i, motor in enumerate(motors):
				pca.channels[i].duty_cycle = motor
				print(i, motor)
			time.sleep(2)

# This will send the signal from the motor array to the PCA
def applyMotors(motors):
    for i, motor in enumerate(motors):
        pca.channels[i].duty_cycle = motor
        print(i, motor)

# An array that correlates to each motor order is thumb, index, middle, ring, pinky
motors = [motorDuty(90), motorDuty(90), motorDuty(90), motorDuty(90), motorDuty(90)]
# When starting up it sets all motors to the rest position
print("Starting up - rest position")
applyMotors(motors)
time.sleep(1)


# The current test code for each case...comment out when using ESP integration
runStart = input("Enter Case: ")

while runStart != "quit":
	if runStart == "test":
		test(motors)
	else:
		handSignal = runStart
		motors = motorSignal(handSignal, motors)
		for i, motor in enumerate(motors):
			pca.channels[i].duty_cycle = motor
			print(i, motor)
	runStart = input("Enter Case: ")
	#runStart = "quit"

input("Exiting...")


"""
# Listens for signals from the ESP and will continuously run until interrupted by the keyboard...uncomment when using ESP integration
print("Listening for signals on GPIO 15...")

try:
    while True:
        if uart.in_waiting > 0:
            raw = uart.readline()
            handSignal = raw.decode('utf-8').strip()  # Decode bytes and strip whitespace/newline

            if handSignal:
                print(f"Received: '{handSignal}'")
                motors = motorSignal(handSignal, motors)
                applyMotors(motors)
except KeyboardInterrupt:
    print("Exiting...")
    uart.close()
"""
