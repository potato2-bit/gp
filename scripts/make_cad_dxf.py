"""Generate DXF versions of drawings D-101..D-107.

Same dimensions as the AutoCAD .scr files in cad/. Geometry is 1:1 in mm.
Run:  python scripts/make_cad_dxf.py
"""
import os
import ezdxf
from ezdxf.enums import TextEntityAlignment

OUT = os.path.join(os.path.dirname(__file__), "..", "cad")
DATE = "2026-06-12"

LAYERS = [
    ("OUTLINE", 7, "CONTINUOUS"),
    ("HIDDEN", 1, "HIDDEN"),
    ("CENTER", 2, "CENTER"),
    ("DIM", 3, "CONTINUOUS"),
    ("TEXT", 4, "CONTINUOUS"),
]


def new_doc():
    doc = ezdxf.new("R2010", setup=True)
    for name, color, lt in LAYERS:
        doc.layers.add(name, color=color, linetype=lt)
    doc.header["$INSUNITS"] = 4  # mm
    return doc


def rect(msp, x1, y1, x2, y2, layer="OUTLINE"):
    msp.add_lwpolyline(
        [(x1, y1), (x2, y1), (x2, y2), (x1, y2)],
        close=True, dxfattribs={"layer": layer})


def circ(msp, x, y, r, layer="OUTLINE"):
    msp.add_circle((x, y), r, dxfattribs={"layer": layer})


def line(msp, x1, y1, x2, y2, layer="OUTLINE"):
    msp.add_line((x1, y1), (x2, y2), dxfattribs={"layer": layer})


def txt(msp, x, y, h, s, layer="TEXT", rot=0):
    msp.add_text(s, dxfattribs={"layer": layer, "height": h, "rotation": rot}
                 ).set_placement((x, y), align=TextEntityAlignment.LEFT)


def ldim(msp, p1, p2, base, angle=0):
    d = msp.add_linear_dim(base=base, p1=p1, p2=p2, angle=angle,
                           dxfattribs={"layer": "DIM"})
    d.render()


def title(msp, x, y, w, num, name, scale="1:2  A3"):
    """Title block, lower-left corner at (x, y), width w, height 60."""
    rect(msp, x, y, x + w, y + 60)
    line(msp, x, y + 30, x + w, y + 30)
    line(msp, x + w * 0.55, y, x + w * 0.55, y + 60)
    txt(msp, x + 8, y + 38, 8, f"{num}  {name}")
    txt(msp, x + 8, y + 8, 5, f"TEC PV-CLEAN ROBOT - REE598 - {DATE}")
    txt(msp, x + w * 0.55 + 8, y + 38, 5, f"SCALE {scale}")
    txt(msp, x + w * 0.55 + 8, y + 8, 5, "UNITS MM - ISO 2768-m")


def save(doc, fname):
    path = os.path.join(OUT, fname)
    doc.saveas(path)
    print("wrote", path)


