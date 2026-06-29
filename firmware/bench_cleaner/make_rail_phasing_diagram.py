"""
Why the two rail motors must be wired with ONE crossed: they face each other on
opposite rails, so identical polarity = opposite travel. Cross one -> they pull as one.
"""
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle, FancyArrowPatch

fig,(ax1,ax2)=plt.subplots(1,2,figsize=(14,6),dpi=150)
STEEL="#8a8f98"; INK="#222"; RED="#d62728"; WHT="#888"; CAR="#d9e6f2"; OK="#2a8a4a"

def rails(ax):
    ax.add_patch(Rectangle((8,68),84,4,fc=STEEL,ec="k"))   # top rail
    ax.add_patch(Rectangle((8,18),84,4,fc=STEEL,ec="k"))   # bottom rail
    ax.add_patch(FancyBboxPatch((40,30),20,30,boxstyle="round,pad=0.3",fc=CAR,ec=INK,lw=1.6))
    ax.text(50,45,"CARRIAGE",fontsize=9,ha="center",va="center",fontweight="bold")
def motor(ax,x,y,lbl):
    ax.add_patch(FancyBboxPatch((x-9,y-5),18,10,boxstyle="round,pad=0.2",fc="#eef2f7",ec=INK,lw=1.6))
    ax.text(x,y,lbl,fontsize=8.5,ha="center",va="center",fontweight="bold")
def spin(ax,x,y,cw,col):
    ax.annotate("",xy=(x+4,y+ (3 if cw else -3)),xytext=(x-4,y+(-3 if cw else 3)),
                arrowprops=dict(arrowstyle="->",color=col,lw=2.2,connectionstyle="arc3,rad=%.1f"%(0.5 if cw else -0.5)))
def travel(ax,col):
    ax.add_patch(FancyArrowPatch((46,45),(64,45),arrowstyle="-|>",mutation_scale=22,color=col,lw=0))

for ax in (ax1,ax2):
    ax.set_xlim(0,100); ax.set_ylim(0,95); ax.axis("off"); rails(ax)
    motor(ax,25,70,"Motor R"); motor(ax,25,20,"Motor L")
    ax.text(75,71,"opposite rails, motors FACE each other",fontsize=8,ha="center",color="#555")

# ---- LEFT: WRONG (same wiring) ----
ax1.set_title("WRONG — both wired the same",fontsize=12,fontweight="bold",color=RED)
ax1.text(25,79,"red→OUT1  white→OUT2",fontsize=8,ha="center",color=RED)
ax1.text(25,11,"red→OUT1  white→OUT2",fontsize=8,ha="center",color=RED)
spin(ax1,25,70,True,RED); spin(ax1,25,20,True,RED)     # same spin in space
ax1.add_patch(FancyArrowPatch((42,52),(30,52),arrowstyle="-|>",mutation_scale=16,color=RED,lw=0)) # top pushes left
ax1.add_patch(FancyArrowPatch((42,38),(58,38),arrowstyle="-|>",mutation_scale=16,color=RED,lw=0)) # bottom pushes right
ax1.text(50,90,"same spin → carriage pushed OPPOSITE ways → they fight",fontsize=9.5,ha="center",color=RED)

# ---- RIGHT: RIGHT (cross one) ----
ax2.set_title("RIGHT — cross ONE motor",fontsize=12,fontweight="bold",color=OK)
ax2.text(25,79,"red→OUT2  white→OUT1  (crossed)",fontsize=8,ha="center",color=OK,fontweight="bold")
ax2.text(25,11,"red→OUT1  white→OUT2",fontsize=8,ha="center",color=INK)
spin(ax2,25,70,False,OK); spin(ax2,25,20,True,OK)      # opposite spin in space
travel(ax2,OK)
ax2.text(50,90,"opposite spin → both push the SAME way → move as one",fontsize=9.5,ha="center",color=OK)

plt.tight_layout()
out="firmware/bench_cleaner/rail_phasing.png"
plt.savefig(out,bbox_inches="tight",facecolor="white"); print("saved",out)
