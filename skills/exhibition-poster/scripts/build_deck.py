#!/usr/bin/env python
"""Build the perfected "innovation for impact" pitch deck for the ZC Innovation Award.

Opens the 10-slide skeleton (keeps its theme), fills all 10 slides per the rubric mapping
in references/award_rubric.md, in Rahma's voice: one idea per slide, the headline states the
takeaway, the body proves it in a few words. Embeds the hero image on slide 5 (solution /
prototype) and the proof figure on slide 8 (impact). Applies the palette accents to titles
and a consistent footer (short name . author . slide #).

Every number traces to project_facts.md / integration_summary.json. Anything unconfirmed is
tagged [confirm]. Writes a perfected copy; leaves the Downloads source untouched.

Usage:
    python build_deck.py [SOURCE.pptx] [OUTPUT.pptx]
Defaults:
    SOURCE = C:/Users/rizk/Downloads/innovation for impact.pptx
    OUTPUT = C:/Users/rizk/Desktop/GRADUATION PROJECT/exhibition/innovation_for_impact_filled.pptx
"""
import os
import sys
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

# ---------------------------------------------------------------- palette ----
NAVY  = RGBColor(0x0B, 0x2A, 0x4A)
GOLD  = RGBColor(0xF4, 0xA3, 0x00)
TEAL  = RGBColor(0x1C, 0xA9, 0xC9)
SKY   = RGBColor(0xEA, 0xF4, 0xFA)
INK   = RGBColor(0x16, 0x24, 0x2E)
MUTED = RGBColor(0x5B, 0x6B, 0x76)
LEAF  = RGBColor(0x2E, 0x9E, 0x5B)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
DISP  = "Segoe UI"
BODY  = "Segoe UI"

FIG_DIR = r"C:/Users/rizk/Desktop/GRADUATION PROJECT/integration/figures"
HERO_IMG  = r"C:/Users/rizk/Desktop/GRADUATION PROJECT/exhibition/story2.png"  # front-iso labeled sim
PROOF_IMG = os.path.join(FIG_DIR, "fig_reservoir_year.png")

SHORT = "Solar-AWH PV-Cleaning Robot"
AUTHOR = "Rahma El-Hamouly"

# ---------------------------------------------------------------- content ----
# (slide_index 0-based, headline, [body lines], optional big-number, optional note)
TITLE = {
    "title": "Autonomous Solar-Regenerated Atmospheric Water-Harvesting Robot "
             "for Photovoltaic Panel Cleaning",
    "hook": "The cleaner that makes its own water — and we proved the loop closes.",
    "author": "Rahma Hesham El-Hamouly  (ID 202000434)  ·  solo project",
    "org": "Zewail City of Science and Technology  ·  School of Engineering  ·  "
           "Renewable Energy Engineering (ENG-REE)",
    "advisor": "Advisor: Dr. Osama Elsamni",
    "event": "ZC Innovation Exhibition  ·  Special Innovation Award  ·  27 June 2026",
}