# ---------------------------------------------------------------- D-101
def d101():
    doc = new_doc(); msp = doc.modelspace()
    rect(msp, 0, 0, 400, 300)                       # plate 400x300x3
    rect(msp, 40, 7, 120, 33)                       # wheel slots 80x26
    rect(msp, 40, 267, 120, 293)
    for x, y in [(66, 41), (94, 41), (66, 85), (94, 85),
                 (66, 215), (94, 215), (66, 259), (94, 259)]:
        circ(msp, x, y, 2.25)                       # motor bracket M4
    for x, y in [(355, 100), (385, 100), (355, 200), (385, 200)]:
        circ(msp, x, y, 2.25)                       # caster M4 csk
    for x, y in [(165, 30), (345, 30), (165, 270), (345, 270)]:
        circ(msp, x, y, 2.5)                        # tank strap D5
    for x, y in [(20, 120), (150, 120), (20, 200), (150, 200)]:
        circ(msp, x, y, 1.6)                        # elx deck M3
    for x, y in [(350, 45), (386, 45)]:
        circ(msp, x, y, 2.25)                       # pump M4
    for x, y in [(370, 22), (390, 22), (370, 278), (390, 278)]:
        circ(msp, x, y, 2.25)                       # brush arm M4
    rect(msp, 170, 35, 340, 265, "HIDDEN")          # tank bay ref
    rect(msp, 10, 110, 160, 210, "HIDDEN")          # elx bay ref
    line(msp, 80, -15, 80, 315, "CENTER")           # axle CL
    line(msp, -15, 150, 415, 150, "CENTER")
    ldim(msp, (0, 0), (400, 0), (200, -40))
    ldim(msp, (0, 0), (0, 300), (-50, 150), angle=90)
    ldim(msp, (0, 0), (80, 0), (40, -22))
    ldim(msp, (66, 41), (94, 41), (80, 58))
    ldim(msp, (165, 30), (345, 30), (255, -22))
    txt(msp, 30, 95, 6, "A 8x D4.5 MOTOR BRACKET (M4)")
    txt(msp, 250, 110, 6, "B 4x D4.5 CASTER (M4 CSK)")
    txt(msp, 200, 282, 6, "C 4x D5 TANK STRAP")
    txt(msp, 30, 222, 6, "D 4x D3.2 ELX DECK (M3)")
    txt(msp, 300, 57, 6, "E 2x D4.5 PUMP (M4)")
    txt(msp, 280, 10, 6, "F 4x D4.5 BRUSH ARM (M4)")
    txt(msp, 88, 318, 6, "DRIVE AXLE CL - TRACK 260")
    txt(msp, -120, 420, 7, "AL 6061-T6 PLATE THK 3, LASER CUT. "
                           "CSK AT B. MASS 0.90 KG")
    title(msp, 300, -180, 400, "D-101", "CHASSIS BASE PLATE")
    save(doc, "D-101_chassis_base_plate.dxf")


# ---------------------------------------------------------------- D-102
def d102():
    doc = new_doc(); msp = doc.modelspace()
    # front view: base 44x6, upright to 44/50, bore D25 at (22,20)
    msp.add_lwpolyline([(0, 0), (44, 0), (44, 44), (28, 50), (16, 50),
                        (0, 44)], close=True, dxfattribs={"layer": "OUTLINE"})
    line(msp, 0, 6, 44, 6)
    circ(msp, 22, 20, 12.5)
    line(msp, 21, 32.5, 21, 50); line(msp, 23, 32.5, 23, 50)  # clamp slit
    circ(msp, 10, 41, 1.6, "HIDDEN"); circ(msp, 34, 41, 1.6, "HIDDEN")
    line(msp, 22, -6, 22, 56, "CENTER"); line(msp, -6, 20, 50, 20, "CENTER")
    ldim(msp, (0, 0), (44, 0), (22, -14))
    ldim(msp, (44, 0), (44, 44), (70, 22), angle=90)
    ldim(msp, (0, 0), (0, 20), (-14, 10), angle=90)
    txt(msp, -5, 62, 4, "BORE D25 H8 - JGA25 MOTOR, CLAMP SLIT 2 + 2x M3")
    # side view at x+110: base 60 deep
    rect(msp, 110, 0, 170, 6); rect(msp, 110, 6, 118, 50)
    rect(msp, 118, 7.8, 180, 32.2, "HIDDEN")        # motor D24.4x62 ref
    line(msp, 104, 20, 192, 20, "CENTER")
    ldim(msp, (110, 0), (170, 0), (140, -14))
    txt(msp, 120, 40, 4, "MOTOR JGA25-370 D24.4x62 (REF)")
    # base plan at y+90: 44x60, 4x D4.5 at 28x44
    rect(msp, 0, 90, 44, 150)
    for x, y in [(8, 98), (36, 98), (8, 142), (36, 142)]:
        circ(msp, x, y, 2.25)
    ldim(msp, (8, 98), (36, 98), (22, 106))
    ldim(msp, (8, 98), (8, 142), (-14, 120), angle=90)
    txt(msp, 0, 158, 4, "BASE PLAN - 4x D4.5 (M4) PATTERN 28x44 = D-101 A")
    txt(msp, -20, 172, 5, "POM, MACHINED, QTY 2 MIRROR PAIR. "
                          "AXLE 14 ABOVE PLATE. MASS 0.06 KG EA")
    title(msp, 0, -80, 280, "D-102", "MOTOR MOUNT BRACKET (x2)", "1:1  A4")
    save(doc, "D-102_motor_mount_bracket.dxf")


