#include <TinyGPSPlus.h>

// The TinyGPSPlus object
TinyGPSPlus gps;
bool printedOnce = false;  // flag to ensure printing only once

void setup() {
  Serial.begin(9600);
  Serial2.begin(9600, SERIAL_8N1, 16, 17); // RX=16, TX=17
  delay(3000);
}

void loop() {
  while (Serial2.available() > 0) {
    if (gps.encode(Serial2.read())) {
      if (!printedOnce && gps.location.isValid()) {
        displayInfo();
        printedOnce = true;  // prevent further prints
      }
    }
  }

  if (millis() > 5000 && gps.charsProcessed() < 10) {
    Serial.println(F("No GPS detected: check wiring."));
    while (true);
  }
}

void displayInfo() {
  Serial.print(F("Location: "));
  if (gps.location.isValid()) {
    Serial.print("Lat: ");
    Serial.print(gps.location.lat(), 6);
    Serial.print(F(", "));
    Serial.print("Lng: ");
    Serial.print(gps.location.lng(), 6);
    Serial.println();
  } else {
    Serial.print(F("INVALID"));
  }
}
void updateSerial()
{
  delay(500);
  while (Serial.available())
  {
    Serial2.write(Serial.read());//Forward what Serial received to Software Serial Port
  }
  while (Serial2.available())
  {
    Serial.write(Serial2.read());//Forward what Software Serial received to Serial Port
  }
}