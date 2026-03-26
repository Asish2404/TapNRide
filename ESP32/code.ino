// ESP32 code for RFID + GPS + LCD Display
#include <SPI.h>
#include <MFRC522.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#include <TinyGPSPlus.h>

// ---------------- RFID ----------------
#define SS_PIN 5
#define RST_PIN 2
#define BUZZER 4

MFRC522 mfrc522(SS_PIN, RST_PIN);

// ---------------- LCD ----------------
LiquidCrystal_I2C lcd(0x27, 16, 2);

// ---------------- GPS ----------------
TinyGPSPlus gps;

// GPS pins
#define RXD2 16
#define TXD2 17

void setup()
{
    Serial.begin(115200);

    // RFID SPI
    SPI.begin(18, 19, 23, 5);
    mfrc522.PCD_Init();

    // GPS
    Serial2.begin(9600, SERIAL_8N1, RXD2, TXD2);

    pinMode(BUZZER, OUTPUT);

    // LCD
    lcd.init();
    lcd.backlight();
    lcd.clear();

    lcd.setCursor(0, 0);
    lcd.print("Smart Bus");
    lcd.setCursor(0, 1);
    lcd.print("Scan Card...");
}

void loop()
{
    // --------- GPS Update ---------
    while (Serial2.available() > 0)
    {
        gps.encode(Serial2.read());
    }

    // --------- RFID Check ---------
    if (!mfrc522.PICC_IsNewCardPresent())
    {
        return;
    }

    if (!mfrc522.PICC_ReadCardSerial())
    {
        return;
    }

    Serial.print("Card UID:");

    String uid = "";

    for (byte i = 0; i < mfrc522.uid.size; i++)
    {
        if (mfrc522.uid.uidByte[i] < 0x10)
            uid += "0";

        uid += String(mfrc522.uid.uidByte[i], HEX);
    }

    uid.toUpperCase();

    Serial.println(uid);

    // -------- GPS Data --------
    float lat = 0;
    float lng = 0;

    if (gps.location.isValid())
    {
        lat = gps.location.lat();
        lng = gps.location.lng();
    }
    else
    {
        lcd.clear();
        lcd.setCursor(0, 0);
        lcd.print("GPS Not Ready");
        delay(2000);
    }

    Serial.print("Latitude: ");
    Serial.println(lat, 6);

    Serial.print("Longitude: ");
    Serial.println(lng, 6);

    // -------- Buzzer --------
    digitalWrite(BUZZER, HIGH);

    // -------- LCD Display --------
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("UID:");
    lcd.print(uid);

    lcd.setCursor(0, 1);
    lcd.print("Loc:");
    lcd.print(lat, 2);
    lcd.print(",");
    lcd.print(lng, 2);

    delay(2000);

    digitalWrite(BUZZER, LOW);

    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("Scan Next Card");

    delay(2000);

    mfrc522.PICC_HaltA();
}