# Bridge Box Mk1 - Wiring Map (Button Heavy)

For SXP 30 Aug 2:30pm - Uno + OLED + Joystick + 1x Encoder + 4x4 Keypad
All on ONE breadboard. One Uno is enough. Second Uno stays spare.

## Power Rails
- Breadboard red rail -> Arduino 5V
- Breadboard blue rail -> Arduino GND
- OLED VCC -> 5V (if your OLED says 3.3V only, use 3.3V instead)
- Joystick +5V -> 5V, GND -> GND
- Encoder + -> 5V, GND -> GND

## OLED 0.96" SSD1306 4-pin (I2C)
- GND -> GND rail
- VCC -> 5V (or 3.3V)
- SCL -> A5
- SDA -> A4

## Joystick (360 + click)
- GND -> GND rail
- +5V -> 5V rail
- VRx -> A0
- VRy -> A1
- SW -> D2

## Rotary Encoder KY-040 (use ONE for now, second stays in bag)
- GND -> GND rail
- + -> 5V rail
- CLK -> D3
- DT -> D4
- SW -> D5

## 4x4 Membrane Keypad (8 wires)
Rows (4 wires on left side of keypad):
- R1 -> D6
- R2 -> D7
- R3 -> D8
- R4 -> D9
Cols (4 wires on right side):
- C1 -> D10
- C2 -> D11
- C3 -> D12
- C4 -> D13

## Breadboard layout tip
- Put OLED top-left, joystick bottom-left, encoder bottom-right, keypad sticking off the side (its ribbon doesn't need breadboard holes - just jumper wires to D6-D13)
- Keep wires short. Common ground is the blue rail.

## Libraries to install in Arduino IDE:
Sketch -> Include Library -> Manage Libraries -> install:
- Adafruit GFX Library
- Adafruit SSD1306
- Keypad by Mark Stanley (or Keypad by Community)

Then open BridgeBox.ino -> Tools -> Board: Arduino Uno -> Port: COM? -> Upload
Open Serial Monitor at 115200 to test - you should see M:CAPTAIN, K:1, E:+1 etc
OLED should show MODE: CAPTAIN and help.

## Python bridge on laptop:
```
pip install pyserial pynput
python C:\Users\ethan\Coding\Python\BridgeBox\bridge_box.py
```
Keep EmptyEpsilon window focused when you press keys - Python sends keys there.

## Mode & Help
- Press D on keypad OR click the encoder to cycle CAPTAIN -> RELAY -> HELM
- Press # to toggle help screen on OLED (shows what each button does)
- OLED always shows MODE + last key + Enc pos

## Second encoder
Leave it out for tomorrow to save pins. After the mission we add it back with a shield or second Uno via serial.

## Test tonight
1. Upload sketch, check OLED says CAPTAIN
2. Run bridge_box.py, press 1-9 - see keys in console
3. Edit MAPPINGS in bridge_box.py to match what SXP EmptyEpsilon actually wants (change 'h','r','f1' etc)
4. Launch EmptyEpsilon client offline - test joystick moves heading and keypad fires hail/relay
