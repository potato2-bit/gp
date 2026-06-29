/* ============================================================================
 *  bench_cleaner.ino  —  Solar-AWH PV-Cleaning Robot, bench prototype firmware
 *  Author: Rahma Hesham El-Hamouly (ID 202000434) · REE · Zewail City
 *  Target: ESP32 DevKit 30-pin · Arduino-ESP32 core 3.x
 *
 *  DRIVER MAP  (the locked layout)
 *    H-BRIDGE  = Board #1 (dual L298N):  ch A -> Rail motor L (Motor A) ,  ch B -> Rail motor R (Motor B)
 *      -> each rail motor on its OWN channel/outputs. Firmware drives both together, but
 *         REVERSES ch B (RAIL_R_REVERSED) so the two motors — which face each other — move as ONE.
 *    OTHER     = Board #2 (dual L298N):  ch A -> Brush         ,  ch B -> Pump
 *    Rails are bidirectional (sweep). Brush & pump spin one way: their IN pins are
 *    hardwired (HIGH/LOW) on Board #2, ESP32 controls only their EN (speed).
 *
 *  SERIAL COMMANDS (115200, line ending = Newline):
 *    rN  rail speed | bN brush speed | pN pump speed   (N=0..255, e.g. r120)
 *    f / v  rails forward / reverse   |  x  rails stop
 *    m  brush on/off  |  w  pump on/off  |  g  auto sweep  |  s  STOP all
 *
 *  ===== EVERY WIRE (read with the wiring tables in chat) =====
 *  Board #1 (H-bridge) -> ESP32:  ENA=25 IN1=26 IN2=27 | ENB=14 IN3=16 IN4=17
 *    OUT1/OUT2 -> Rail motor L (Motor A) ;  OUT3/OUT4 -> Rail motor R (Motor B)
 *  Board #2 (other)    -> ESP32:  chA EN=23 (IN1->5V,IN2->GND) ; chB EN=22 (IN3->5V,IN4->GND)
 *    chA OUT1/OUT2 -> Brush ;  chB OUT3/OUT4 -> Pump(red/black)
 *  Encoder (Rail L motor): A=32 B=33 Vcc=3V3 GND=common
 *  Limits: LIM_L NO=18 , LIM_R NO=19 (COM->GND)         Current: ACS712 OUT->/2->34
 *  Humidity: DHT22/AM2302 DATA=4  (Vcc->3V3, GND->common; bare sensor: 4.7k pull-up DATA->3V3)
 *  Both boards: remove the two EN jumpers, KEEP the onboard 5V-regulator jumper.
 *  POWER: 12V(+)->ACS712 Ip+ ; Ip- -> both VS + buck IN ; buck 5V -> ESP32 5V + ACS712 VCC
 *  ALL grounds common.
 * ==========================================================================*/

#include <DHT.h>            // install: Adafruit "DHT sensor library" + "Adafruit Unified Sensor"

// -------- CALIBRATION --------
const float RAIL_TRAVEL_MM  = 900.0;
long  TICKS_PER_TRAVEL      = 0;          // printed on first auto sweep
const float PUMP_FLOW_MLPS  = 6.0;
const float COUPON_LEN_MM   = 900.0;
const float COUPON_WIDTH_MM = 250.0;
const float DOSE_L_PER_M2   = 0.3;

// -------- SPEEDS (live over serial) --------
int DRIVE_DUTY = 130, BRUSH_DUTY = 220, PUMP_DUTY = 200;
int NUM_PASSES = 2;
const int PAUSE_MS = 400;

#define INVERT_DRIVE    0
#define INVERT_ENCODER  0
#define RAIL_R_REVERSED 1   // Motor B faces Motor A -> reverse ch B so both travel the SAME way
                            //  (set 0 if your two motors are mounted the same way, not mirrored)

// -------- ACS712 --------
const int I_DIVIDER = 2; const float I_SENS_MV_PER_A = 66; float i_offset_mV = 2500;

