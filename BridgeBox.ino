// Bridge Box Mk1 - Button Heavy + OLED + Joystick + Encoder + Keypad
// Uses U8g2 (works on your 0x3C SSD1306) - not Adafruit (was noisy)
// Board: Uno CH340 COM3
// Wiring: OLED GND/VCC SDA:A4 SCL:A5 | Joystick A0/A1/D2 | Encoder D3/D4/D5 | Keypad D6-D13

#include <Wire.h>
#include <U8g2lib.h>
#include <Keypad.h>

U8G2_SSD1306_128X64_NONAME_1_HW_I2C u8g2(U8G2_R0, U8X8_PIN_NONE);

// Joystick
const int JOY_X = A0;
const int JOY_Y = A1;
const int JOY_SW = 2;

// Encoder KY-040
const int ENC_CLK = 3;
const int ENC_DT  = 4;
const int ENC_SW  = 5;

// Keypad 4x4
const byte ROWS = 4, COLS = 4;
char keys[ROWS][COLS] = {
  {'*','0','#','D'},
  {'7','8','9','C'},
  {'4','5','6','B'},
  {'1','2','3','A'}
};
byte rowPins[ROWS] = {6,7,8,9};
byte colPins[COLS] = {10,11,12,13};
Keypad keypad = Keypad(makeKeymap(keys), rowPins, colPins, ROWS, COLS);

// Modes - only Helm + Relay for today's mission
const char* MODES[] = {"RELAY", "HELM"};
const int MODE_COUNT = 2;
int modeIdx = 0;
String lastKey = "-";
String lastAction = "Ready";
int encPos = 0;
int lastEncPos = 0;
int lastCLK = HIGH;
unsigned long lastEncTime = 0, lastJoySend = 0, helpUntil = 0;
bool displayHelp = false;
bool helmSpeedEnabled = true;
bool helmTurnEnabled = true;

void setup() {
  Serial.begin(115200);
  pinMode(JOY_SW, INPUT_PULLUP);
  pinMode(ENC_CLK, INPUT_PULLUP);
  pinMode(ENC_DT, INPUT_PULLUP);
  pinMode(ENC_SW, INPUT_PULLUP);
  lastCLK = digitalRead(ENC_CLK);
  u8g2.begin();
  drawMain();
  Serial.print("M:"); Serial.println(MODES[modeIdx]);
  Serial.println("BridgeBox Ready U8G2 - 115200");
}

