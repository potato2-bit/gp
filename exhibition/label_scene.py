"""Label the integrated simulation scene (with the silica-gel dock tank) for poster Fig 1.

Base = iso_scene.png (cropped from integration shot_mid_clean — shows the translucent
silica-gel dock tank + chimney, the rail-guided robot, and the 24° PV panel). Upscaled 2x so
the callouts stay crisp. Output -> fig_system_labeled.png.
"""
from PIL import Image, ImageDraw, ImageFont

SRC, OUT = "iso_scene.png", "fig_system_labeled.png"
UP = 2
PADL, PADT, PADR, PADB = 110, 250, 120, 70
NAVY, GOLD, WHITE = (11, 42, 74), (244, 163, 0), (255, 255, 255)
F = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 42)

base = Image.open(SRC).convert("RGB")
base = base.resize((base.width*UP, base.height*UP), Image.LANCZOS)
bgpix = base.getpixel((base.width-4, 4))
W = base.width + PADL + PADR
H = base.height + PADT + PADB
canvas = Image.new("RGB", (W, H), WHITE)
canvas.paste(base, (PADL, PADT))
d = ImageDraw.Draw(canvas)

# (text, tip x, tip y  in ORIGINAL iso_scene px, box centre x, box centre y in PADDED px)
LABELS = [
    ("Solar-regenerated silica-gel dock\n(harvests + stores the water)", 130, 112, 360, 120),
    ("Rail-guided cleaning robot:\nspray bar + microfibre roller",        300,  88, 880,  85),
    ("PV panel (24° tilt)",                                           430,  60, 1300, 250),
    ("Guide rail (robot drives along it)",                                330, 150, 430, 800),
]

def tip(tx, ty):
    return (PADL + tx*UP, PADT + ty*UP)

for text, tx, ty, cx, cy in LABELS:                      # leaders first
    d.line([(cx, cy), tip(tx, ty)], fill=NAVY, width=6)
for text, tx, ty, cx, cy in LABELS:                      # tip dots
    x, y = tip(tx, ty); r = 11
    d.ellipse([x-r, y-r, x+r, y+r], fill=GOLD, outline=NAVY, width=3)
for text, tx, ty, cx, cy in LABELS:                      # boxes + text on top
    bb = d.multiline_textbbox((0, 0), text, font=F, align="center", spacing=6)
    w, h = bb[2]-bb[0], bb[3]-bb[1]
    px, py = 26, 18
    d.rounded_rectangle([cx-w/2-px, cy-h/2-py, cx+w/2+px, cy+h/2+py],
                        radius=16, fill=WHITE, outline=NAVY, width=5)
    d.multiline_text((cx, cy), text, font=F, fill=NAVY, anchor="mm",
                     align="center", spacing=6)

canvas.save(OUT)
print("saved", OUT, canvas.size)
