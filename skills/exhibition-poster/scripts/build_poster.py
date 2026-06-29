#!/usr/bin/env python
"""Build the perfected A0 exhibition poster for the innovation award.

Draws the poster at the source template's size (POSTER.pptx, A1) then scales the whole slide
up to A0 (A0 = A1 x sqrt(2), same aspect ratio, so the design is preserved exactly). Content
from the CONTENT block below — header, hook, problem/solution columns,
system-flow diagram, big impact stats, three-scale market, status cards, BMC strip, footer.

Content comes from skills/exhibition-poster/references/project_facts.md. Edit CONTENT here
(or that file) — never hand-position shapes. Writes a perfected copy; leaves the source alone.

Usage:
    python build_poster.py [SOURCE.pptx] [OUTPUT.pptx]
Defaults:
    SOURCE = C:/Users/rizk/Downloads/POSTER.pptx
    OUTPUT = C:/Users/rizk/Desktop/GRADUATION PROJECT/exhibition/POSTER_perfected.pptx
"""
import os
import sys
from pptx import Presentation
from pptx.util import Inches, Pt, Emu, Mm
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

# real assets to embed (absolute paths; mind the space in the folder name)
FIG_DIR = r"C:/Users/rizk/Desktop/GRADUATION PROJECT/integration/figures"
HERO_IMG  = r"C:/Users/rizk/Desktop/GRADUATION PROJECT/exhibition/story2.png"  # front-iso labeled sim
PROOF_IMG = os.path.join(FIG_DIR, "fig_reservoir_year.png")  # AR ~1.95 (1639x840)

# ---------------------------------------------------------------- palette ----
NAVY  = RGBColor(0x0B, 0x2A, 0x4A)
GOLD  = RGBColor(0xF4, 0xA3, 0x00)
TEAL  = RGBColor(0x1C, 0xA9, 0xC9)
SKY   = RGBColor(0xEA, 0xF4, 0xFA)
INK   = RGBColor(0x16, 0x24, 0x2E)
MUTED = RGBColor(0x5B, 0x6B, 0x76)
PAPER = RGBColor(0xFF, 0xFF, 0xFF)
LEAF  = RGBColor(0x2E, 0x9E, 0x5B)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
DISP  = "Segoe UI"          # display / headlines (bold)
BODY  = "Segoe UI"          # body

