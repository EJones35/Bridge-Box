# Bridge Box
## A spaceship console run by an Arduino Uno and Python

### Building
To build it, get a `OLED 0.96" SSD1306` for the screen, a 4x4 keypad, a joystick, a breadboard and an Arduino Uno.

Connect the wires as stated in `Wiring.md`.

If you want these components all from one place, buy the 30 days in space kit from `https://craftingtable.com/products/adventure-kit-30-days-lost-in-space`.

Replace your `keybindings.json` with the one in this repo for the correct control scheme.

### Running
To run it, connect the Arduino to port COM3 of your device and run `bridge_box.py`.

The screen coordinates for EmptyEpsilon are in `helm_coords.txt` and `relay_coords.txt`.

You can run `grab_coords.py` to redo the locations of the buttons.

### Controls
#### Helm
##### Impulse
**1** - Sets impulse to 0%
**2** - Sets impulse to 25%
**3** - Sets impulse to 50%
**A** - Sets impulse to 75%
**4** - Sets impulse to 100%

**\*+2** - Sets impulse to -25%
**\*+3** - Sets impulse to -50%
**\*+4** - Sets impulse to -75%
**\*+5** - Sets impulse to -100%

##### Warp
**5** - Sets warp to level 0
**6** - Sets warp to level 1
**B** - Sets warp to level 2
**7** - Sets warp to level 3
**8** - Sets warp to level 4

##### Turning
**Joystick left** - Turns the ship left
**Joystick right** - Turns the ship right

##### QOL Controls
**9** - Toggles if the joystick contols the speed of the ship
**C** - Toggles if the joystick contols the turning of the ship

#### Relay
##### Alerts
**1** - Red alert
**2** - Yellow alert
**3** - Clear alert

##### Mouse
**Joystick move** - Move mouse
**Joystick click** - Left click
**A** - Toggle mouse hold (helpful in moving waypoints/the map)

##### Custom
**0** - Call Flight Controller
