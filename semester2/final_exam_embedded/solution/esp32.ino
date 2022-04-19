/****************
 **  Purpose   **
 ****************/
/*
Sends distance sensor data to MQTT broker.

Algorithm:
1. ESP32 connects to WiFi (public or protected via WPA-PSK)
2. ESP32 connects to specified MQTT broker on specified topic
3. loads data from distance sensor HC-SR04 in centimeters
4. convert data to JSON format
5. send JSON data to MQTT broker on specified topic
6. repeat step 3

Result can be tested on Linux with command: $(mosquitto_sub -h <mqtt_server> -p <mqtt_port> -t <mqtt_topic>)
*/


/****************
 ** Schematics **
 ****************/
/*
1. Wemos Mini D1 ESP8266 CP2104 ESP32/32S:
        +---------------+
GND|--- |o|o         o|o| ---|GND
---|036 |o|o         o|o| ---|027
039|026 |o|o         o|o| 022|025
035|018 |o|o         o|o| 021|032
033|019 |o|o         o|o| 017|012
034|023 |o|o         o|o| 016|004
014|005 |o|o         o|o| GND|000
---|3V3 |o|o         o|o| VCC|002
009|--- |o|o         o|o| ---|---
---|--- |o|o         o|o| ---|---
        +------USB------+

2. HC-SR04:
HCSR04 VCC  <=> EPS32 VCC
HCSR04 Trig <=> ESP32 016
HCSR04 Echo <=> ESP32 017
HCSR04 GND  <=> ESP32 GND
*/


/****************
 **   Set Up   **
 ****************/
/*
1. Arduino USB port:
* Tools -> Port -> /dev/ttyUSB0

2. Arduino ESP32 Board:
* File -> Preferences -> Additional Boards Manager URLs: https://dl.espressif.com/dl/package_esp32_index.json,http://arduino.esp8266.com/stable/package_esp8266com_index.json -> OK
* Tools -> Board -> Boards Manager -> Arduino AVR Boards -> Install|Update
* Tools -> Board -> Boards Manager -> esp32 -> Install
* Tools -> Board -> ESP32 Arduino -> DOIT ESP32 DEVKIT V1

3. Install necessary libraries:
* Sketch -> Include Library -> Manage Libraries -> "HC-SR04"
* Sketch -> Include Library -> Manage Libraries -> "ArduinoJson"
* Sketch -> Include Library -> Manage Libraries -> "PubSubClient"

4. Fix for Linux - cannot upload code via serial port:
* $(python3 -m pip install pyserial)

5. Fix for Linux (Artix) - user privileges to /dev/ttyUSB0:
* $(sudo usermod -aG uucp <USER>)
*/


/****************
 ** References **
 ****************/
/*
* ESP32 Board: https://www.instructables.com/Installing-the-ESP32-Board-in-Arduino-IDE-Windows-/
* D1 ESP32 pins: https://robolabor.ee/et/arendusplaadid/1066-d1-mini-esp-wroom-32.html
* https://www.eelectronicparts.com/products/mh-et-live-d1-mini-esp32-esp-32-wifi-bluetooth-internet-of-things-development-board
* https://techtutorialsx.com/2017/04/29/esp32-sending-json-messages-over-mqtt/
* https://create.arduino.cc/projecthub/abdularbi17/ultrasonic-sensor-hc-sr04-with-arduino-tutorial-327ff6
* https://roboticsbackend.com/arduino-led-complete-tutorial/
* https://gist.github.com/me-no-dev/2d2b51b17226f5e9c5a4d9a78bdc0720
* https://www.metageek.com/training/resources/understanding-rssi/
* https://mntolia.com/10-free-public-private-mqtt-brokers-for-testing-prototyping/
* https://arduinojson.org/
* http://www.steves-internet-guide.com/arduino-sending-receiving-json-mqtt/

- MQTT:
* library API: https://pubsubclient.knolleary.net/api#state
*/

/******************************************************************************/

/* Libraries */
#include <HCSR04.h>
#include <WiFi.h>
#include <ArduinoJson.h>
#include <PubSubClient.h> /* MQTT */