# ---------------------------------------------------------------- D-103
def d103():
    doc = new_doc(); msp = doc.modelspace()
    rect(msp, 0, -40, 250, 40)                      # roller D80x250
    line(msp, 0, -12.5, 250, -12.5, "HIDDEN")       # core D25
    line(msp, 0, 12.5, 250, 12.5, "HIDDEN")
    rect(msp, -25, -4, 0, 4); rect(msp, 250, -4, 275, 4)   # shaft D8
    rect(msp, -37, -20, -25, 20); rect(msp, 275, -20, 287, 20)  # housings
    rect(msp, 287, -6, 323, 6, "HIDDEN")            # drive motor ref
    rect(msp, -10, 55, 260, 65)                     # spray bar D10 x 270
    for i in range(5):                              # nozzles pitch 50
        x = 25 + 50 * i
        line(msp, x, 55, x - 3, 47); line(msp, x, 55, x + 3, 47)
    line(msp, -45, 0, 330, 0, "CENTER")
    ldim(msp, (0, -40), (250, -40), (125, -62))
    ldim(msp, (25, 55), (75, 55), (50, 80))
    ldim(msp, (0, 55), (25, 55), (12, 95))
    ldim(msp, (0, -40), (0, 40), (-52, 0), angle=90)
    txt(msp, 40, 90, 5, "SPRAY BAR D10 PVC - 5 NOZZLES D1.0 AT PITCH 50")
    txt(msp, 60, -75, 5, "MICROFIBRE ROLLER D80 x 250 ON D25 PVC CORE")
    # end view at x 420
    circ(msp, 420, 0, 40); circ(msp, 420, 0, 12.5); circ(msp, 420, 0, 4)
    circ(msp, 420, 0, 11, "HIDDEN")                 # 608ZZ
    circ(msp, 440, 60, 5)
    line(msp, 437, 56, 425, 35); line(msp, 443, 56, 455, 35)
    line(msp, 372, 0, 468, 0, "CENTER"); line(msp, 420, -48, 420, 48, "CENTER")
    txt(msp, 392, -60, 5, "END VIEW - 608ZZ 8x22x7 IN POM HOUSING")
    txt(msp, 400, 76, 5, "NOZZLE AIM 30 DEG AHEAD OF CONTACT")
    txt(msp, -50, 246, 5, "SHAFT STEEL D8 h6. LOW-PRESSURE SPRAY. "
                          "ASSY MASS 0.60 KG")
    title(msp, 140, -160, 340, "D-103", "BRUSH ASSEMBLY")
    save(doc, "D-103_brush_assembly.dxf")


