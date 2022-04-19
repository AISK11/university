#include <HCSR04.h>
#define PIN_HCSR04_TRIG 16
#define PIN_HCSR04_ECHO 17

double* _hcsr_distances;
int hcsr_value = -1;

double getDistanceCm(double *distance) {
  distance = HCSR04.measureDistanceCm();
  return distance[0];
}

void setup() {
  Serial.begin(9600); /* initialize serial communication at 9600 bits per second. */
  Serial.print("\n\n-------------------- START --------------------\n");
  HCSR04.begin(PIN_HCSR04_TRIG, PIN_HCSR04_ECHO);
  Serial.print("[+] Distance sensor HC-SR04 initialized.\n");
}

void loop() {
  hcsr_value = round(getDistanceCm(_hcsr_distances)); /* convert double to int */
  Serial.print("Measured distance: ");
  Serial.print(hcsr_value);
  Serial.print(" cm.\n");
  delay(1000);
}