# ---------------------------------------------------------------- content ----
# Every number here traces to project_facts.md or integration_summary.json.
CONTENT = {
    "kicker": "ZC INNOVATION EXHIBITION  ·  SPECIAL INNOVATION AWARD  ·  EGYPT'S NEW CITIES",
    # short, large title (was a cramped 3-line title)
    "title": "Autonomous Solar-Regenerated\nPV-Cleaning Robot",
    "subtitle": "A rail-guided robot that makes its own distilled cleaning water from desert air "
                "with a solar-regenerated silica-gel adsorber — then cleans the panels that power it. "
                "The closed loop is validated day-by-day across six Egyptian sites.",
    "author": "Rahma Hesham El-Hamouly (202000434)   ·   Advisor: Dr. Osama Elsamni   ·   "
              "Zewail City — School of Engineering — Renewable Energy Engineering",
    "hook": "The cleaner that makes its own water — and we proved the loop closes.",
    "hook_sub": "No trucked water.   No one on the roof.   No streaks on the glass.",

    "problem": ("THE PROBLEM", [
        "PV plants in Egypt's desert cities need panels clean every day — but water is scarce "
        "and trucked in, and crews on hot rooftops are slow, costly, and a fall and heat hazard.",
        "Dust quietly erodes yield every day between cleanings.",
        "Every option fails: manual crews need water and labour, dry robots scratch the glass "
        "and leave dust, coatings wear off, doing nothing wastes power.",
    ]),
    "users": ("WHO IT'S FOR  ·  EVIDENCE", [
        "O&M teams at utility & commercial PV plants; rooftop-solar owners in NAC, New Alamein, "
        "New Mansoura; municipal solar street-light operators.",
        "Decides: O&M managers & owners.   Pays: developers, ESCOs, new-city programmes.",
        "Grounded in real NASA POWER (2020) climate for six sites, a coupled supply–demand "
        "co-sim, an as-built silica-gel dock, and a live ROS 2 + Gazebo demo. Still to gather: "
        "≥3 owner interviews; a measured 24 h harvest run [confirm].",
    ]),
    "solution": ("THE SOLUTION  —  one machine, closed loop", [
        "A silica-gel bed adsorbs water vapour from the cool night air; by day the sun "
        "regenerates it and the released vapour condenses into distilled water, banked in a dock tank.",
        "A rail robot drives itself up the 24° panel, sprays 0.3 L/m² from that tank, and a "
        "microfibre roller wipes. Each day the harvester refills; each pass draws down.",
        "Supply and demand share one clock: control on an ESP32, the live coupling a ROS 2 node "
        "(awh_water_bus.py) that banks harvest, refills the tank, and prints the balance.",
    ]),
    "whatsnew": ("WHAT'S NEW", [
        "No other panel cleaner brings its own water AND proves the loop closes.",
        "Dry robots scratch and leave dust. Wet robots need water a desert can't spare.",
        "Ours harvests distilled water from air, washes wet with ZERO external water, leaves no "
        "streaks — and is validated as self-supplying across a full year and six climates.",
    ]),

    # the headline engineering insight — featured prominently
    "insight": ("THE ENGINEERING INSIGHT",
                "The binding constraint is the summer low-RH spell, not the annual average.",
                "Sizing to a 20% annual surplus is not enough in arid sites — Benban still defers "
                "6 cleans because a dry summer stretch (days ~120–240) drains the reservoir, while "
                "humid Delta sites ride through. Design rule: size the harvester to the worst "
                "spell, not the yearly mean."),

    "flow_title": "HOW IT WORKS  —  air in, clean panels out, energy back",
    "flow": ["Night desert air", "Silica-gel bed\nadsorbs moisture", "Sun regenerates →\ndistilled water",
             "Spray 0.3 L/m²\n+ microfibre roller", "Clean panel\n→ energy powers the cycle"],

    "stats_title": "THE IMPACT  —  real co-simulation numbers (residential 9.9 kWp, 46 m²)",
    "stats": [
        ("1,435", "L/yr", "cleaning water harvested\nfrom air = its whole need", "co-sim demand_Lyr"),
        ("7.4–8.9", "MWh/yr", "energy recovered by\nkeeping the panel clean", "co-sim energy_recovered"),
        ("1.2–1.6", "%", "of array output spent\nharvesting + cleaning", "co-sim parasitic_frac"),
        ("0", "", "external water trucked in\n· workers on the roof", "design intent"),
    ],
    # two validation badges that sit beside the proof figure
    "badges": [
        ("6 / 6", "Egyptian sites where the loop\ncloses (3 scales each)", "co-sim, all sites"),
        ("~45 kg", "silica-gel bed closes the loop at NAC\n= the as-built dock (validation)",
         "co-sim sized_bed_kg"),
    ],
    "proof_caption": "Coupled dock reservoir over the year, 6 sites: the level stays positive "
                     "all year — the loop closes. The summer dip (days ~120–240) is the binding spell.",

    "market": ("BUILT TO SCALE — three sizes, one idea", [
        ("Commercial rooftops", "malls, warehouses, factories  ·  50–500 kWp"),
        ("Residential rooftops", "villas & apartments in new cities  ·  3–20 kWp  ← validated demo"),
        ("Solar street-lights", "standalone poles  ·  100–400 Wp each"),
    ], "Self-supply is scale-invariant in the co-sim. Deployment: NAC · New Alamein · New "
       "Mansoura · New Ismailia."),

    "value": ("VALUE PROPOSITION", [
        "For PV operators in Egypt's desert who can't spare water or risk rooftop crews,",
        "the robot keeps panels clean and makes its own distilled water from the air —",
        "unlike dry robots that scratch and leave dust, or wet ones that need trucked water.",
        "It pays for the water and the cleaning out of the power it recovers: 1.2–1.6% in, "
        "thousands of kWh back.",
    ]),

    "status": [
        ("PROTOTYPE STATUS", LEAF, [
            "Design finished; system coupled and validated.",
            "Year-long co-sim across 6 sites × 3 scales; live ROS 2 WaterBus self-check "
            "at NAC (f = 1.21).",
            "Bench parts procured and assembling now.",
        ]),
        ("AT THE EXHIBITION", TEAL, [
            "Live: the integrated Gazebo + ROS 2 demo — dock fills the tank, robot sweeps the "
            "24° panel, spray draws the tank down, balance prints live.",
            "Plus the bench unit and this poster.",
            "Backup if live demo fails: play the rendered demo GIF, walk the reservoir-year figure.",
        ]),
        ("NEXT VALIDATION", GOLD, [
            "Riskiest assumption: real night-time silica-gel water yield at low RH matches the model.",
            "Cheapest test: a measured 24 h harvest run, logging litres vs. RH & temp [confirm].",
            "Then: ≥3 O&M/owner interviews + a per-scale payback model [confirm].",
        ]),
    ],

    "honesty": "Honest by design: Gazebo has no fluid solver, so the tank fill is real geometry "
               "(water column = reservoir level) and the spray is a visual cue. Soiling is a "
               "1%/day model; recovered-energy is an upper bound vs. a never-cleaned panel.",

    "bmc": ("BUSINESS MODEL  ·  how it moves beyond the exhibition",
            "Cleaning-as-a-service or unit sale  ·  Channels: solar EPC/O&M firms & new-city "
            "programmes  ·  Partners: NREA / Benban developers, new-city authorities  ·  "
            "Off-the-shelf BOM; possible sustainability subsidy.  Per-scale payback model [confirm]."),

    "footer": "Scan for the live demo video and the full technical report",
}