/* Constants */
#define KEY_NONE    0
#define KEY_WEP     1
#define KEY_WPA_PSK 2
#define KEY_WPA_EAP 3

/* GPIO Pins */
#define PIN_HCSR04_TRIG 16
#define PIN_HCSR04_ECHO 17

/* Config Variables */
const char* wifi_essid       = "esp32";
const unsigned char wifi_key = KEY_WPA_PSK;
const char* wifi_password    = "cisco123";

const char* mqtt_server   = "public.mqtthq.com";
const int mqtt_port       = 1883;
const char* mqtt_topic    = "garage_sensor";
const char* mqtt_user     = "";
const char* mqtt_password = "";

const char* json_device_name       = "ESP32";
unsigned short json_resend_timeout = 1000; /* ms */

/* Program Variables */
unsigned char exit_status_code = 0; /* 0 = OK */
WiFiClient wifi_client;
PubSubClient mqtt_client(wifi_client);
double* _hcsr_distances;
int hcsr_value = -1;

/******************************************************************************/

unsigned char connectToWiFi(void) {
  Serial.print("    Connecting to WiFi \"");
  Serial.print(wifi_essid);
  Serial.print("\"");

  if(wifi_key == KEY_NONE) {
    WiFi.begin(wifi_essid);
  }
  else if(wifi_key == KEY_WPA_PSK) {
    WiFi.begin(wifi_essid, wifi_password);
  }

  unsigned char wait_counter = 0;
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
    wait_counter++;
    if (wait_counter >= 20) {
      break;
    }
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.print("\n[+] Conected to WiFi \"");
    Serial.print(WiFi.SSID());
    Serial.print("\"");
    Serial.print(" with IP address: ");
    Serial.print(WiFi.localIP());
    Serial.print(" [");
    byte mac[6];
    WiFi.macAddress(mac);
    Serial.print(mac[5], HEX);
    Serial.print(":");
    Serial.print(mac[4], HEX);
    Serial.print(":");
    Serial.print(mac[3], HEX);
    Serial.print(":");
    Serial.print(mac[2], HEX);
    Serial.print(":");
    Serial.print(mac[1], HEX);
    Serial.print(":");
    Serial.print(mac[0], HEX);
    Serial.print("]");
    Serial.print(" (signal: ");
    long rssi = WiFi.RSSI();
    Serial.print(rssi);
    if (rssi > -67) {
      Serial.print(" (Amazing)");
    }
    else if (rssi > -70) {
      Serial.print(" (Very Good)");
    }
    else if (rssi > -80) {
      Serial.print(" (Okay)");
    }
    else if (rssi > -90) {
      Serial.print(" (Not Good)");
    }
    else {
      Serial.print(" (Unusable)");
    }
    Serial.print(").\n");
    return 0;
  }
  else {
    Serial.print("\n[-] Connection to WiFi \"");
    Serial.print(wifi_essid);
    Serial.print("\" failed!\n");
  }
  return 1;
}


