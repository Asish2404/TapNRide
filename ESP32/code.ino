#include <SPI.h>
#include <MFRC522.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#include <TinyGPSPlus.h>
#include <Keypad.h>

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

// ---------------- KEYPAD ----------------
const byte ROWS = 4; 
const byte COLS = 4; 

char keys[ROWS][COLS] = {
  {'D','C','B','A'},
  {'#','9','6','3'},
  {'0','8','5','2'},
  {'*','7','4','1'}
};

byte rowPins[ROWS] = {12, 13, 14, 15}; 
byte colPins[COLS] = {26, 25, 33, 32}; 

Keypad keypad = Keypad(makeKeymap(keys), rowPins, colPins, ROWS, COLS);

// -------- KEYPAD INPUT STORAGE --------
String input = "";
String ip = "";

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
    lcd.print("System Ready");

    delay(2000);

    lcd.clear();
    lcd.print("Enter ID...");
}

void loop()
{
    // --------- KEYPAD INPUT ---------
    char key = keypad.getKey();

    if (key)
    {
        if (key == '#')  // ENTER
        {
            ip = input;

            lcd.clear();
            lcd.setCursor(0, 0);
            lcd.print("ID:");
            lcd.setCursor(0, 1);
            lcd.print(ip);

            input = "";
            delay(1500);

            lcd.clear();
            lcd.print("Scan Card...");
        }
        else if (key == '*') // CLEAR
        {
            input = "";
            lcd.clear();
            lcd.print("Cleared");

            delay(1000);

            lcd.clear();
            lcd.print("Scan Card...");
        }
        else if (key >= '0' && key <= '9')   // ✅ only numbers
        {
            input += key;

            lcd.clear();
            lcd.setCursor(0, 0);
            lcd.print("Enter ID:");
            lcd.setCursor(0, 1);
            lcd.print(input);
        }
    }

    // --------- RFID CHECK ---------
    if (!mfrc522.PICC_IsNewCardPresent())
        return;

    if (!mfrc522.PICC_ReadCardSerial())
        return;

    // ❌ Do NOT proceed if ID not entered
    if (ip == "")
    {
        Serial.println("ERROR:EMPTY_ID");

        lcd.clear();
        lcd.print("Enter ID First");
        delay(1500);

        return;
    }

    String uid = "";

    for (byte i = 0; i < mfrc522.uid.size; i++)
    {
        if (mfrc522.uid.uidByte[i] < 0x10)
            uid += "0";

        uid += String(mfrc522.uid.uidByte[i], HEX);
    }

    uid.toUpperCase();

    // ✅ ONLY VALID OUTPUT FORMAT
    Serial.print(uid);
    Serial.print(",");
    Serial.println(ip);   // 🔥 ONLY THIS PRINT

    // -------- BUZZER --------
    digitalWrite(BUZZER, HIGH);

    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("UID:");
    lcd.print(uid);

    delay(2000);

    digitalWrite(BUZZER, LOW);

    lcd.clear();
    lcd.print("Done");

    delay(1500);

    lcd.clear();
    lcd.print("Enter ID");

    ip = "";  // ✅ reset after use

    mfrc522.PICC_HaltA();
}