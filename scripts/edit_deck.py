# -*- coding: utf-8 -*-
"""Edit the defense deck: fix text errors, swap AI charts for real figures, add Gazebo render."""
import os, shutil, fitz
from pptx import Presentation
from pptx.util import Emu, Inches
from PIL import Image

ROOT = r"C:\Users\rizk\Desktop\GRADUATION PROJECT"
DECK = os.path.join(ROOT, "Autonomous Thermoelectric Water-Harvesting Robot for PV Cleaning.pptx")
TMP  = os.path.join(ROOT, "output", "_deckfig")
os.makedirs(TMP, exist_ok=True)

# 1) render the real PDF figures to PNG
def pdf2png(pdf, png, dpi=200):
    d = fitz.open(os.path.join(ROOT, pdf)); p = d[0]
    pix = p.get_pixmap(matrix=fitz.Matrix(dpi/72, dpi/72))
    pix.save(png); d.close(); return png

fig = {
    4 : pdf2png("figures/fig_cop_sec_dT.pdf",   os.path.join(TMP,"s4.png")),
    10: pdf2png("figures/fig_monthly_climate.pdf", os.path.join(TMP,"s10.png")),
    11: pdf2png("figures/nac_monthly_water.pdf", os.path.join(TMP,"s11.png")),
    18: pdf2png("figures/fig_diurnal.pdf",       os.path.join(TMP,"s18.png")),
}
GAZ = os.path.join(ROOT, "figures", "slides", "gazebo_labeled_overview.png")

# 2) backup + open
shutil.copy(DECK, DECK + ".bak")
prs = Presentation(DECK)

# 3) text replacements (run-level, then paragraph-level fallback)
REPL = {
    "[Author Name]": "Rahma Hesham",
    "02 May, 2029": "June 2026",
    "Rimberio University": "Zewail City of Science and Technology",
    "TEC modules & heat sinks: 3,200 EGP": "TEC harvester (tiles, coolers, fans): 2,240 EGP",
    "Motors, PCB & electronics: 2,750 EGP": "Drive, power & control electronics: 6,710 EGP",
    "Rail & mechanical structure: 85,000 EGP": "Station battery bank — dominant line item",
    "Raspberry Pi 4 & ESP32 control: 42,600 EGP": "PV, MPPT, 38 TEC tiles & rail structure",
    "4,800 m² array": "46 m²/clean × 104 cleans",
}
def fix_text(tf):
    for para in tf.paragraphs:
        joined = "".join(r.text for r in para.runs)
        hit = [k for k in REPL if k in joined]
        if not hit:
            continue
        # try run-level first (preserves formatting)
        done_in_run = False
        for r in para.runs:
            for k in list(REPL):
                if k in r.text:
                    r.text = r.text.replace(k, REPL[k]); done_in_run = True
        # paragraph-level fallback for substrings split across runs
        joined2 = "".join(r.text for r in para.runs)
        if any(k in joined2 for k in REPL):
            new = joined2
            for k in REPL: new = new.replace(k, REPL[k])
            if para.runs:
                para.runs[0].text = new
                for r in para.runs[1:]: r.text = ""

def walk_text(shapes):
    for sh in shapes:
        if 'GROUP' in str(sh.shape_type): walk_text(sh.shapes)
        elif sh.has_text_frame: fix_text(sh.text_frame)

for s in prs.slides: walk_text(s.shapes)

# 4) swap the AI charts for real figures (remove old picture, add fitted new one)
def fit(L,T,W,H,iw,ih):
    ar = iw/ih
    nW = W; nH = int(W/ar)
    if nH > H: nH = H; nW = int(H*ar)
    return L + (W-nW)//2, T + (H-nH)//2, nW, nH

def replace_pic(slide, png):
    pic = next((sh for sh in slide.shapes if 'PICTURE' in str(sh.shape_type)), None)
    if pic is None: return False
    L,T,W,H = pic.left, pic.top, pic.width, pic.height
    iw,ih = Image.open(png).size
    pic._element.getparent().remove(pic._element)
    nL,nT,nW,nH = fit(L,T,W,H,iw,ih)
    slide.shapes.add_picture(png, nL,nT,nW,nH)
    return True

for sidx, png in fig.items():
    ok = replace_pic(prs.slides[sidx-1], png)
    print(f"slide {sidx} image swap:", ok)

# 5) add the labelled Gazebo render to slide 17 (validation), lower-left empty area
s17 = prs.slides[17-1]
iw,ih = Image.open(GAZ).size
ar = iw/ih
W = Inches(7.2); H = int(W/ar)
maxH = Inches(4.3)
if H > maxH: H = maxH; W = int(H*ar)
s17.shapes.add_picture(GAZ, Inches(1.32), Inches(6.55), W, H)
print("slide 17 gazebo added")

prs.save(DECK)
print("SAVED")
