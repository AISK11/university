#!/usr/bin/env python3

#####################
##     Purpose     ##
#####################
'''
Lights Hue and print message on a display.

Algorithm:
1. initialization of display and Hue
2. listens for incoming hooks from MQTT broker
3. on hook, received data are evaluated
4. according to distance value, display is turned ON/OFF and message is displayed
5. according to distance value, Hue changes color accordingly
'''


#####################
##   Schematics    ##
#####################
'''
1. Philips Hue:
+-----------------------------+       +------------+   +-----------------+
| LED-1 | LED-2 | ... | LED-N |ooooooo| Hue Bridge |---| Wireless Router |
+-----------------------------+       +------------+   +-----------------+
                                                          |
                                                       +-----+
                                                       | RPI |
                                                       +-----+

2. Raspberry Pi 1 Model B+:
                 +---------+
            3.3V | O     O | 5V
IO02 (SDA1, I2C) | O     O | 5V
IO03 (SCL1, I2C) | O     O | GND
                 | O     O |
             GND | O     O |
                 | O     O |
                 | O     O | GND
                 | O     O |
                 | O     O |
                 | O     O | GND
                 | O     O |
                 | O     O |
             GND | O     O |
                 | O     O |
                 | O     O | GND
                 | O     O |
                 | O     O | GND
                 | O     O |
                 | O     O |
             GND | O     O |
                 +-- USB --+

3. Display 2004A + I2C:
GND <=> GND
VCC <=> 5V
SDA <=> IO02
SCL <=> IO03
'''


#####################
##     Set Up      ##
#####################
'''
1. Install MQTT client:
* $(sudo apt install mosquitto-clients)

2. Install dependencies:
* $(sudo apt install -y python3-pip python3-smbus i2c-tools)
* $(python3 -m pip install RPLCD paho-mqtt)

3. Allow I2C:
* $(sudo raspi-config) -> "3 Interface Options" -> "I5 I2C" -> "Yes"

4. Start I2C modules on startup:
* File (/etc/modules)
i2c-bcm2708
i2c-dev

5. Reboot:
* $(reboot)

6. Check if display is detected:
$(sudo i2cdetect -y 1)

7. Generate Hue token:
* http://<HUE-IP>/debug/clip.html
URL:         /api
Mesage Body: {"devicetype":"<dania>#<exam>"}
POST

8. Get Hue data:
* http://<HUE-IP>/debug/clip.html
URL: /api/<HUE-TOKEN>/lights
Mesage Body: {}
GET

9. Curl the data:
- GET:
$(curl -X GET http://<HUE-IP>/api/<HUE-TOKEN>/lights[/<1>])

- PUT on/off toggle:
$(curl -X PUT -d '{"on":true}' http://<HUE-IP>/api/<HUE-TOKEN>/lights/<1>/state)
$(curl -X PUT -d '{"on":false}' http://<HUE-IP>/api/<HUE-TOKEN>/lights/<1>/state)

- Change color:
$(curl -X PUT -d '{"xy":[0.3,0.3]}' http://<HUE-IP>/api/<HUE-TOKEN>/lights/<1>/state)
'''

#####################
##   References    ##
#####################
'''
- Philips Hue:
* Token generation: https://developers.meethue.com/develop/get-started-2/

- RPI:
* GPIO pins: https://www.raspberry-pi-geek.com/howto/GPIO-Pinout-Rasp-Pi-1-Model-B-Rasp-Pi-2-Model-B
* GPIO Display: https://phppot.com/web/guide-to-setup-raspberry-pi-with-lcd-display-using-i2c-backpack/

- Python3 libs:
* ping3: https://pypi.org/project/ping3/
* mqtt: https://pypi.org/project/paho-mqtt/#connect-reconnect-disconnect

- Colors:
* CT colors: https://sites.ecse.rpi.edu/~schubert/Light-Emitting-Diodes-dot-org/chap17/F17-04%20Chromaticity%20diagram.jpg
* Philips colors: https://www.enigmaticdevices.com/philips-hue-lights-popular-xy-color-values/
'''

################################################################################
## Libraries
import threading
import time
import requests ## HTTP lib
from RPLCD import i2c ## Install with: ($python3 -m pip install RPLCD)
import paho.mqtt.client as mqtt ## Install with: ($python3 -m pip install paho-mqtt)
import json

## Config Variables
display_address = 0x27 ## generally 0x27, verify with $(i2cdetect -y 1)
display_x       = 20 ## columns
display_y       = 4  ## rows