# ---------------------------------------------------------------- D-104
def d104():
    doc = new_doc(); msp = doc.modelspace()
    rect(msp, 0, 0, 170, 170)                       # cold plate 170x170x3
    for cx, cy in [(42.5, 42.5), (127.5, 42.5), (42.5, 127.5),
                   (127.5, 127.5)]:                 # TEC pockets 40x40
        rect(msp, cx - 20, cy - 20, cx + 20, cy + 20)
        line(msp, cx, cy - 28, cx, cy + 28, "CENTER")
        line(msp, cx - 28, cy, cx + 28, cy, "CENTER")
    for x, y in [(85, 10), (85, 85), (85, 160), (10, 85), (160, 85),
                 (10, 10), (160, 10), (10, 160)]:
        circ(msp, x, y, 2.25)                       # clamp M4
    rect(msp, 0, -14, 170, -2, "HIDDEN")            # gutter 12x12
    circ(msp, 85, -8, 4, "HIDDEN")                  # drain D8
    ldim(msp, (0, 0), (170, 0), (85, -40))
    ldim(msp, (0, 0), (0, 170), (-34, 85), angle=90)
    ldim(msp, (22.5, 22.5), (62.5, 22.5), (42.5, -16))
    ldim(msp, (42.5, 22.5), (127.5, 22.5), (85, 30))
    txt(msp, 20, 178, 5, "COLD PLATE AL 6061 170x170x3 - "
                         "4x TEC POCKET 40x40x0.5")
    txt(msp, 100, -10, 5, "GUTTER 12x12 + DRAIN D8 TO TANK")
    # section at (250, 230): plate 3 / TEC 3.6 / sink 25
    rect(msp, 250, 260, 420, 263)
    rect(msp, 270, 256.4, 310, 260); rect(msp, 360, 256.4, 400, 260)
    rect(msp, 250, 231.4, 420, 256.4)
    for x in range(260, 401, 20):
        line(msp, x, 231.4, x, 256.4)
    txt(msp, 250, 290, 5, "SECTION: COLD PLATE 3 / TEC1-12706 3.6 / "
                          "HOT SINKS 160x160x25")
    # fan plate at (250, 0): 180x90, 2x D76 cutouts, holes 71.5 sq
    rect(msp, 250, 0, 430, 90)
    circ(msp, 295, 45, 38); circ(msp, 385, 45, 38)
    for cx in (295, 385):
        for dx in (-35.75, 35.75):
            for dy in (-35.75, 35.75):
                circ(msp, cx + dx, 45 + dy, 2.25)
    txt(msp, 250, 100, 5, "FAN PLATE AL 1.5 - 2x D76 CUTOUT, "
                          "8x D4.5 ON 71.5 SQ (80MM FANS)")
    txt(msp, -60, 318, 5, "COLD FACE UP, TILT 15 DEG TO GUTTER. "
                          "2 M/S COLD-SIDE FACE VELOCITY. MASS 1.05 KG")
    title(msp, 180, -120, 400, "D-104", "TEC COLD-PLATE SANDWICH")
    save(doc, "D-104_tec_coldplate_sandwich.dxf")


# ---------------------------------------------------------------- D-105
def d105():
    doc = new_doc(); msp = doc.modelspace()
    rect(msp, 0, 0, 170, 230)                       # tank plan ext
    rect(msp, 2, 2, 168, 228, "HIDDEN")             # 2 mm wall
    circ(msp, 85, 40, 20); circ(msp, 85, 40, 16)    # filler cap D40
    for x, y in [(-5, 30), (175, 30), (-5, 200), (175, 200)]:
        circ(msp, x, y, 2.5)                        # lug holes D5
    circ(msp, 85, 200, 4)                           # inlet D8
    circ(msp, 30, 115, 8)                           # level switch D16
    ldim(msp, (0, 0), (170, 0), (85, -30))
    ldim(msp, (0, 0), (0, 230), (-34, 115), angle=90)
    txt(msp, 8, 240, 5, "TANK PLAN - LUGS D5 MATCH D-101 C (180x240)")
    # front elev at x 260: 170 x 100
    rect(msp, 260, 0, 430, 100)
    rect(msp, 262, 2, 428, 98, "HIDDEN")
    rect(msp, 430, 8, 442, 16)                      # outlet barb D8
    rect(msp, 329, 100, 361, 108)                   # cap
    line(msp, 262, 93, 428, 93, "HIDDEN")           # 3.6 L level
    ldim(msp, (260, 0), (430, 0), (345, -22))
    ldim(msp, (430, 0), (430, 100), (462, 50), angle=90)
    txt(msp, 270, 110, 5, "FRONT ELEV - WORKING LEVEL 3.6 L AT H=93 INT")
    # pump at (260,160): 90x40, feet 2x M4 pitch 36
    rect(msp, 260, 160, 350, 200)
    circ(msp, 287, 156, 2.25); circ(msp, 323, 156, 2.25)
    rect(msp, 350, 170, 360, 178); rect(msp, 350, 184, 360, 192)
    ldim(msp, (287, 156), (323, 156), (305, 138))
    txt(msp, 250, 226, 5, "PUMP 12V DIAPHRAGM 90x40x35, "
                          "FEET 2x D4.5 PITCH 36 (D-101 E)")
    txt(msp, -60, 318, 5, "HDPE 2 MM WELDED. INTERNAL 166x226x96 = 3.60 L. "
                          "TANK 0.28 + PUMP 0.12 KG DRY")
    title(msp, 120, -120, 340, "D-105", "WATER TANK 3.6 L + PUMP")
    save(doc, "D-105_water_tank_pump.dxf")


