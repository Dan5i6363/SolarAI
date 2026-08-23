# ESP32 + SX1278 future integration

These sketches are untested hardware examples. They use an SX1278 at 433 MHz,
an I2C SSD1306 OLED, and a buzzer. Adjust pins/frequency for your board and
antenna/regulatory requirements. The payload is JSON telemetry followed by the
same CRC32 concept as Python; no RF performance is claimed.
