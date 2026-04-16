import serial

# --- Configuration ---
SERIAL_PORT = '/dev/serial0'
BAUD_RATE   = 115200

# Valid gesture labels matching ESP32 gestureName() output
VALID_GESTURES = {
    "FIST",
    "PINCH",
    "MIDDLE-PINCH",
    "PEACE",
    "THUMBS-UP",
    "POINT",
    "THUMB",
    "INDEX",
    "MIDDLE",
    "RING",
    "PINKY",
    "EXTENSION",
    "REST"
}

def handle_gesture(gesture: str):
    if gesture == "FIST":
        pass  # TODO: motor command for FIST

    elif gesture == "PINCH":
        pass  # TODO: motor command for PINCH

    elif gesture == "MIDDLE-PINCH":
        pass  # TODO: motor command for MIDDLE-PINCH

    elif gesture == "PEACE":
        pass  # TODO: motor command for PEACE

    elif gesture == "THUMBS-UP":
        pass  # TODO: motor command for THUMBS-UP

    elif gesture == "POINT":
        pass  # TODO: motor command for POINT

    elif gesture == "THUMB":
        pass  # TODO: motor command for THUMB

    elif gesture == "INDEX":
        pass  # TODO: motor command for INDEX

    elif gesture == "MIDDLE":
        pass  # TODO: motor command for MIDDLE

    elif gesture == "RING":
        pass  # TODO: motor command for RING

    elif gesture == "PINKY":
        pass  # TODO: motor command for PINKY

    elif gesture == "EXTENSION":
        pass  # TODO: motor command for EXTENSION

    elif gesture == "REST":
        pass  # TODO: stop / hold motor position

def main():
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        print(f"Listening on {SERIAL_PORT} at {BAUD_RATE} baud...")
    except serial.SerialException as e:
        print(f"Failed to open serial port: {e}")
        return

    while True:
        try:
            line = ser.readline().decode('utf-8', errors='ignore').strip()

            if not line:
                continue  # skip empty lines

            if line not in VALID_GESTURES:
                continue  # discard garbled or partial lines

            print(f"Gesture: {line}")
            handle_gesture(line)

        except serial.SerialException as e:
            print(f"Serial error: {e}")
            break

        except KeyboardInterrupt:
            print("Stopped by user.")
            break

    ser.close()

if __name__ == "__main__":
    main()