// -------- PINS --------
const int ENA=25, IN1=26, IN2=27;   // Board#1 chA -> Rail motor L (Motor A)
const int ENB=14, IN3=16, IN4=17;   // Board#1 chB -> Rail motor R (Motor B)
const int BRUSH_EN=23;              // Board#2 chA EN -> Brush (dir hardwired on board)
const int PUMP_EN =22;              // Board#2 chB EN -> Pump  (dir hardwired on board)
const int ENC_A=32, ENC_B=33;
const int LIM_L=18, LIM_R=19;
const int I_SENSE=34;
const int DHT_PIN=4;                 // DHT22 / AM2302 data
const int PWM_FREQ=20000, PWM_RES=8;
DHT dht(DHT_PIN, DHT22);
float airT=NAN, airRH=NAN, dewC=NAN; // refreshed every 2 s

// -------- STATE --------
volatile long ticks=0;
enum Mode { MANUAL, HOMING, SWEEP_R, SWEEP_L, PARKED };
Mode mode=MANUAL;
int  railDir=0, passCount=0;
bool brushState=false, pumpState=false, printedCal=false;
unsigned long pumpOnAccum_ms=0, pumpStart_ms=0; bool pumpRunning=false;
String line="";

void IRAM_ATTR encISR(){ bool b=digitalRead(ENC_B);
#if INVERT_ENCODER
  b=!b;
#endif
  if(b) ticks++; else ticks--; }

// -------- ACTUATORS --------
void driveRails(int d){            // Motor A on ch A, Motor B on ch B; both move as one
#if INVERT_DRIVE
  d=-d;
#endif
  railDir=d; bool fwd=d>0; int duty=d?DRIVE_DUTY:0;
  // Motor A (Rail L) -- channel A, OUT1/OUT2
  digitalWrite(IN1, d&&fwd);  digitalWrite(IN2, d&&!fwd);  ledcWrite(ENA, duty);
  // Motor B (Rail R) -- channel B, OUT3/OUT4; reversed so it travels the SAME way as A
  bool fwdB = RAIL_R_REVERSED ? !fwd : fwd;
  digitalWrite(IN3, d&&fwdB); digitalWrite(IN4, d&&!fwdB); ledcWrite(ENB, duty);
}
void setBrush(bool on){ brushState=on; ledcWrite(BRUSH_EN, on?BRUSH_DUTY:0); }
void setPump(bool on){ pumpState=on;
  if(on&&!pumpRunning){ pumpStart_ms=millis(); pumpRunning=true; }
  if(!on&&pumpRunning){ pumpOnAccum_ms+=millis()-pumpStart_ms; pumpRunning=false; }
  ledcWrite(PUMP_EN, on?PUMP_DUTY:0); }
void cleanOn(bool on){ setBrush(on); setPump(on); }
void allStop(){ mode=MANUAL; driveRails(0); setBrush(false); setPump(false); }

float sprayedML(){ unsigned long t=pumpOnAccum_ms+(pumpRunning?millis()-pumpStart_ms:0);
  return (t/1000.0)*PUMP_FLOW_MLPS; }
float posMM(){ return TICKS_PER_TRAVEL>0 ? (float)ticks/TICKS_PER_TRAVEL*RAIL_TRAVEL_MM : -1; }
float busAmps(){ return (I_DIVIDER*analogReadMilliVolts(I_SENSE) - i_offset_mV)/I_SENS_MV_PER_A; }

void help(){ Serial.println(F(
  "cmds: rN bN pN | f v x (rails) | m (brush) w (pump) | g (auto) s (stop)")); }

void runCmd(String s){
  char c=s[0]; int v=s.substring(1).toInt();
  switch(c){
    case 'r': DRIVE_DUTY=constrain(v,0,255); if(railDir)driveRails(railDir);
              Serial.printf("rail=%d\n",DRIVE_DUTY); break;
    case 'b': BRUSH_DUTY=constrain(v,0,255); if(brushState)setBrush(true);
              Serial.printf("brush=%d\n",BRUSH_DUTY); break;
    case 'p': PUMP_DUTY=constrain(v,0,255);  if(pumpState)setPump(true);
              Serial.printf("pump=%d\n",PUMP_DUTY); break;
    case 'f': mode=MANUAL; driveRails(+1); break;
    case 'v': mode=MANUAL; driveRails(-1); break;
    case 'x': driveRails(0); break;
    case 'm': setBrush(!brushState); break;
    case 'w': setPump(!pumpState); break;
    case 'g': mode=HOMING; Serial.println(F("auto: homing...")); driveRails(-1); break;
    case 's': allStop(); Serial.println(F("STOP")); break;
    default : help();
  }
}

