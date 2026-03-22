import serial
import requests

ser = serial.Serial("COM7",115200,timeout=1)

print("Waiting for RFID scans...")

while True:
    try:
        if ser.in_waiting > 0:

            uid = ser.readline().decode('utf-8',errors='ignore').strip()

            if "Card UID" in uid:

                uid = uid.replace("Card UID:", "").replace(" ","").strip()

                print("Received UID:", uid)

                response = requests.post(
                    "http://127.0.0.1:8000/scan",
                    params={
                        "card_id": uid,
                        "from_stop": "BusStop1",
                        "to_stop": "BusStop2"
                    }
                )

                print("Server Response:", response.text)

    except Exception as e:
        print("Error:", e)