"""Draw silica-gel-correct callouts on the clean isometric Gazebo render (shot_wide.png).

Produces exhibition/fig_system_labeled.png — the labeled isometric front-up-side view of
the system, used as the poster's Fig 1. Tip coordinates are in ORIGINAL 1600x1000 pixels;
the script pads the canvas so edge labels have room.
"""
from PIL import Image, ImageDraw, ImageFont

SRC = "iso_base.png"          # = gazebo/pvbot_description/shot_wide.png (1600x1000)
OUT = "fig_system_labeled.png"
PAD = 130
NAVY = (11, 42, 74)
GOLD = (244, 163, 0)
WHITE = (255, 255, 255)

def font(sz, bold=True):
    path = "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"
    return ImageFont.truetype(path, sz)

F = font(34)

# (label text, tip x, tip y  [in ORIGINAL px], box center x, box center y [in PADDED px])
LABELS = [
    ("Solar-regenerated\nsilica-gel adsorber", 955, 255,  330, 150),
    ("Microfibre roller\n+ spray bar",        1110, 300, 1640, 165),
    ("Gantry carriage\n(rail-driven)",        1000, 360, 1660, 470),
    ("Support frame",                         1190, 545, 1690, 800),
    ("PV panel (24° tilt)",               690, 520,  860, 1180),
    ("Guide rails",                            560, 360,  250, 690),
]

base = Image.open(SRC).convert("RGB")
bg = base.getpixel((5, 5))
canvas = Image.new("RGB", (base.width + 2 * PAD, base.height + 2 * PAD), bg)
canvas.paste(base, (PAD, PAD))
d = ImageDraw.Draw(canvas)

def box_for(text, cx, cy):
    bb = d.multiline_textbbox((0, 0), text, font=F, align="center", spacing=6)
    w, h = bb[2] - bb[0], bb[3] - bb[1]
    padx, pady = 22, 16
    return [cx - w/2 - padx, cy - h/2 - pady, cx + w/2 + padx, cy + h/2 + pady], (w, h)

# 1) leader lines (box centre -> tip); covered by the box later so they emanate from its edge
for text, tx, ty, cx, cy in LABELS:
    d.line([(cx, cy), (tx + PAD, ty + PAD)], fill=NAVY, width=5)
# 2) tip dots
for text, tx, ty, cx, cy in LABELS:
    r = 9
    d.ellipse([tx+PAD-r, ty+PAD-r, tx+PAD+r, ty+PAD+r], fill=GOLD, outline=NAVY, width=3)
# 3) boxes + text
for text, tx, ty, cx, cy in LABELS:
    rect, _ = box_for(text, cx, cy)
    d.rounded_rectangle(rect, radius=14, fill=WHITE, outline=NAVY, width=4)
    d.multiline_text((cx, cy), text, font=F, fill=NAVY, anchor="mm",
                     align="center", spacing=6)

canvas.save(OUT)
print("saved", OUT, canvas.size)
