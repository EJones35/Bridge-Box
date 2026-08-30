#!/usr/bin/env python3
"""
Bridge Box Mk1 - Python bridge for SXP EmptyEpsilon - Sun 30 Aug 14:30
Handles per-station mappings from your 30 Aug scheme.

- Relay: 1 Red,2 Yellow,3 Clear,0 Call FC -> mouse clicks at recorded coords (save/move/click/restore)
- Weapons: 1 2 3 A load, 4 5 6 B fire, 0 change weapon, 5 shields,6/7 beam freq,8/9 shield freq, C calibrate
- Helm: joystick Y forward/back = speed, X = turn, click = impulse/warp toggle, 0 = dock
- Captain/Science/Engineering: joystick = mouse, 2 left click,3 right click

Relay coords: run grab_coords.py, press F8 over each button, paste relay_coords.txt
"""
import serial, serial.tools.list_ports, time, pathlib, sys
from pynput.keyboard import Controller as KCtrl, Key
from pynput.mouse import Controller as MCtrl, Button

kb = KCtrl()
mouse = MCtrl()

# --- Relay click locations - fill after F8 grabs ---
# Format: "1": (x,y), "2": (x,y), "3": (x,y), "0": (x,y)
# Leave as None until you grab - then paste from relay_coords.txt
RELAY_COORDS = {
    "1": None,  # Red
    "2": None,  # Yellow
    "3": None,  # Clear
    "0": None,  # Call FC
}

# Try auto-load from relay_coords.txt - your 30 Aug grab: 1 Red,2 Yellow,3 None,4 CallFC,5 AlertLevel
coord_file = pathlib.Path(__file__).parent / "relay_coords.txt"
if coord_file.exists():
    try:
        lines=[l.strip() for l in coord_file.read_text().splitlines() if "," in l]
        vals=[]
        for l in lines:
            part=l.split(":")[-1].strip()
            x,y=part.split(",")
            vals.append((int(x.strip()), int(y.strip())))
        if len(vals)>=5:
            RELAY_COORDS["1"], RELAY_COORDS["2"], RELAY_COORDS["3"], RELAY_COORDS["0"] = vals[0], vals[1], vals[2], vals[3]
            RELAY_COORDS["5"] = vals[4]  # Alert Level menu
            print(f"Loaded Relay coords 5-pt from {coord_file}: {RELAY_COORDS}")
        elif len(vals)>=4:
            RELAY_COORDS["1"], RELAY_COORDS["2"], RELAY_COORDS["3"], RELAY_COORDS["0"] = vals[0], vals[1], vals[2], vals[3]
            print(f"Loaded Relay coords from {coord_file}: {RELAY_COORDS}")
    except Exception as e:
        print(f"relay_coords parse fail: {e}")

# Helm impulse slider - your 30 Aug grab: 0,25,50,75,100,-25,-50,-75,-100,warp1-4 + extra
HELM_IMPULSE_COORDS={}
helm_file = pathlib.Path(__file__).parent / "helm_coords.txt"
if helm_file.exists():
    try:
        lines=[l.strip() for l in helm_file.read_text().splitlines() if "," in l]
        vals=[]
        for l in lines:
            part=l.split(":")[-1].strip()
            x,y=part.split(",")
            vals.append((int(x.strip()), int(y.strip())))
        # order you logged: 0,25,50,75,100,-25,-50,-75,-100,warp1,2,3,4,(extra)
        if len(vals)>=5:
            HELM_IMPULSE_COORDS["1"]=vals[0]  # 0%
            HELM_IMPULSE_COORDS["2"]=vals[1]  # 25%
            HELM_IMPULSE_COORDS["3"]=vals[2]  # 50%
            HELM_IMPULSE_COORDS["A"]=vals[3]  # 75%
            HELM_IMPULSE_COORDS["4"]=vals[4]  # 100%
            print(f"Loaded Helm impulse coords from {helm_file}: {HELM_IMPULSE_COORDS}")
        if len(vals)>=9:
            # negative -25,-50,-75,-100 are vals 5-8 (0-index 5-8)
            HELM_IMPULSE_NEG={}
            HELM_IMPULSE_NEG["2"]=vals[5]  # -25
            HELM_IMPULSE_NEG["3"]=vals[6]  # -50
            HELM_IMPULSE_NEG["A"]=vals[7]  # -75
            HELM_IMPULSE_NEG["4"]=vals[8]  # -100
            # stash globally
            globals()["HELM_IMPULSE_NEG"]=HELM_IMPULSE_NEG
            print(f"Loaded Helm NEG impulse {HELM_IMPULSE_NEG}")
        if len(vals)>=13:
            print(f"Helm full grab has {len(vals)} points (neg impulse + warp also logged)")
    except Exception as e:
        print(f"helm_coords parse fail: {e}")