SLIDES = {
    2: {  # Project title & team
        "head": "One robot that harvests its own water, then cleans the panels that power it.",
        "body": [
            "Project: Autonomous Solar-Regenerated Atmospheric Water-Harvesting Robot "
            "for Photovoltaic Panel Cleaning.",
            "Rahma Hesham El-Hamouly (202000434) — solo graduation project.",
            "Zewail City — School of Engineering — Renewable Energy Engineering.",
            "Advisor: Dr. Osama Elsamni.",
            "Type: hardware device · prototype · environmental-impact solution.",
        ],
    },
    3: {  # Main problem / industry gap
        "head": "Desert solar plants need clean panels every day — but water and rooftop crews "
                "are exactly what a desert can't spare.",
        "body": [
            "Dust quietly cuts power every day between cleanings.",
            "Cleaning water is scarce and trucked in; crews on hot rooftops are slow, costly, "
            "and a fall and heat hazard.",
            "Every option fails: manual crews need water and labour, dry robots scratch and "
            "leave dust, coatings wear off, doing nothing wastes power.",
        ],
    },
    4: {  # Target users / beneficiaries + evidence
        "head": "For the people who keep desert PV running — and we have the data, not just a hunch.",
        "body": [
            "User: O&M teams at utility & commercial PV plants; rooftop owners in NAC, "
            "New Alamein, New Mansoura; municipal street-light operators.",
            "Decides: O&M managers & owners.  Pays: developers, ESCOs, new-city programmes.",
            "Evidence: real NASA POWER (2020) climate for six sites, a coupled supply–demand "
            "co-sim, an as-built silica-gel dock, a live ROS 2 + Gazebo demo.",
            "Still to gather: 3+ owner interviews and a measured 24 h harvest run [confirm].",
        ],
    },
    5: {  # Solution & prototype (HERO image)
        "head": "A solar-regenerated silica-gel bed makes the water; a rail robot does the "
                "cleaning; one clock ties supply to demand.",
        "body": [
            "A silica-gel bed adsorbs moisture from the night air; by day the sun regenerates it "
            "and the released vapour condenses into the dock tank.",
            "The robot drives up the 24° panel, sprays 0.3 L/m², a microfibre roller wipes.",
            "Each day the harvester refills; each pass draws down — coupled live by a ROS 2 "
            "node (awh_water_bus.py) on an ESP32-controlled robot.",
            "Stage: designed, coupled, and validated in a year-long co-sim + live demo.",
        ],
        "image": HERO_IMG,
        "caption": "Live integrated Gazebo + ROS 2 demo — tank fills, robot sweeps, balance prints.",
    },
    6: {  # Value proposition
        "head": "Clean panels with zero trucked water and nobody on the roof — paid for out of "
                "the power it recovers.",
        "body": [
            "For PV operators in Egypt's desert who can't spare water or risk rooftop crews,",
            "the robot keeps panels clean and makes its own distilled water from the air —",
            "unlike dry robots that scratch and leave dust, or wet ones that need trucked water.",
            "It spends 1.2–1.6% of the array's output and returns thousands of kWh a year.",
        ],
    },
    7: {  # Market / sector research
        "head": "One idea, three scales — and self-supply holds at every one.",
        "body": [
            "Commercial rooftops: malls, warehouses, factories (50–500 kWp).",
            "Residential rooftops: villas & apartments in new cities (3–20 kWp) — the validated "
            "demo scale.",
            "Solar street-lights: standalone poles (100–400 Wp each).",
            "Deployment targets: NAC · New Alamein · New Mansoura · New Ismailia. "
            "Self-supply is scale-invariant in the co-sim.",
        ],
    },
    8: {  # Potential impact (PROOF figure)
        "head": "Across all six Egyptian sites, the robot harvests every litre it needs — the "
                "loop closes.",
        "body": [
            "1,435 L/yr harvested from air = the whole residential cleaning need.",
            "7.4–8.9 MWh/yr recovered by keeping the panel clean (upper bound vs. a "
            "never-cleaned panel).",
            "1.2–1.6% parasitic load; 0 trucked water; 0 rooftop workers.",
            "Insight: the binding constraint is the summer low-RH spell, not the annual "
            "average — size to the worst spell.",
        ],
        "image": PROOF_IMG,
        "caption": "Coupled dock reservoir over the year, 6 sites: stays positive all year; the "
                   "summer dip (days ~120–240) is the binding spell.",
    },
    9: {  # Business model / adoption pathway
        "head": "It leaves the exhibition as cleaning-as-a-service or a unit sale, on an "
                "off-the-shelf BOM.",
        "body": [
            "Segments: utility & commercial PV O&M, residential owners, municipal street-lights.",
            "Channels: solar EPC/O&M firms and new-city sustainability programmes.",
            "Partners: NREA / Benban developers, new-city authorities; possible subsidy.",
            "Revenue: service contract or unit sale.  Per-scale payback model [confirm].",
        ],
    },
    10: {  # Next validation steps
        "head": "One bench test stands between the model and the field.",
        "body": [
            "Riskiest assumption: real night-time silica-gel water yield at low RH matches the modelled harvest.",
            "Cheapest test: a measured 24 h harvest run, logging litres vs. RH and temp, "
            "against the co-sim [confirm].",
            "Then: 3+ O&M/owner interviews and a per-scale payback model [confirm].",
            "Ask: a site partner for a 2-week field pilot at residential scale.",
        ],
    },
}

