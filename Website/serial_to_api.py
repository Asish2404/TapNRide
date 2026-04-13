#--------------------------
import serial # fetching Key pressed & Card ID from Arduino IDE - serial
import requests # for making API calls to fetch data from Arduino IDE

ser=serial.Serial('COM7', 115200)
while True:
    line = ser.readline().decode().strip()
    if line:
        try:
            card_UID, Bus_Stop = line.split(",") # format ---> card_id,key_Stop
            r = requests.post("http://127.0.0.1:8000/scan", data={
                "card_id": card_UID,
                "keyStop": int(Bus_Stop)
            })
            print("Sent:", card_UID, Bus_Stop, "Response:", r.status_code, r.text)
        except ValueError:
            # If the line is not in "UID,stopKey" format
            print("Invalid line:", line)