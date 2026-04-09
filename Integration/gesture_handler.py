import serial

# Match the baud rate set in ESP32's Serial.begin()
ser = serial.Serial('/dev/ttyS0', 115200, timeout=1)

def handle_gesture(gesture: int):
    if gesture == 1:
        pass  # trigger REST motor routine
    elif gesture == 2:
        pass  # trigger FIST motor routine
    elif gesture == 3:
        pass  # trigger PINCH motor routine
    elif gesture == 4:
        pass  # trigger MIDDLE-PINCH motor routine
    elif gesture == 5:
        pass  # trigger POINT motor routine
    elif gesture == 6:
        pass  # trigger THUMBS-UP motor routine
    elif gesture == 7:
        pass  # trigger PEACE motor routine
    elif gesture == 8:
        pass  # trigger THUMB motor routine
    elif gesture == 9:
        pass  # trigger INDEX motor routine
    elif gesture == 10:
        pass  # trigger MIDDLE motor routine
    elif gesture == 11:
        pass  # trigger RING motor routine
    elif gesture == 12:
        pass  # trigger PINKY motor routine

print("Listening for gestures...")

while True:
    line = ser.readline().decode('utf-8', errors='ignore').strip()
    if line:
        print(f"Received: {line}")
        handle_gesture(line)

# install pyserial