# ---------------------------------------------------------------- helpers ----
def set_title(slide, text, accent=NAVY, size=30):
    """Fill the slide's title placeholder, restyled in the palette."""
    ph = None
    for sh in slide.placeholders:
        if sh.placeholder_format.idx == 0:
            ph = sh; break
    if ph is None:
        return None
    tf = ph.text_frame
    tf.clear()
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.LEFT
    r = p.add_run(); r.text = text
    f = r.font
    f.name = DISP; f.bold = True; f.size = Pt(size); f.color.rgb = accent
    return ph

def fill_body(slide, lines, size=19, accent=TEAL):
    """Fill the content placeholder (idx 1) with bullets in ink, accent dots."""
    ph = None
    for sh in slide.placeholders:
        if sh.placeholder_format.idx == 1:
            ph = sh; break
    if ph is None:
        return None
    tf = ph.text_frame
    tf.clear()
    tf.word_wrap = True
    for i, ln in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = PP_ALIGN.LEFT
        p.space_after = Pt(8); p.line_spacing = 1.08
        rb = p.add_run(); rb.text = "▸ "
        rb.font.name = DISP; rb.font.bold = True; rb.font.size = Pt(size); rb.font.color.rgb = accent
        rt = p.add_run(); rt.text = ln
        rt.font.name = BODY; rt.font.size = Pt(size); rt.font.color.rgb = INK
    return ph

def fitted_picture(slide, path, x, y, w, h):
    from PIL import Image
    iw, ih = Image.open(path).size
    ar = iw / ih; box_ar = w / h
    if ar > box_ar:
        dw = w; dh = w / ar
    else:
        dh = h; dw = h * ar
    px = x + (w - dw) / 2; py = y + (h - dh) / 2
    slide.shapes.add_picture(path, Inches(px), Inches(py), Inches(dw), Inches(dh))
    return px, py, dw, dh

def add_rect(slide, x, y, w, h, fill=None, shape=MSO_SHAPE.RECTANGLE):
    s = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    if fill is None:
        s.fill.background()
    else:
        s.fill.solid(); s.fill.fore_color.rgb = fill
    s.line.fill.background(); s.shadow.inherit = False
    return s

def add_text(slide, x, y, w, h, runs, anchor=MSO_ANCHOR.TOP, align=PP_ALIGN.LEFT,
             wrap=True, line=1.05):
    """runs = list of (text, size, color, bold, font)."""
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame; tf.word_wrap = wrap; tf.vertical_anchor = anchor
    tf.margin_left = Inches(0.05); tf.margin_right = Inches(0.05)
    tf.margin_top = Inches(0.02); tf.margin_bottom = Inches(0.02)
    for i, (text, size, color, bold, font) in enumerate(runs):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align; p.line_spacing = line; p.space_after = Pt(4)
        r = p.add_run(); r.text = text
        r.font.name = font; r.font.size = Pt(size); r.font.bold = bold; r.font.color.rgb = color
    return tb

def add_footer(slide, W, H, n):
    """Consistent footer: short name . author . slide # on a slim navy bar."""
    bar_h = 0.32
    add_rect(slide, 0, H - bar_h, W, bar_h, fill=NAVY)
    add_rect(slide, 0, H - bar_h, W, 0.04, fill=GOLD)
    add_text(slide, 0.35, H - bar_h, W - 0.7, bar_h,
             [(f"{SHORT}   ·   {AUTHOR}", 10, WHITE, True, DISP)],
             anchor=MSO_ANCHOR.MIDDLE, align=PP_ALIGN.LEFT)
    add_text(slide, W - 1.2, H - bar_h, 0.85, bar_h,
             [(str(n), 10, GOLD, True, DISP)],
             anchor=MSO_ANCHOR.MIDDLE, align=PP_ALIGN.RIGHT)