else:
    HELM_IMPULSE_COORDS={}
    HELM_IMPULSE_NEG={}

def find_port():
    for p in serial.tools.list_ports.comports():
        if "Arduino" in p.description or "CH340" in p.description or "USB" in p.description:
            return p.device
    ports=list(serial.tools.list_ports.comports())
    return ports[0].device if ports else None

def press_key(name):
    named={'enter':Key.enter,'space':Key.space,'up':Key.up,'down':Key.down,'left':Key.left,'right':Key.right,'esc':Key.esc,'tab':Key.tab, 'shift':Key.shift, 'ctrl':Key.ctrl}
    if name.lower() in named:
        k=named[name.lower()]; kb.press(k); kb.release(k)
    elif name.lower().startswith('f') and name[1:].isdigit():
        try:
            k=getattr(Key, name.lower()); kb.press(k); kb.release(k)
        except: kb.press(name); kb.release(name)
    else:
        kb.press(name); kb.release(name)
    print(f"  key {name}")

def click_at(coord):
    if coord is None:
        print("  no coord - run grab_coords.py first")
        return
    ox, oy = mouse.position
    x,y = coord
    mouse.position = (x,y)
    time.sleep(0.03)
    mouse.click(Button.left, 1)
    time.sleep(0.03)
    mouse.position = (ox, oy)
    print(f"  click {x},{y} -> restore {ox},{oy}")

# Weapons keymap - per your scheme 30 Aug
# Note: 5/6 double-booked (Fire vs Shields/Beam) - Fire takes priority for now, Shields on * ?
WEAPONS_MAP = {
    '1': '1', '2': '2', '3': '3', 'A': 'a',  # load
    '4': '4', '5': '5', '6': '6', 'B': 'b',  # fire
    '0': 'o',  # change weapon
    '7': '7', '8': '8', '9': '9', 'C': 'c',
    # 5 shields etc overlap - map * to shields for now to avoid clash
    '*': '5', '#': '6', 'D': 'd',
}

current_mode="CAPTAIN"  # default, will follow Arduino M: messages

# Keep last mouse for joystick-as-mouse
JOY_MOUSE_SENS = 0.08  # finer, less jump
mouse_held = False
helm_held = set()
helm_warp = False  # Helm click toggles Impulse (False) vs Warp (True)
helm_warp_level = 0  # 0..4 -> 6,7,8,9,0
helm_warp_fwd_held = False
helm_warp_back_held = False
helm_star_held = False
helm_speed_enabled = True
helm_turn_enabled = True
HELM_IMPULSE_NEG={}