hue_host  = "192.168.0.99"
hue_port  = 80
hue_token = "9tqqDGEtt41iiWt4dlHI6ZHmTlvnz2vYa72q5tZa"
hue_led   = 1

mqtt_server    = "public.mqtthq.com"
mqtt_port      = 1883
mqtt_topic     = "garage_sensor"
mqtt_user      = ""
mqtt_password  = ""
mqtt_keepalive = 60 ## exchange ping if no messages received for this time period

colors = {
    "white":  [0.3333,0.3333],
    "red":    [0.675,0.322],
    "blue":   [0.167,0.04],
    "green":  [0.2,0.8],
    "yellow": [0.4325,0.5007],
    "orange": [0.5567,0.4091],
    "purple": [0.2485,0.0917]
}

## Program Variables
display_i2c_expander = "PCF8574"
display_port         = 1 ## 0 on an older Raspberry Pi
display_charmap      = "A00"
lcd = i2c.CharLCD(display_i2c_expander, display_address, port=display_port, charmap=display_charmap, cols=display_x, rows=display_y)

################################################################################

def initDisplay():
    print("[Display] Initializing display (I2C 2004A).")
    lcd.cursor_mode = "hide"

    ## Print initialization message
    lcd.clear()
    lcd.backlight_enabled = True
    lcd.cursor_pos = (1, 0)
    lcd.write_string("Initializing")
    time.sleep(1)
    i = 0
    while i < 3:
        lcd.write_string(".")
        time.sleep(1)
        i += 1
    lcd.clear()
    lcd.backlight_enabled = False


def initHue():
    ## Try to connect
    r = requests.get(f"http://{hue_host}/api/{hue_token}")
    print(f"[Hue] Response from '{r.url}' - {r.status_code}\n'{r.text}'")

    ## Brightness to 100%
    r = requests.put(f"http://{hue_host}/api/{hue_token}/lights/{str(hue_led)}/state", data="{\"bri\": 100}")
    #print(f"[Hue] Response from '{r.url}' - {r.status_code}\n'{r.text}'")

    ## Turn ON
    r = requests.put(f"http://{hue_host}/api/{hue_token}/lights/{str(hue_led)}/state", data="{\"on\": true}")

    ## Change colors
    r = requests.put(f"http://{hue_host}/api/{hue_token}/lights/{str(hue_led)}/state", data="{\"xy\": " + str(colors["white"]) + "}")
    time.sleep(0.5)
    r = requests.put(f"http://{hue_host}/api/{hue_token}/lights/{str(hue_led)}/state", data="{\"xy\": " + str(colors["red"]) + "}")
    time.sleep(0.5)
    r = requests.put(f"http://{hue_host}/api/{hue_token}/lights/{str(hue_led)}/state", data="{\"xy\": " + str(colors["blue"]) + "}")
    time.sleep(0.5)
    r = requests.put(f"http://{hue_host}/api/{hue_token}/lights/{str(hue_led)}/state", data="{\"xy\": " + str(colors["green"]) + "}")
    time.sleep(0.5)
    r = requests.put(f"http://{hue_host}/api/{hue_token}/lights/{str(hue_led)}/state", data="{\"xy\": " + str(colors["yellow"]) + "}")
    time.sleep(0.5)
    r = requests.put(f"http://{hue_host}/api/{hue_token}/lights/{str(hue_led)}/state", data="{\"xy\": " + str(colors["orange"]) + "}")
    time.sleep(0.5)
    r = requests.put(f"http://{hue_host}/api/{hue_token}/lights/{str(hue_led)}/state", data="{\"xy\": " + str(colors["purple"]) + "}")
    time.sleep(0.5)
    r = requests.put(f"http://{hue_host}/api/{hue_token}/lights/{str(hue_led)}/state", data="{\"xy\": " + str(colors["white"]) + "}")
    time.sleep(0.5)

    ## Turn OFF
    r = requests.put(f"http://{hue_host}/api/{hue_token}/lights/{str(hue_led)}/state", data="{\"on\": false}")


def initialize():
    t1 = threading.Thread(target=initDisplay, args=())
    t2 = threading.Thread(target=initHue, args=())
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    mqttInit()