# ---------------------------------------------------------------- build ------
def build(src, out):
    prs = Presentation(src)
    W = Emu(prs.slide_width).inches
    H = Emu(prs.slide_height).inches

    # ---- slide 1: title slide ------------------------------------------------
    s1 = prs.slides[0]
    # navy band down the left + gold rule for identity, theme stays
    add_rect(s1, 0, 0, W, 0.16, fill=GOLD)
    add_rect(s1, 0, H - 1.55, W, 1.55, fill=NAVY)
    add_rect(s1, 0, H - 1.55, W, 0.06, fill=GOLD)
    # remove any empty title-slide placeholders so no "click to add" prompt remains —
    # we draw the title + hook as textboxes (robust and theme-independent)
    for ph in list(s1.placeholders):
        if ph.placeholder_format.idx in (0, 1) and not ph.text_frame.text.strip():
            ph._element.getparent().remove(ph._element)
    # draw the title + hook directly as textboxes
    add_text(s1, 0.8, 1.4, W - 1.6, 2.6,
             [(TITLE["title"], 33, NAVY, True, DISP)], line=1.02)
    add_text(s1, 0.8, 3.95, W - 1.6, 1.0,
             [(TITLE["hook"], 22, GOLD, True, DISP)], line=1.02)
    # footer block (white text on navy)
    add_text(s1, 0.8, H - 1.42, W - 1.6, 1.3, [
        (TITLE["author"], 15, WHITE, True, DISP),
        (TITLE["org"], 13, SKY, False, BODY),
        (TITLE["advisor"] + "    ·    " + TITLE["event"], 13, TEAL, True, BODY),
    ], line=1.18)
    add_footer(s1, W, H, 1)

    # ---- slides 2-10 ---------------------------------------------------------
    for idx in range(2, 11):
        slide = prs.slides[idx - 1]
        spec = SLIDES[idx]
        set_title(slide, spec["head"], accent=NAVY, size=27)
        # narrow the content placeholder if the slide carries an image (text left, image right)
        has_img = "image" in spec
        if has_img:
            # shrink content placeholder to the left half
            for sh in slide.placeholders:
                if sh.placeholder_format.idx == 1:
                    sh.left = Inches(0.55); sh.top = Inches(1.95)
                    sh.width = Inches(6.7); sh.height = Inches(4.85)
            fill_body(slide, spec["body"], size=16)
            # image card on the right
            ix, iy, iw, ih = 7.45, 1.95, W - 7.45 - 0.55, 4.55
            add_rect(slide, ix, iy, iw, ih, fill=NAVY, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
            fitted_picture(slide, spec["image"], ix + 0.12, iy + 0.12, iw - 0.24, ih - 0.78)
            add_text(slide, ix + 0.18, iy + ih - 0.66, iw - 0.36, 0.6,
                     [(spec["caption"], 11, SKY, False, BODY)],
                     anchor=MSO_ANCHOR.MIDDLE, align=PP_ALIGN.CENTER, line=1.03)
        else:
            fill_body(slide, spec["body"], size=19)
        # accent rule under the title
        add_rect(slide, 0.66, 1.78, 2.6, 0.07, fill=GOLD)
        add_footer(slide, W, H, idx)

    prs.save(out)
    print("saved:", out, f"({W:.2f} x {H:.2f} in, {len(prs.slides)} slides)")

if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else r"C:/Users/rizk/Downloads/innovation for impact.pptx"
    out = sys.argv[2] if len(sys.argv) > 2 else \
        r"C:/Users/rizk/Desktop/GRADUATION PROJECT/exhibition/innovation_for_impact_filled.pptx"
    build(src, out)
