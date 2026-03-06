import serial
import csv
import sys
from datetime import datetime

PORT = "/dev/cu.usbserial-0001"  # change to your ESP32 port
BAUD = 115200
OUTPUT_FILE = f"emg_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
HEADER = ["fist", "pinch", "extension", "sample"]

def main():
    print(f"Opening port {PORT} at {BAUD} baud...")
    try:
        ser = serial.Serial(PORT, BAUD, timeout=2)
    except serial.SerialException as e:
        print(f"Could not open port: {e}")
        sys.exit(1)

    print(f"Writing to {OUTPUT_FILE}")

    with open(OUTPUT_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(HEADER)

        while True:
            line = ser.readline().decode("utf-8", errors="ignore").strip()
            if not line:
                continue
            if line == "DATA COLLECTION COMPLETE":
                print("Done — data collection complete.")
                break
            parts = [p.strip() for p in line.split(",")]
            if len(parts) == 4:
                writer.writerow(parts)
                f.flush()
                print(parts)
            else:
                print(f"Skipping malformed line: {line}")

    ser.close()

if __name__ == "__main__":
    main()