# ---------------------------------------------------------------- D-106
def d106():
    doc = new_doc(); msp = doc.modelspace()
    rect(msp, 0, 0, 150, 100)                       # deck 150x100x3
    for x, y in [(10, 10), (140, 10), (10, 90), (140, 90)]:
        circ(msp, x, y, 1.6)                        # chassis M3 130x80
    rect(msp, 15, 62, 70, 90, "HIDDEN")             # ESP32 55x28
    for x, y in [(18.5, 65), (66.5, 65), (18.5, 87), (66.5, 87)]:
        circ(msp, x, y, 1.6)                        # M3 48x22
    rect(msp, 90, 50, 133, 93, "HIDDEN")            # driver 43x43
    for x, y in [(93, 53), (130, 53), (93, 90), (130, 90)]:
        circ(msp, x, y, 1.6)                        # M3 37x37
    rect(msp, 15, 30, 41, 50, "HIDDEN")             # INA219 26x20
    circ(msp, 18, 40, 1.6); circ(msp, 38, 40, 1.6)  # M3 x20
    rect(msp, 90, 20, 133, 41, "HIDDEN")            # buck 43x21
    circ(msp, 93, 30, 1.6); circ(msp, 130, 30, 1.6)
    rect(msp, 26, 3, 124, 18, "HIDDEN")             # battery ref
    ldim(msp, (0, 0), (150, 0), (75, -18))
    ldim(msp, (0, 0), (0, 100), (-18, 50), angle=90)
    ldim(msp, (10, 10), (140, 10), (75, 16))
    ldim(msp, (18.5, 65), (66.5, 65), (42, 70))
    txt(msp, 16, 94, 4, "ESP32 DEVKITC (M3 48x22)")
    txt(msp, 90, 96, 4, "DRIVER (M3 37x37)")
    txt(msp, 15, 24, 4, "INA219 (M3 x20)")
    txt(msp, 90, 14, 4, "BUCK (M3 x37)")
    # side elev at y 130
    rect(msp, 0, 130, 150, 133)
    rect(msp, 8, 120, 12, 130); rect(msp, 138, 120, 142, 130)
    line(msp, 0, 120, 150, 120)
    rect(msp, 0, 168, 150, 171)
    rect(msp, 8, 133, 12, 168); rect(msp, 138, 133, 142, 168)
    txt(msp, 30, 174, 4, "COVER ACRYLIC 3, VENT SLOTS 4x 40x3")
    txt(msp, 30, 138, 4, "DECK ON M3x10 STANDOFFS, COVER ON M3x35")
    txt(msp, -20, 194, 4, "ACRYLIC 3 MM LASER CUT. BRASS M3 STANDOFFS. "
                          "BAY MASS 0.37 KG INCL BATTERY")
    title(msp, 0, -80, 260, "D-106", "ELECTRONICS BAY", "1:1  A4")
    save(doc, "D-106_electronics_bay.dxf")