def mqttConnectHook(client, userdata, flags, rc):
    print(f"[MQTT] Connected with result code {str(rc)}.")
    ## Show on Hue
    r = requests.put(f"http://{hue_host}/api/{hue_token}/lights/{str(hue_led)}/state", data="{\"xy\": " + str(colors["yellow"]) + "}")
    ## Print on display
    lcd.clear()
    lcd.backlight_enabled = True
    lcd.cursor_pos = (1, 0)
    lcd.write_string("MQTT connected!")

    client.subscribe(mqtt_topic)
    #client.subscribe("$SYS/#") -## All topics
    print(f"[MQTT] subscribed to topic '{mqtt_topic}'.")
    ## Print on display
    lcd.clear()
    lcd.backlight_enabled = True
    lcd.cursor_pos = (0, 0)
    lcd.write_string("MQTT subscribed -")
    lcd.cursor_pos = (1, 0)
    lcd.write_string(f"{mqtt_server}:{mqtt_port} ")
    lcd.write_string(f"\"{mqtt_topic}\"")
    lcd.cursor_pos = (3, 0)
    lcd.write_string("Waiting for data...")
    ## Show on Hue
    r = requests.put(f"http://{hue_host}/api/{hue_token}/lights/{str(hue_led)}/state", data="{\"xy\": " + str(colors["blue"]) + "}")
    time.sleep(1)

    ## Turn everything off
    r = requests.put(f"http://{hue_host}/api/{hue_token}/lights/{str(hue_led)}/state", data="{\"on\": false}")
    lcd.clear()
    lcd.backlight_enabled = False


def mqttMessageHook(client, userdata, msg):
    message = msg.payload ## OUTPUT in bytes: b'{"device":"ESP32","distance_cm":26}
    message = message.decode('utf-8') ## convert to string
    print(f"[MQTT] Topic '{msg.topic}' = {message}")

    data = json.loads(message) ## convert string to dict
    distance = data["distance_cm"] ## <int>

    ## data evaluation
    '''
    > 200cm:
      Display is OFF
      HUE is OFF
    <= 200cm && > 100cm:
      Display shows distance
      HUE is GREEN
    <= 100cm && > 30cm:
      Display shows distance
      HUE is YELLOW
    <= 30cm:
      Display shows distance
      HUE is RED
    '''
    if distance > 200:
        lcd.clear()
        lcd.backlight_enabled = False
        r = requests.put(f"http://{hue_host}/api/{hue_token}/lights/{str(hue_led)}/state", data="{\"on\": false}")
    elif distance > 100:
        lcd.clear()
        lcd.backlight_enabled = True
        lcd.cursor_pos = (1, 0)
        lcd.write_string(f"{distance} cm")
        r = requests.put(f"http://{hue_host}/api/{hue_token}/lights/{str(hue_led)}/state", data="{\"on\": true}")
        r = requests.put(f"http://{hue_host}/api/{hue_token}/lights/{str(hue_led)}/state", data="{\"xy\": " + str(colors["green"]) + "}")
    elif distance > 30:
        lcd.clear()
        lcd.backlight_enabled = True
        lcd.cursor_pos = (1, 0)
        lcd.write_string(f"{distance} cm")
        r = requests.put(f"http://{hue_host}/api/{hue_token}/lights/{str(hue_led)}/state", data="{\"on\": true}")
        r = requests.put(f"http://{hue_host}/api/{hue_token}/lights/{str(hue_led)}/state", data="{\"xy\": " + str(colors["orange"]) + "}")
    else:
        lcd.clear()
        lcd.backlight_enabled = True
        lcd.cursor_pos = (1, 0)
        lcd.write_string(f"{distance} cm!!!")
        r = requests.put(f"http://{hue_host}/api/{hue_token}/lights/{str(hue_led)}/state", data="{\"on\": true}")
        r = requests.put(f"http://{hue_host}/api/{hue_token}/lights/{str(hue_led)}/state", data="{\"xy\": " + str(colors["red"]) + "}")


def mqttInit():
    print(f"[MQTT] Connecting to MQTT broker...")
    ## Print on display
    lcd.clear()
    lcd.backlight_enabled = True
    lcd.cursor_pos = (1, 0)
    lcd.write_string("Connecting to MQTT...")
    ## Show on Hue
    r = requests.put(f"http://{hue_host}/api/{hue_token}/lights/{str(hue_led)}/state", data="{\"on\": true}")
    r = requests.put(f"http://{hue_host}/api/{hue_token}/lights/{str(hue_led)}/state", data="{\"xy\": " + str(colors["orange"]) + "}")

    mqtt_client = mqtt.Client()
    mqtt_client.on_connect = mqttConnectHook
    mqtt_client.on_message = mqttMessageHook
    mqtt_client.connect(mqtt_server, mqtt_port, mqtt_keepalive)
    mqtt_client.loop_forever()

################################################################################

def main():
    initialize()

if __name__ == "__main__":
    main()