void loop() {
  char k = keypad.getKey();
  if (k) {
    lastKey = String(k);
    // Helm thrust/turn toggles - 9 and C
    if (modeIdx==1 && k=='9') { // HELM is index 1 now (RELAY 0, HELM 1)
      helmSpeedEnabled = !helmSpeedEnabled;
      lastAction = helmSpeedEnabled ? "Thrust ON" : "Thrust OFF";
      Serial.print("K:"); Serial.println(k);
      drawMain(); return;
    }
    if (modeIdx==1 && k=='C') {
      helmTurnEnabled = !helmTurnEnabled;
      lastAction = helmTurnEnabled ? "Turn ON" : "Turn OFF";
      Serial.print("K:"); Serial.println(k);
      drawMain(); return;
    }
    if (k == 'D') {
      cycleMode();
    } else if (k == '#') {
      displayHelp = !displayHelp;
      helpUntil = millis() + 4000;
      lastAction = displayHelp ? "Help ON" : "Help OFF";
      Serial.println("K:#");
    } else {
      Serial.print("K:"); Serial.println(k);
      lastAction = String("Key ") + k;
      if (displayHelp) helpUntil = millis() + 4000;
    }
    drawMain();
  }

  int clk = digitalRead(ENC_CLK);
  if (clk != lastCLK) {
    if (digitalRead(ENC_DT) != clk) encPos++; else encPos--;
    if (millis() - lastEncTime > 30) {
      int diff = encPos - lastEncPos;
      if (diff != 0) {
        Serial.print("E:"); Serial.println(diff);
        lastEncPos = encPos;
        lastAction = String("Enc ") + (diff>0?"+":"") + diff;
        lastEncTime = millis();
        drawMain();
      }
    }
  }
  lastCLK = clk;

  static unsigned long encDown = 0; static bool encWasDown=false;
  if (digitalRead(ENC_SW)==LOW && !encWasDown){ encDown=millis(); encWasDown=true; }
  if (digitalRead(ENC_SW)==HIGH && encWasDown){
    encWasDown=false;
    if (millis()-encDown < 600){ cycleMode(); Serial.println("E:BTN"); lastAction="Enc Click"; drawMain(); }
  }

  // Ghost-joystick filter - ignore floating A0/A1 until a real stick is seen centred
  static bool hasJoystick = false;
  static int stableCount = 0;
  int x = analogRead(JOY_X), y = analogRead(JOY_Y);
  bool joyBtn = digitalRead(JOY_SW)==LOW;
  static int lastX=512, lastY=512; static bool lastJoyBtn=false;
  if (!hasJoystick) {
    // look for centred stick (400-624) for 10 consecutive loops
    if (x>400 && x<624 && y>400 && y<624) stableCount++; else stableCount=0;
    if (stableCount>10) hasJoystick=true;
  }
  if (hasJoystick) {
    if (hasJoystick && millis() - lastJoySend > 50) {
      // always stream while joystick is armed - so centre releases held keys on Python side
      Serial.print("J:"); Serial.print(x); Serial.print(","); Serial.print(y); Serial.print(","); Serial.println(joyBtn?1:0);
      lastX=x; lastY=y; lastJoySend=millis();
      bool moved = abs(x-512)>80 || abs(y-512)>80;
      lastAction = moved ? (joyBtn ? "Joy BTN" : "Joy Move") : "Ready";
      drawMain();
    } else if (!hasJoystick && millis() - lastJoySend > 100) {
      // quiet until armed - don't spam
    }
    if (joyBtn != lastJoyBtn){
      if (joyBtn){ Serial.println("J:BTN"); lastAction="Joy Click"; drawMain(); }
      lastJoyBtn=joyBtn;
    }
  } else {
    // keep joystick pins quiet until you plug it - show Ready, not Joy Move
    lastJoyBtn = joyBtn;
  }
  if (displayHelp && millis() > helpUntil){ displayHelp=false; drawMain(); }
}

void cycleMode(){
  modeIdx = (modeIdx+1)%MODE_COUNT;
  Serial.print("M:"); Serial.println(MODES[modeIdx]);
  lastAction = String(MODES[modeIdx]);
  displayHelp=true; helpUntil=millis()+3000;
}

const int XOFF = 6;
void drawMain(){
  u8g2.firstPage();
  do{
    u8g2.setFont(u8g2_font_6x10_tr);
    u8g2.drawStr(XOFF,10,"MODE:");
    u8g2.setFont(u8g2_font_7x13B_tr);
    u8g2.drawStr(XOFF,26,MODES[modeIdx]);
    u8g2.setFont(u8g2_font_6x10_tr);
    u8g2.drawStr(80+XOFF,26,lastKey.c_str());
    u8g2.drawLine(XOFF,30,124,30);
    if(displayHelp){
      drawHelpInner();
    } else {
      u8g2.drawStr(XOFF,42, ("Last: "+lastAction).c_str());
      if(modeIdx==1){ // HELM - show thrust/turn locks
        char buf[32]; snprintf(buf,sizeof(buf),"Thr:%s Tur:%s", helmSpeedEnabled?"ON":"OFF", helmTurnEnabled?"ON":"OFF");
        u8g2.drawStr(XOFF,54,buf);
        u8g2.drawStr(XOFF,62,"9:Thr C:Turn D:Mode");
      } else {
        char buf[20]; snprintf(buf,sizeof(buf),"Enc:%d",encPos);
        u8g2.drawStr(XOFF,54,buf);
        u8g2.drawStr(XOFF,62,"Relay D=Mode");
      }
    }
  } while(u8g2.nextPage());
}
void drawHelpInner(){
  if(modeIdx==0){ // RELAY
    u8g2.drawStr(XOFF,42,"1:RED 2:YEL 3:Reset");
    u8g2.drawStr(XOFF,52,"0:CallFC A:Hold");
    u8g2.drawStr(XOFF,62,"D:Mode");
  } else { // HELM
    u8g2.drawStr(XOFF,42,"Joy:Steer+Thrust");
    u8g2.drawStr(XOFF,52,"9:Thr  C:Turn 0:Dock");
    u8g2.drawStr(XOFF,62,"Click:Imp/Warp D:Mode");
  }
}
