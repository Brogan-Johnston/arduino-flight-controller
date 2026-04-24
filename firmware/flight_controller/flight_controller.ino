/*
 * flight_controller.ino
 * Arduino UNO R3 — Flight Stick & Throttle Controller
 *
 * Reads joystick X/Y axes, joystick button, and a potentiometer
 * for throttle. Sends CSV data over USB serial at 50 Hz for the
 * PC app to consume.
 *
 * Serial output format (115200 baud):
 *   X,Y,BTN,THROTTLE\n
 *   X, Y:      0–1023  (joystick analog, center ≈ 512)
 *   BTN:       0 or 1  (1 = pressed)
 *   THROTTLE:  0–1023  (potentiometer raw ADC)
 *
 * Calibration (0% and 100% positions) is handled by the PC app and
 * stored in default_config.json — no EEPROM writes needed on the Arduino.
 *
 * Wiring (no breadboard):
 *   Joystick VRx  → A0
 *   Joystick VRy  → A1
 *   Joystick SW   → D2  (active LOW, uses INPUT_PULLUP)
 *   Joystick VCC  → 5V  (Arduino power header)
 *   Joystick GND  → GND (Arduino power header, first GND pin)
 *   Throttle pot wiper → A2
 *   Throttle pot VCC   → Joystick VCC pin (daisy-chained, no breadboard needed)
 *   Throttle pot GND   → GND (Arduino power header, second GND pin)
 */

// ── Pin definitions ────────────────────────────────────────────────────
const int JOY_X_PIN    = A0;
const int JOY_Y_PIN    = A1;
const int JOY_BTN_PIN  = 2;
const int THROTTLE_PIN = A2;

// ── Timing ────────────────────────────────────────────────────────────
// 50 Hz output (one packet every 20 ms)
const unsigned long SEND_INTERVAL_MS = 20;
unsigned long lastSendTime = 0;

// ── Setup ─────────────────────────────────────────────────────────────
void setup() {
  Serial.begin(115200);
  pinMode(JOY_BTN_PIN, INPUT_PULLUP);
}

// ── Main loop ─────────────────────────────────────────────────────────
void loop() {
  unsigned long now = millis();

  if (now - lastSendTime >= SEND_INTERVAL_MS) {
    lastSendTime = now;

    int joyX     = analogRead(JOY_X_PIN);
    int joyY     = analogRead(JOY_Y_PIN);
    int button   = (digitalRead(JOY_BTN_PIN) == LOW) ? 1 : 0;
    int throttle = analogRead(THROTTLE_PIN);

    Serial.print(joyX);
    Serial.print(',');
    Serial.print(joyY);
    Serial.print(',');
    Serial.print(button);
    Serial.print(',');
    Serial.println(throttle);
  }
}
