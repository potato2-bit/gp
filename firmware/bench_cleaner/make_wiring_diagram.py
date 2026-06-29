"""
Full bench wiring map: ESP32 + Board#1 (H-bridge: rails L/R) + Board#2 (brush/pump)
+ ACS712 current sensor + buck + limits + encoder. Solar-AWH PV-cleaning robot.
"""
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Circle, Rectangle

fig, ax = plt.subplots(figsize=(15, 9.5), dpi=150)
ax.set_xlim(0, 100); ax.set_ylim(0, 100); ax.axis("off")
SIG="#1f6fb0"; PWR="#d62728"; GND="#333"; ENC="#3a7a35"; INK="#222"; BOX="#eef2f7"

def box(x,y,w,h,t,fc=BOX):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle="round,pad=0.2",fc=fc,ec=INK,lw=2,zorder=2))
    ax.text(x+w/2,y+h-2.2,t,fontsize=10,fontweight="bold",ha="center",zorder=3)
def wire(p0,p1,c,lw=2.0,z=1):
    ax.plot([p0[0],p1[0]],[p0[1],p1[1]],color=c,lw=lw,zorder=z,solid_capstyle="round")
def motor(x,y,t):
    ax.add_patch(Circle((x,y),3.2,fc="#d9e6f2",ec=INK,lw=1.8,zorder=3))
    ax.text(x,y,"M",fontsize=9,ha="center",va="center",fontweight="bold",zorder=4)
    ax.text(x,y-5,t,fontsize=8.5,ha="center",zorder=4)

ax.text(50,97,"Bench wiring map — every connection",fontsize=15,fontweight="bold",ha="center")

# ---- ESP32 ----
box(8,30,20,46,"ESP32")
esp=[("25",70,"ENA L"),("26",66,"IN1 L"),("27",62,"IN2 L"),
     ("14",57,"ENB R"),("16",53,"IN3 R"),("17",49,"IN4 R"),
     ("23",43,"EN brush"),("22",39,"EN pump"),
     ("32",34,"enc A"),("33",31.5,"enc B")]
for g,y,lbl in esp:
    ax.text(27.4,y,f"{g}",fontsize=8,ha="right",va="center",color=SIG,fontweight="bold")
    ax.text(9.5,y,lbl,fontsize=7.3,ha="left",va="center",color="#555")
ax.text(18,73,"3V3 → enc Vcc",fontsize=7.3,ha="center",color=ENC)
ax.text(18,27.5,"5V ← buck   GND ← common",fontsize=7.3,ha="center",color=GND)

# ---- Board #1 H-bridge ----
box(58,60,24,32,"BOARD #1  (H-BRIDGE)")
ax.text(70,84.5,"ch A → Rail L",fontsize=8.5,ha="center")
ax.text(70,80.5,"ENA·IN1·IN2   OUT1/OUT2",fontsize=7.4,ha="center",color="#555")
ax.text(70,72.5,"ch B → Rail R",fontsize=8.5,ha="center")
ax.text(70,68.5,"ENB·IN3·IN4   OUT3/OUT4",fontsize=7.4,ha="center",color="#555")
motor(92,82,"Rail L"); motor(92,67,"Rail R")
wire((82,82),(89,82),PWR); wire((82,67),(89,67),PWR)

# ---- Board #2 other ----
box(58,22,24,30,"BOARD #2  (OTHER)")
ax.text(70,46.5,"ch A → Brush   EN only",fontsize=8.5,ha="center")
ax.text(70,42.8,"IN1→5V  IN2→GND   OUT1/OUT2",fontsize=7.2,ha="center",color="#555")
ax.text(70,34.5,"ch B → Pump    EN only",fontsize=8.5,ha="center")
ax.text(70,30.8,"IN3→5V  IN4→GND   OUT3/OUT4",fontsize=7.2,ha="center",color="#555")
motor(92,44,"Brush"); motor(92,29,"Pump")
wire((82,44),(89,44),PWR); wire((82,29),(89,29),PWR)

# ---- signal wires ESP32 -> boards ----
for y in (70,66,62,57,53,49):  wire((28,y),(58,y if y>59 else y+12),SIG,1.6)
# simpler straight bundles
for y in (70,66,62):  wire((28,y),(58,80+(70-y)*0.0+ (y-62)),SIG,1.4)
wire((28,43),(58,46),SIG,1.6)   # brush EN
wire((28,39),(58,34),SIG,1.6)   # pump EN
# encoder
wire((28,34),(89,82),ENC,1.4); wire((28,31.5),(89,82),ENC,1.4)
ax.text(55,86,"enc A/B,Vcc,GND  (Rail-L motor)",fontsize=7,color=ENC,ha="center")

# ---- ACS712 + buck + 12V ----
box(34,6,18,12,"ACS712  (in-line)")
ax.text(43,12.5,"Ip+ ← 12V(+)   Ip- → both VS",fontsize=7,ha="center",color="#555")
ax.text(43,9.5,"VCC 5V · GND · OUT→/2→34",fontsize=7,ha="center",color="#555")
box(8,8,18,12,"BUCK 12→5V")
ax.text(17,12,"5V → ESP32 + ACS712 VCC",fontsize=7,ha="center",color="#555")

# power/ground buses
wire((2,15),(8,15),PWR,3)           # 12V into buck
ax.text(2,17.5,"12V +",fontsize=8,color=PWR,fontweight="bold")
wire((52,12),(70,22),PWR,2.5)       # 12V to boards (via ACS712)
wire((52,14),(70,60),PWR,2.5)
ax.text(60,18,"12V (VS) to both boards",fontsize=7,color=PWR,ha="center")
ax.text(50,2.5,"BLACK = common GND (12V−, buck, both boards, ESP32, ACS712, encoder, limit COMs)  ·  RED = +12V  ·  BLUE = ESP32 signal  ·  GREEN = encoder",
        fontsize=8,ha="center",color=INK)

# limits
ax.text(18,22,"LIM_L→18 · LIM_R→19  (COM→GND, NO→pin)",fontsize=7.2,ha="center",color="#555",
        bbox=dict(boxstyle="round,pad=0.25",fc="white",ec="#999"))

plt.tight_layout()
out="firmware/bench_cleaner/wiring_diagram.png"
plt.savefig(out,bbox_inches="tight",facecolor="white"); print("saved",out)
