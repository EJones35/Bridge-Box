#!/usr/bin/env python3
"""
Grab Relay screen coords with F8
- Run: python grab_coords.py
- Hover mouse over each EmptyEpsilon button, press F8 to log
- Order: Red (1), Yellow (2), Clear (3), Call FC (0) - press in that order if you can
- Log goes to relay_coords.txt and console - paste that file back to JARVIS
- Press ESC to quit
"""
from pynput import keyboard, mouse
from pathlib import Path

out = Path(__file__).parent / "relay_coords.txt"
coords = []
m = mouse.Controller()

print("=== F8 Grabber ===")
print("Hover over Red Alert -> F8, Yellow -> F8, Clear -> F8, Call FC -> F8")
print("Press ESC to quit\n")

def on_press(key):
    global coords
    try:
        if key == keyboard.Key.f8:
            x, y = m.position
            coords.append((x,y))
            line = f"{len(coords)}: {x},{y}"
            print(line)
            with open(out, "a") as f:
                f.write(line + "\n")
            print(f"  logged -> {out}")
        elif key == keyboard.Key.esc:
            print("\nDone. Paste relay_coords.txt here:")
            print(out.read_text() if out.exists() else "(empty)")
            return False
    except Exception as e:
        print("err", e)

# clear old
if out.exists():
    out.unlink()
print(f"Logging to {out}")

with keyboard.Listener(on_press=on_press) as listener:
    listener.join()