unsigned char connectToMqtt(void) {
  mqtt_client.setServer(mqtt_server, mqtt_port);
  Serial.print("    Connecting to MQTT server ");
  Serial.print(mqtt_server);
  Serial.print(":");
  Serial.print(mqtt_port);
  Serial.print(" \"");
  Serial.print(mqtt_topic);
  Serial.print("\"...");

  if (mqtt_client.connect(mqtt_topic, mqtt_user, mqtt_password )) {
    Serial.print("\n[+] Connected to MQTT server ");
    Serial.print(mqtt_server);
    Serial.print(":");
    Serial.print(mqtt_port);
    Serial.print(" \"");
    Serial.print(mqtt_topic);
    Serial.print("\".\n");
    return 0;
  }
  else {
    Serial.print("\n[-] Connection to MQTT broker ");
    Serial.print(mqtt_server);
    Serial.print(":");
    Serial.print(mqtt_port);
    Serial.print(" failed with status code: ");
    short broker_response = mqtt_client.state();
    Serial.print(broker_response);
    Serial.print(" (");
    switch (broker_response) {
      case -4:
        Serial.print("MQTT_CONNECTION_TIMEOUT - the server didn't respond within the keepalive time");
        break;
      case -3:
        Serial.print("MQTT_CONNECTION_LOST - the network connection was broken");
        break;
      case -2:
        Serial.print("MQTT_CONNECT_FAILED - the network connection failed");
        break;
      case -1:
        Serial.print("MQTT_DISCONNECTED - the client is disconnected cleanly");
        break;
      case 1:
        Serial.print("MQTT_CONNECT_BAD_PROTOCOL - the server doesn't support the requested version of MQTT");
        break;
      case 2:
        Serial.print("MQTT_CONNECT_BAD_CLIENT_ID - the server rejected the client identifier");
        break;
      case 3:
        Serial.print("MQTT_CONNECT_UNAVAILABLE - the server was unable to accept the connection");
        break;
      case 4:
        Serial.print("MQTT_CONNECT_BAD_CREDENTIALS - the username/password were rejected");
        break;
      case 5:
        Serial.print("MQTT_CONNECT_UNAUTHORIZED - the client was not authorized to connect");
        break;
      default:
        Serial.print("UNKNOWN");
        break;
    }
    Serial.print(")!\n");
  }
  return 1;
}


unsigned char healthCheck(void) {
  /* check connection to WiFi */
  if (WiFi.status() != WL_CONNECTED) {
    return 1; /* no connection to WiFi */
  }
  return 0;
}


double getDistanceCm(double *distance) {
  distance = HCSR04.measureDistanceCm();
  return distance[0];
}


unsigned char sendJsonToMqttBroker(void) {
  StaticJsonDocument<256> json_data;

  /* data */
  json_data["device"] = json_device_name;
  json_data["distance_cm"] = hcsr_value;

  /* prints JSON on the screen */
  Serial.print("    ");
  serializeJson(json_data, Serial);
  Serial.print("\n");

  /* send JSON to MQTT */
  char out[128];
  serializeJson(json_data, out);
  boolean data_sent = mqtt_client.publish(mqtt_topic, out); /* 1 == OK, 0 != OK */
  return !data_sent; /* 0 == OK, 1 != OK */
}

/******************************************************************************/

void setup() {
  Serial.begin(9600); /* initialize serial communication at 9600 bits per second. */
  Serial.print("\n\n-------------------- START --------------------\n");

  exit_status_code = connectToWiFi();
  while (exit_status_code) {
    exit_status_code = connectToWiFi();
  }

  exit_status_code = connectToMqtt();
  while (exit_status_code) {
    delay(5000);
    exit_status_code = connectToMqtt();
  }

  HCSR04.begin(PIN_HCSR04_TRIG, PIN_HCSR04_ECHO);
  Serial.print("[+] Distance sensor HC-SR04 initialized.\n");
}

void loop() {
  hcsr_value = round(getDistanceCm(_hcsr_distances)); /* convert double to int */

  /* handle interruptions */
  exit_status_code = healthCheck();
  switch (exit_status_code) {
    case 1:
      Serial.print("[-] Device has lost connection to WiFi \"");
      Serial.print(wifi_essid);
      Serial.print("\"!\n");
      exit_status_code = connectToWiFi();
      while (exit_status_code) {
        exit_status_code = connectToWiFi();
      }
      exit_status_code = connectToMqtt();
      while (exit_status_code) {
        delay(5000);
        exit_status_code = connectToMqtt();
      }
      break;
    default:
      exit_status_code = sendJsonToMqttBroker();
      if (exit_status_code) {
        Serial.print("[-] JSON data could not be sent to ");
        Serial.print(mqtt_server);
        Serial.print(":");
        Serial.print(mqtt_port);
        Serial.print(" \"");
        Serial.print(mqtt_topic);
        Serial.print("\"!\n");
      }
      else {
        Serial.print("[+] JSON data sent to ");
        Serial.print(mqtt_server);
        Serial.print(":");
        Serial.print(mqtt_port);
        Serial.print(" \"");
        Serial.print(mqtt_topic);
        Serial.print("\".\n");
      }
  }
  delay(json_resend_timeout);
}