# ---------------------------------------------------------------- helpers ----
def _para(tf, text, size, color, bold=False, align=PP_ALIGN.LEFT, font=BODY,
          first=False, sa=4, sb=0, line=1.04, bullet=False):
    p = tf.paragraphs[0] if first else tf.add_paragraph()
    p.alignment = align
    p.space_after = Pt(sa); p.space_before = Pt(sb); p.line_spacing = line
    r = p.add_run(); r.text = ("•  " + text) if bullet else text
    f = r.font
    f.size = Pt(size); f.bold = bold; f.name = font; f.color.rgb = color
    return p

def rect(slide, x, y, w, h, fill=None, line=None, line_w=0.0, shape=MSO_SHAPE.RECTANGLE,
         shadow=False):
    s = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    if fill is None:
        s.fill.background()
    else:
        s.fill.solid(); s.fill.fore_color.rgb = fill
    if line is None:
        s.line.fill.background()
    else:
        s.line.color.rgb = line; s.line.width = Pt(line_w or 1.0)
    s.shadow.inherit = False
    return s

def textbox(slide, x, y, w, h, anchor=MSO_ANCHOR.TOP, wrap=True,
            ml=0.16, mr=0.16, mt=0.08, mb=0.08):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = wrap; tf.vertical_anchor = anchor
    tf.margin_left = Inches(ml); tf.margin_right = Inches(mr)
    tf.margin_top = Inches(mt); tf.margin_bottom = Inches(mb)
    return tf

