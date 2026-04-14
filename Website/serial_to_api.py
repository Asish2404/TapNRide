import serial
import requests

ser = serial.Serial('COM7', 115200)

while True:
    line = ser.readline().decode(errors='ignore').strip()
    if not line or "," not in line:
        continue

    try:
        card_UID, Bus_Stop = line.split(",")
        Bus_Stop = int(Bus_Stop)

        print("TAP:", card_UID, "at stop", Bus_Stop)

        r = requests.post("http://127.0.0.1:8000/scan", data={
            "card_id": card_UID,
            "keyStop": Bus_Stop
        })

        # print("Response:", r.status_code, r.text)

    except Exception as e:
        print("Error:", e)