def handle_line(line):
    global current_mode, mouse_held, helm_held, helm_warp, helm_warp_level, helm_warp_fwd_held, helm_warp_back_held, helm_star_held, HELM_IMPULSE_NEG, helm_speed_enabled, helm_turn_enabled
    line=line.strip()
    if not line: return
    print(f"< {line}")
    if line.startswith("M:"):
        new_mode=line[2:].strip()
        # release helm holds when leaving HELM
        if current_mode=="HELM" and new_mode!="HELM":
            for k in list(helm_held):
                try:
                    key={"up":Key.up,"down":Key.down,"left":Key.left,"right":Key.right,"8":'8',"6":'6'}[k]
                    if isinstance(key, Key): kb.release(key)
                    else: kb.release(key)
                    print(f"Helm release {k} on mode change")
                except: pass
            helm_held.clear()
        current_mode=new_mode
        print(f"== MODE {current_mode} ==")
        # swap EE station - only Relay/Helm now
        station_keys={"RELAY":Key.f6,"HELM":Key.f2}
        if new_mode in station_keys:
            k=station_keys[new_mode]
            kb.press(k); kb.release(k)
            print(f"  -> EE station {new_mode} ({k})")
        return
    if line.startswith("K:"):
        k=line[2:].strip()
        # A = hold mouse down (toggle) in mouse modes - joystick click stays normal click
        if k=="A" and current_mode in ("RELAY","SCIENCE","ENGINEERING","CAPTAIN"):
            if not mouse_held:
                mouse.press(Button.left)
                mouse_held = True
                print("A -> mouse HOLD down")
            else:
                mouse.release(Button.left)
                mouse_held = False
                print("A -> mouse RELEASE")
            return
        # Relay: 1 Red,2 Yellow,3 Reset,0 CallFC - 5 is menu opener internally only
        if current_mode=="RELAY":
            if k=="5":
                print("Relay 5 ignored - use 1/2/3")
                return
            if k in ("1","2","3"):
                # need Alert Level menu first, then the level
                lvl = {"1":"Red","2":"Yellow","3":"Reset"}[k]
                print(f"Relay {k} -> Alert Menu + {lvl}")
                click_at(RELAY_COORDS["5"])
                time.sleep(0.10)
                click_at(RELAY_COORDS[k])
                return
            if k in RELAY_COORDS and RELAY_COORDS[k] is not None:
                print(f"Relay {k} -> click")
                click_at(RELAY_COORDS[k])
            else:
                print(f"Relay {k} no mapping")
        elif current_mode=="WEAPONS":
            # map weapons keys
            # handle shields etc: 5->shields but also fire 5 - prioritize fire for 4/5/6/B, shields on * fallback
            key=WEAPONS_MAP.get(k)
            if key:
                print(f"Weapons {k} -> {key}")
                press_key(key)
        elif current_mode=="CAPTAIN":
            if k=='2': mouse.click(Button.left,1); print("Captain left click")
            elif k=='3': mouse.click(Button.right,1); print("Captain right click")
            else: print(f"Captain {k} ignored (joystick is mouse)")
        elif current_mode=="HELM":
            # Toggle speed/turn
            if k=='9':
                helm_speed_enabled = not helm_speed_enabled
                print(f"Helm speed {'ON' if helm_speed_enabled else 'OFF'}")
                return
            if k=='C':
                helm_turn_enabled = not helm_turn_enabled
                print(f"Helm turn {'ON' if helm_turn_enabled else 'OFF'}")
                return
            # * hold for -impulse
            if k=='*':
                helm_star_held = True
                print("Helm * held - next 2/3/A/4 will be NEG")
                return
            # Discrete levels - impulse via slider clicks, *+key for negative
            if k in ('1','2','3','A','4'):
                if helm_star_held and k in HELM_IMPULSE_NEG:
                    coord=HELM_IMPULSE_NEG.get(k)
                    if coord:
                        click_at(coord); print(f"Helm impulse *+{k} -> NEG click {coord}")
                    helm_star_held=False
                    return
                if helm_star_held and k=='1':
                    helm_star_held=False
                coord=HELM_IMPULSE_COORDS.get(k)
                if coord:
                    click_at(coord); print(f"Helm impulse {k} -> click {coord} ({'0% 25% 50% 75% 100%'.split()[('1','2','3','A','4').index(k)]})")
                else:
                    press_key(k); print(f"Helm impulse {k} fallback key")
                helm_star_held=False
                return
            if k in ('5','6','B','7','8'):
                warp_map={'5':'6','6':'7','B':'8','7':'9','8':'0'}
                wk=warp_map[k]
                try: helm_warp_level = ['6','7','8','9','0'].index(wk)
                except: pass
                press_key(wk); print(f"Helm warp {k} -> {wk} (level {helm_warp_level})")
                return
            if k=='0': press_key('d'); print("Helm dock")
            else: print(f"Helm key {k} ignored")
        elif current_mode in ("SCIENCE","ENGINEERING"):
            print(f"{current_mode} key {k} ignored - joystick is mouse")
        else:
            # generic fallback
            if k in ("1","2","3","0") and current_mode=="RELAY":
                click_at(RELAY_COORDS.get(k))
        return
    if line.startswith("E:"):
        v=line[2:].strip()
        if v=="BTN":
            print("Enc click -> mode cycle already on Arduino")
        else:
            try:
                diff=int(v)
                if current_mode=="HELM":
                    # Helm encoder could be throttle fine tune
                    key='w' if diff>0 else 's'
                    for _ in range(abs(diff)): press_key(key)
                elif current_mode=="WEAPONS":
                    # beam/shield freq
                    key='6' if diff>0 else '7'
                    for _ in range(abs(diff)): press_key(key)
            except: pass
        return
    if line.startswith("J:"):
        if line=="J:BTN":
            # joystick click
            if current_mode in ("RELAY","SCIENCE","ENGINEERING","CAPTAIN"):
                mouse.click(Button.left,1); print("Joy click -> left click")
            elif current_mode=="HELM":
                helm_warp = not helm_warp
                mode = "WARP" if helm_warp else "IMPULSE"
                print(f"Helm click -> toggle to {mode}")
                # quick feedback - tap space to stop current
                # OLED won't show warp/impulse yet - watch console for mode
                # Next forward/back will use the new mode
            return
        parts=line[2:].split(",")
        if len(parts)==3:
            try:
                x,y,b=int(parts[0]), int(parts[1]), int(parts[2])
                dx, dy = x-512, y-512
                if current_mode in ("RELAY","SCIENCE","ENGINEERING","CAPTAIN"):
                    # mouse mode - smoother: smaller steps, more frequent - click handled via J:BTN only, not here
                    mx = int(dx * JOY_MOUSE_SENS)
                    my = int(dy * JOY_MOUSE_SENS)
                    if abs(mx)>0 or abs(my)>0:
                        steps = max(1, max(abs(mx), abs(my)) // 12)
                        ox, oy = mouse.position
                        for _ in range(steps):
                            ox += mx // steps
                            oy += my // steps
                            mouse.position = (ox, oy)
                            time.sleep(0.004)
                    # no click here - J:BTN handles single click on press edge only
                elif current_mode=="HELM":
                    # Helm - HOLD keys while stick deflected - warp vs impulse toggled by click - with speed/turn toggles
                    if helm_speed_enabled:
                        if not helm_warp:  # Impulse
                            if y < 380:
                                if 'up' not in helm_held: kb.press(Key.up); helm_held.add('up'); print("Helm hold Up (Impulse)")
                                if 'down' in helm_held: kb.release(Key.down); helm_held.discard('down')
                                if '8' in helm_held: kb.release('8'); helm_held.discard('8')
                                if '6' in helm_held: kb.release('6'); helm_held.discard('6')
                            elif y > 650:
                                if 'down' not in helm_held: kb.press(Key.down); helm_held.add('down'); print("Helm hold Down (Impulse)")
                                if 'up' in helm_held: kb.release(Key.up); helm_held.discard('up')
                                if '8' in helm_held: kb.release('8'); helm_held.discard('8')
                                if '6' in helm_held: kb.release('6'); helm_held.discard('6')
                            else:
                                if 'up' in helm_held: kb.release(Key.up); helm_held.discard('up'); print("Helm release Up")
                                if 'down' in helm_held: kb.release(Key.down); helm_held.discard('down'); print("Helm release Down")
                                if '8' in helm_held: kb.release('8'); helm_held.discard('8')
                                if '6' in helm_held: kb.release('6'); helm_held.discard('6')
                        else:  # Warp - step 0..4 via 6,7,8,9,0 per keybindings.json
                            warp_keys = ['6','7','8','9','0']  # 0->6, 1->7, 2->8, 3->9, 4->0
                            if y < 380:
                                if not helm_warp_fwd_held and helm_warp_level < 4:
                                    helm_warp_level += 1
                                    k = warp_keys[helm_warp_level]
                                    press_key(k); print(f"Helm Warp up -> {helm_warp_level} ({k})")
                                helm_warp_fwd_held = True
                                helm_warp_back_held = False
                                if 'up' in helm_held: kb.release(Key.up); helm_held.discard('up')
                                if 'down' in helm_held: kb.release(Key.down); helm_held.discard('down')
                            elif y > 650:
                                if not helm_warp_back_held and helm_warp_level > 0:
                                    helm_warp_level -= 1
                                    k = warp_keys[helm_warp_level]
                                    press_key(k); print(f"Helm Warp down -> {helm_warp_level} ({k})")
                                helm_warp_fwd_held = False
                                helm_warp_back_held = True
                                if 'up' in helm_held: kb.release(Key.up); helm_held.discard('up')
                                if 'down' in helm_held: kb.release(Key.down); helm_held.discard('down')
                            else:
                                helm_warp_fwd_held = False
                                helm_warp_back_held = False
                                if 'up' in helm_held: kb.release(Key.up); helm_held.discard('up')
                                if 'down' in helm_held: kb.release(Key.down); helm_held.discard('down')
                                if '8' in helm_held: kb.release('8'); helm_held.discard('8')
                                if '6' in helm_held: kb.release('6'); helm_held.discard('6')
                    else:
                        # speed disabled - ensure no speed keys held
                        for k in ['up','down','8','6']:
                            if k in helm_held:
                                try: kb.release(Key.up if k=='up' else Key.down if k=='down' else k)
                                except: pass
                                helm_held.discard(k)
                        helm_warp_fwd_held=False; helm_warp_back_held=False
                    # turn left/right - check toggle
                    if helm_turn_enabled:
                        if x < 380:
                            if 'left' not in helm_held: kb.press(Key.left); helm_held.add('left'); print("Helm hold Left")
                            if 'right' in helm_held: kb.release(Key.right); helm_held.discard('right')
                        elif x > 650:
                            if 'right' not in helm_held: kb.press(Key.right); helm_held.add('right'); print("Helm hold Right")
                            if 'left' in helm_held: kb.release(Key.left); helm_held.discard('left')
                        else:
                            if 'left' in helm_held: kb.release(Key.left); helm_held.discard('left'); print("Helm release Left")
                            if 'right' in helm_held: kb.release(Key.right); helm_held.discard('right'); print("Helm release Right")
                    else:
                        if 'left' in helm_held: kb.release(Key.left); helm_held.discard('left'); print("Helm turn OFF - release Left")
                        if 'right' in helm_held: kb.release(Key.right); helm_held.discard('right'); print("Helm turn OFF - release Right")
                    return  # don't do the generic mouse move below
                elif current_mode=="WEAPONS":
                    pass
            except Exception as e: print(e)

def main():
    port=find_port()
    if not port:
        print("No port"); return
    print(f"Opening {port} 115200  mode {current_mode}")
    if any(v is None for v in RELAY_COORDS.values()):
        print("Relay coords not set - run grab_coords.py first or 1/2/3/0 will do nothing")
    ser=serial.Serial(port,115200,timeout=0.1)
    time.sleep(2); ser.reset_input_buffer()
    print("Ready - focus EmptyEpsilon. Use D or encoder click to cycle CAPTAIN->RELAY->HELM->WEAPONS->SCIENCE->ENGINEERING")
    try:
        while True:
            if ser.in_waiting:
                for l in ser.readline().decode(errors='ignore').splitlines():
                    handle_line(l)
            time.sleep(0.01)
    except KeyboardInterrupt:
        ser.close()

if __name__=="__main__":
    main()