def card(slide, x, y, w, h, headline, lines, accent, head_size=27, body_size=18):
    rect(slide, x, y, w, h, fill=SKY, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
    rect(slide, x, y, 0.22, h, fill=accent, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
    tf = textbox(slide, x + 0.30, y + 0.12, w - 0.5, h - 0.24)
    _para(tf, headline, head_size, NAVY, bold=True, font=DISP, first=True, sa=8)
    for ln in lines:
        _para(tf, ln, body_size, INK, bullet=True, sa=6, line=1.06)

def rescale_to(prs, target_w, target_h):
    """Scale the finished slide (geometry + fonts + spacing) to a new page size.

    A0 and A1 share the same sqrt(2) aspect ratio, so this preserves the design exactly —
    every shape, image, and font grows by the same factor and stays aligned to the edges.
    """
    sx = target_w / prs.slide_width
    sy = target_h / prs.slide_height
    fscale = (sx + sy) / 2.0
    for slide in prs.slides:
        for shp in slide.shapes:
            shp.left   = int(round(shp.left * sx))
            shp.top    = int(round(shp.top * sy))
            shp.width  = int(round(shp.width * sx))
            shp.height = int(round(shp.height * sy))
            try:
                if shp.line is not None and shp.line.width is not None:
                    shp.line.width = int(round(int(shp.line.width) * fscale))
            except (TypeError, ValueError):
                pass
            if shp.has_text_frame:
                for p in shp.text_frame.paragraphs:
                    if p.space_after is not None:
                        p.space_after = int(round(int(p.space_after) * fscale))
                    if p.space_before is not None:
                        p.space_before = int(round(int(p.space_before) * fscale))
                    for r in p.runs:
                        if r.font.size is not None:
                            r.font.size = Pt(round(r.font.size.pt * fscale, 1))
    prs.slide_width = int(round(target_w))
    prs.slide_height = int(round(target_h))

def fitted_picture(slide, path, x, y, w, h):
    """Place an image inside the box (x,y,w,h), preserving aspect ratio and centring it."""
    from PIL import Image
    iw, ih = Image.open(path).size
    ar = iw / ih
    box_ar = w / h
    if ar > box_ar:                       # image wider than box -> fit to width
        dw = w; dh = w / ar
    else:                                  # taller -> fit to height
        dh = h; dw = h * ar
    px = x + (w - dw) / 2
    py = y + (h - dh) / 2
    slide.shapes.add_picture(path, Inches(px), Inches(py), Inches(dw), Inches(dh))
    return px, py, dw, dh

# ---------------------------------------------------------------- build ------
def build(src, out):
    prs = Presentation(src)
    W = Emu(prs.slide_width).inches
    H = Emu(prs.slide_height).inches
    slide = prs.slides[0]
    for sh in list(slide.shapes):                      # clear the template
        sh._element.getparent().remove(sh._element)

    M = 0.85
    IN = W - 2 * M                                      # inner width
    rect(slide, 0, 0, W, H, fill=PAPER)                # paper background

    colw = (IN - 0.7) / 2                               # two-column body width
    rx = M + colw + 0.7                                  # right column x

    G = 0.24                                             # standard vertical gap

    # ---- header band (navy, taller for the 3-line registered title) ----------
    HB = 4.55
    rect(slide, 0, 0, W, 0.18, fill=GOLD)
    rect(slide, 0, 0.18, W, HB - 0.18, fill=NAVY)
    tf = textbox(slide, M, 0.28, IN, HB - 0.40)
    _para(tf, CONTENT["kicker"], 21, GOLD, bold=True, font=DISP, first=True, sa=6)
    for i, line in enumerate(CONTENT["title"].split("\n")):
        _para(tf, line, 50, WHITE, bold=True, font=DISP, sa=0, line=0.98)
    _para(tf, CONTENT["subtitle"], 20, SKY, sb=9, sa=3, line=1.04)
    _para(tf, CONTENT["author"], 18, TEAL, bold=True, sb=6, line=1.03)

    # ---- hook strip (gold) ---------------------------------------------------
    y = HB + 0.10
    HK = 1.28
    rect(slide, 0, y, W, HK, fill=GOLD)
    tf = textbox(slide, M, y + 0.04, IN, HK - 0.08, anchor=MSO_ANCHOR.MIDDLE)
    _para(tf, CONTENT["hook"], 41, NAVY, bold=True, font=DISP, align=PP_ALIGN.CENTER,
          first=True, sa=4, line=0.98)
    _para(tf, CONTENT["hook_sub"], 24, NAVY, align=PP_ALIGN.CENTER, sa=0)

    # ---- hero band: left = problem+users cards, right = hero image -----------
    y = y + HK + G
    ch = 2.35
    card(slide, M, y, colw, ch, *CONTENT["problem"], accent=GOLD, head_size=24, body_size=17)
    card(slide, M, y + ch + 0.22, colw, ch, *CONTENT["users"], accent=TEAL,
         head_size=24, body_size=16)
    # hero image panel on the right (navy frame + caption ribbon)
    hh = 2 * ch + 0.22
    rect(slide, rx, y, colw, hh, fill=NAVY, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
    cap_h = 0.70
    fitted_picture(slide, HERO_IMG, rx + 0.14, y + 0.14, colw - 0.28, hh - cap_h - 0.24)
    t = textbox(slide, rx + 0.18, y + hh - cap_h, colw - 0.36, cap_h, anchor=MSO_ANCHOR.MIDDLE)
    _para(t, "LIVE INTEGRATED DEMO  —  the AWH dock fills the tank, the robot sweeps the "
             "24° panel, the water balance prints (Gazebo + ROS 2).", 16, SKY, font=DISP,
          align=PP_ALIGN.CENTER, first=True, line=1.04)

    # ---- solution + what's new (two cards) -----------------------------------
    y = y + hh + G
    sc_h = 2.40
    card(slide, M, y, colw, sc_h, *CONTENT["solution"], accent=TEAL, head_size=23, body_size=16)
    card(slide, rx, y, colw, sc_h, *CONTENT["whatsnew"], accent=GOLD, head_size=23, body_size=16)

    # ---- engineering insight band (full width, the headline finding) ---------
    y = y + sc_h + G
    ih = 1.60
    itag, ihead, ibody = CONTENT["insight"]
    rect(slide, M, y, IN, ih, fill=NAVY, line=GOLD, line_w=3.0,
         shape=MSO_SHAPE.ROUNDED_RECTANGLE)
    t = textbox(slide, M + 0.35, y + 0.10, IN - 0.7, ih - 0.20, anchor=MSO_ANCHOR.MIDDLE)
    _para(t, itag, 19, GOLD, bold=True, font=DISP, first=True, sa=3)
    _para(t, ihead, 28, WHITE, bold=True, font=DISP, sa=5, line=1.0)
    _para(t, ibody, 18, SKY, sa=0, line=1.05)

    # ---- system flow band ----------------------------------------------------
    y = y + ih + G
    tf = textbox(slide, M, y, IN, 0.50)
    _para(tf, CONTENT["flow_title"], 27, NAVY, bold=True, font=DISP, first=True)
    fy = y + 0.62
    fh = 1.45
    n = len(CONTENT["flow"])
    gap = 0.48
    bw = (IN - (n - 1) * gap) / n
    for i, label in enumerate(CONTENT["flow"]):
        bx = M + i * (bw + gap)
        fill = GOLD if i in (0, n - 1) else NAVY
        tcol = NAVY if i in (0, n - 1) else WHITE
        rect(slide, bx, fy, bw, fh, fill=fill, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
        t = textbox(slide, bx, fy, bw, fh, anchor=MSO_ANCHOR.MIDDLE, ml=0.07, mr=0.07)
        first = True
        for ln in label.split("\n"):
            _para(t, ln, 19, tcol, bold=True, font=DISP, align=PP_ALIGN.CENTER,
                  first=first, sa=0, line=1.0); first = False
        if i < n - 1:
            rect(slide, bx + bw + 0.03, fy + fh / 2 - 0.24, gap - 0.06, 0.48,
                 fill=TEAL, shape=MSO_SHAPE.CHEVRON)

    # ---- impact band: 2x2 big-number grid (left) + proof figure (right) ------
    y = fy + fh + G
    tf = textbox(slide, M, y, IN, 0.50)
    _para(tf, CONTENT["stats_title"], 27, NAVY, bold=True, font=DISP, first=True)
    sy = y + 0.54
    band_h = 3.80
    # left half: 2x2 grid of stat cards
    gcols, grows = 2, 2
    gsg = 0.28
    sw = (colw - (gcols - 1) * gsg) / gcols
    s_h = (band_h - (grows - 1) * gsg) / grows
    for i, (num, unit, label, basis) in enumerate(CONTENT["stats"]):
        r_, c_ = divmod(i, gcols)
        sx = M + c_ * (sw + gsg)
        scy = sy + r_ * (s_h + gsg)
        rect(slide, sx, scy, sw, s_h, fill=SKY, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
        rect(slide, sx, scy, sw, 0.14, fill=GOLD, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
        t = textbox(slide, sx, scy + 0.14, sw, s_h - 0.24, anchor=MSO_ANCHOR.MIDDLE,
                    ml=0.10, mr=0.10)
        nsize = 76 if len(num) <= 4 else 52
        _para(t, num, nsize, GOLD, bold=True, font=DISP, align=PP_ALIGN.CENTER,
              first=True, sa=0, line=0.88)
        if unit:
            _para(t, unit, 24, NAVY, bold=True, font=DISP, align=PP_ALIGN.CENTER, sa=2)
        for ln in label.split("\n"):
            _para(t, ln, 17, INK, align=PP_ALIGN.CENTER, sa=0, line=1.0)
        _para(t, basis, 13, MUTED, align=PP_ALIGN.CENTER, sb=2)
    # right half: proof figure card with caption
    rect(slide, rx, sy, colw, band_h, fill=PAPER, line=NAVY, line_w=1.5,
         shape=MSO_SHAPE.ROUNDED_RECTANGLE)
    t = textbox(slide, rx + 0.22, sy + 0.10, colw - 0.44, 0.45)
    _para(t, "PROOF — the loop closes all year", 21, NAVY, bold=True, font=DISP, first=True)
    fitted_picture(slide, PROOF_IMG, rx + 0.18, sy + 0.62, colw - 0.36, band_h - 1.55)
    t = textbox(slide, rx + 0.22, sy + band_h - 0.85, colw - 0.44, 0.78)
    _para(t, CONTENT["proof_caption"], 14, MUTED, first=True, line=1.04)

    # ---- validation badge strip (2 across, full width) -----------------------
    y = sy + band_h + G
    bs_h = 1.15
    bsg = 0.4
    bsw = (IN - bsg) / 2
    for i, (num, label, basis) in enumerate(CONTENT["badges"]):
        bx = M + i * (bsw + bsg)
        rect(slide, bx, y, bsw, bs_h, fill=NAVY, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
        rect(slide, bx, y, 0.22, bs_h, fill=LEAF, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
        # big gold number on the left of the badge
        nbw = 2.3
        tn = textbox(slide, bx + 0.40, y + 0.08, nbw, bs_h - 0.16, anchor=MSO_ANCHOR.MIDDLE)
        _para(tn, num, 44, GOLD, bold=True, font=DISP, first=True, line=0.9)
        # label + basis to the right of the number
        tl = textbox(slide, bx + 0.40 + nbw, y + 0.08, bsw - 0.55 - nbw, bs_h - 0.16,
                     anchor=MSO_ANCHOR.MIDDLE, ml=0.0)
        for j, ln in enumerate(label.split("\n")):
            _para(tl, ln, 17, WHITE, first=(j == 0), sa=0, line=1.04)
        _para(tl, basis, 13, TEAL, sb=2)

    # ---- market (left) + value proposition (right) ---------------------------
    y = y + bs_h + G
    rh = 3.05
    mtitle, scales, mfoot = CONTENT["market"]
    rect(slide, M, y, colw, rh, fill=PAPER, line=NAVY, line_w=1.5,
         shape=MSO_SHAPE.ROUNDED_RECTANGLE)
    t = textbox(slide, M + 0.25, y + 0.12, colw - 0.5, rh - 0.24)
    _para(t, mtitle, 25, NAVY, bold=True, font=DISP, first=True, sa=8)
    for name, desc in scales:
        _para(t, name, 21, TEAL, bold=True, font=DISP, sa=0, bullet=True)
        _para(t, desc, 17, INK, sa=6, line=1.02)
    _para(t, mfoot, 15, MUTED, sb=5, line=1.03)
    vtitle, vlines = CONTENT["value"]
    rect(slide, rx, y, colw, rh, fill=NAVY, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
    t = textbox(slide, rx + 0.28, y + 0.14, colw - 0.55, rh - 0.28, anchor=MSO_ANCHOR.MIDDLE)
    _para(t, vtitle, 25, GOLD, bold=True, font=DISP, first=True, sa=8)
    for ln in vlines:
        _para(t, ln, 19, WHITE, sa=6, line=1.06)

    # ---- status row: three cards ---------------------------------------------
    y = y + rh + G
    sh3 = 2.95
    sg3 = 0.50
    sw3 = (IN - 2 * sg3) / 3
    for i, (head, accent, lines) in enumerate(CONTENT["status"]):
        sx = M + i * (sw3 + sg3)
        card(slide, sx, y, sw3, sh3, head, lines, accent, head_size=21, body_size=15)

    # ---- honesty note (left) + business model (right) on one row ------------
    y = y + sh3 + G
    bh = 1.45
    rect(slide, M, y, colw, bh, fill=SKY, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
    rect(slide, M, y, 0.22, bh, fill=GOLD, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
    t = textbox(slide, M + 0.32, y + 0.10, colw - 0.55, bh - 0.20, anchor=MSO_ANCHOR.MIDDLE)
    _para(t, "HONEST BY DESIGN", 19, NAVY, bold=True, font=DISP, first=True, sa=4)
    _para(t, CONTENT["honesty"].split(": ", 1)[1], 15, INK, line=1.05)
    btitle, btext = CONTENT["bmc"]
    rect(slide, rx, y, colw, bh, fill=NAVY, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
    rect(slide, rx, y, 0.22, bh, fill=TEAL, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
    t = textbox(slide, rx + 0.32, y + 0.10, colw - 0.55, bh - 0.20, anchor=MSO_ANCHOR.MIDDLE)
    _para(t, "BUSINESS MODEL  ·  beyond the exhibition", 19, GOLD, bold=True, font=DISP,
          first=True, sa=4)
    _para(t, btext, 15, WHITE, line=1.05)

    # ---- footer --------------------------------------------------------------
    content_bottom = y + bh
    fy2 = H - 1.05
    rect(slide, 0, fy2, W, 1.05, fill=NAVY)
    rect(slide, 0, fy2, W, 0.10, fill=GOLD)
    t = textbox(slide, M, fy2 + 0.06, IN - 1.6, 0.99, anchor=MSO_ANCHOR.MIDDLE)
    _para(t, CONTENT["footer"], 18, WHITE, bold=True, font=DISP,
          align=PP_ALIGN.LEFT, first=True, line=1.05)
    # QR placeholder block in the footer's right corner
    qr = W - M - 0.85
    rect(slide, qr, fy2 + 0.16, 0.78, 0.78, fill=PAPER, line=GOLD, line_w=1.5)
    tq = textbox(slide, qr, fy2 + 0.16, 0.78, 0.78, anchor=MSO_ANCHOR.MIDDLE,
                 ml=0.02, mr=0.02)
    _para(tq, "QR", 18, NAVY, bold=True, font=DISP, align=PP_ALIGN.CENTER, first=True)

    flag = "  <-- OVERFLOW" if content_bottom > fy2 else "  OK"
    print(f"[layout] content bottom = {content_bottom:.2f} in;  footer top = {fy2:.2f} in;  "
          f"page H = {H:.2f} in{flag}  (A1 build space)")

    rescale_to(prs, Mm(841), Mm(1189))                 # scale the whole layout up to A0
    prs.save(out)
    Wn = Emu(prs.slide_width).inches; Hn = Emu(prs.slide_height).inches
    print("saved:", out, f"({Wn:.2f} x {Hn:.2f} in  =  A0 portrait)")

if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else r"C:/Users/rizk/Downloads/POSTER.pptx"
    out = sys.argv[2] if len(sys.argv) > 2 else \
        r"C:/Users/rizk/Desktop/GRADUATION PROJECT/exhibition/POSTER_perfected.pptx"
    build(src, out)