// -------- SETUP --------
void setup(){
  Serial.begin(115200);
  pinMode(IN1,OUTPUT); pinMode(IN2,OUTPUT); pinMode(IN3,OUTPUT); pinMode(IN4,OUTPUT);
  ledcAttach(ENA,PWM_FREQ,PWM_RES);
  ledcAttach(ENB,PWM_FREQ,PWM_RES);
  ledcAttach(BRUSH_EN,PWM_FREQ,PWM_RES); ledcWrite(BRUSH_EN,0);
  ledcAttach(PUMP_EN, PWM_FREQ,PWM_RES); ledcWrite(PUMP_EN,0);
  pinMode(ENC_A,INPUT_PULLUP); pinMode(ENC_B,INPUT_PULLUP);
  pinMode(LIM_L,INPUT_PULLUP); pinMode(LIM_R,INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(ENC_A),encISR,RISING);
  dht.begin();
  long acc=0; for(int i=0;i<64;i++){ acc+=analogReadMilliVolts(I_SENSE); delay(2); }
  i_offset_mV=I_DIVIDER*(acc/64.0);
  Serial.println(F("=== bench_cleaner ready (manual) ===")); help();
}

// -------- LOOP --------
void loop(){
  while(Serial.available()){ char c=Serial.read();
    if(c=='\n'||c=='\r'){ if(line.length()) runCmd(line); line=""; }
    else line+=c; }

  switch(mode){
    case MANUAL:
      if(railDir>0 && digitalRead(LIM_R)==LOW) driveRails(0);
      if(railDir<0 && digitalRead(LIM_L)==LOW) driveRails(0);
      break;
    case HOMING:
      if(digitalRead(LIM_L)==LOW){ driveRails(0); delay(PAUSE_MS); ticks=0; passCount=0;
        Serial.println(F("homed; sweeping")); cleanOn(true); driveRails(+1); mode=SWEEP_R; }
      break;
    case SWEEP_R:
      if(digitalRead(LIM_R)==LOW){ driveRails(0); cleanOn(false);
        if(!printedCal){ Serial.printf(">>> TICKS_PER_TRAVEL = %ld\n",ticks); printedCal=true; }
        passCount++; delay(PAUSE_MS);
        if(passCount>=NUM_PASSES){ mode=PARKED; break; }
        cleanOn(true); driveRails(-1); mode=SWEEP_L; }
      break;
    case SWEEP_L:
      if(digitalRead(LIM_L)==LOW){ driveRails(0); cleanOn(false);
        passCount++; delay(PAUSE_MS);
        if(passCount>=NUM_PASSES){ mode=PARKED; break; }
        cleanOn(true); driveRails(+1); mode=SWEEP_R; }
      break;
    case PARKED: allStop(); mode=MANUAL;
        Serial.printf("=== done: %d passes, %.0f mL ===\n",passCount,sprayedML()); break;
  }

  // DHT22 is slow: refresh no faster than every 2 s, compute dew point (Magnus)
  static unsigned long td=0;
  if(millis()-td>2000){ td=millis();
    float h=dht.readHumidity(), tC=dht.readTemperature();
    if(!isnan(h)&&!isnan(tC)){ airRH=h; airT=tC;
      double g=log(h/100.0)+17.62*tC/(243.12+tC); dewC=243.12*g/(17.62-g); }
  }

  static unsigned long t=0;
  if(millis()-t>300){ t=millis();
    Serial.printf("[%d] rail%d br%d pu%d | ticks %ld pos %.0f mm spray %.0f mL I %.2fA | %.0f%%RH %.1fC dew %.1fC\n",
      (int)mode, railDir, brushState, pumpState, ticks, posMM(), sprayedML(), busAmps(),
      airRH, airT, dewC);
  }
}