# ---------------------------------------------------------------- D-107
def d107():
    doc = new_doc(); msp = doc.modelspace()
    # side elevation
    line(msp, -60, 0, 520, 0)                       # ground
    rect(msp, 0, 15, 400, 18)                       # plate
    circ(msp, 80, 30, 30); circ(msp, 80, 30, 4)     # wheel D60
    rect(msp, 58, 18, 102, 62)                      # bracket ref
    rect(msp, 170, 18, 340, 118)                    # tank
    rect(msp, 172, 123, 342, 155)                   # TEC sandwich
    rect(msp, 10, 18, 160, 66, "HIDDEN")            # elx bay
    circ(msp, 370, 15, 15)                          # caster
    line(msp, 400, 18, 425, 55); line(msp, 400, 15, 430, 50)  # arm
    circ(msp, 420, 25, 40); circ(msp, 420, 25, 12.5)          # brush
    circ(msp, 440, 85, 5)                           # spray bar
    ldim(msp, (0, 15), (400, 15), (200, -40))
    ldim(msp, (0, 0), (460, 0), (230, -70))
    ldim(msp, (340, 0), (340, 155), (540, 80), angle=90)
    txt(msp, 0, 80, 5, "1 PLATE D-101"); txt(msp, 30, 68, 5, "2 BKT D-102")
    txt(msp, 50, -18, 5, "3 WHEEL D60 x2"); txt(msp, 330, -18, 5, "4 CASTER x2")
    txt(msp, 200, 60, 5, "5 TANK D-105")
    txt(msp, 200, 162, 5, "6 TEC SANDWICH D-104")
    txt(msp, 10, 72, 5, "7 ELX D-106"); txt(msp, 408, 98, 5, "8 BRUSH D-103")
    # plan at y 240
    rect(msp, 0, 240, 400, 540)
    rect(msp, 50, 250, 110, 270, "HIDDEN")
    rect(msp, 50, 510, 110, 530, "HIDDEN")
    rect(msp, 170, 275, 340, 505, "HIDDEN")
    rect(msp, 172, 305, 342, 475, "HIDDEN")
    rect(msp, 10, 350, 160, 450, "HIDDEN")
    rect(msp, 410, 265, 460, 515)                   # brush swath 250
    ldim(msp, (0, 240), (0, 540), (-40, 390), angle=90)
    ldim(msp, (410, 265), (410, 515), (490, 390), angle=90)
    txt(msp, 415, 525, 5, "BRUSH SWATH 250")
    txt(msp, 130, 548, 5, "ENVELOPE 460 x 300 x 155 "
                          "(195 WITH 15 DEG HARVEST SHIM)")
    txt(msp, -70, 614, 5, "MASS: 1 PLATE 0.90 / 2 BKTS 0.12 / MOTORS 0.36 / "
                          "3 WHEELS 0.30 / 4 CASTERS 0.10")
    txt(msp, -70, 602, 5, "5 TANK+PUMP 0.40 + WATER 1.80 / 6 TEC 1.05 / "
                          "7 ELX 0.37 / 8 BRUSH 0.60  TOTAL 6.00 KG")
    txt(msp, -70, 590, 5, "ASSY ORDER 1>2>3>4>5>6>7>8. DESIGN: 24 DEG PANEL, "
                          "F=32 N, T=1.37 N-M (0.69/WHEEL, MOTOR 1.03 SF1.5)")
    title(msp, 500, -130, 400, "D-107", "GENERAL ASSEMBLY")
    save(doc, "D-107_general_assembly.dxf")


if __name__ == "__main__":
    for f in (d101, d102, d103, d104, d105, d106, d107):
        f()
    print("done")
