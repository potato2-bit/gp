---
name: framework-extraction
description: >
  Use this skill to extract a template, diagram, form, canvas, or framework shown inside a
  photo, screenshot, scanned page, or PDF and reproduce it faithfully as an editable,
  filled-in document. Trigger whenever the user says "apply what you see in the photo/PDF",
  "fill in this template", "recreate this diagram/slide/form", "read the frameworks in this
  file", or hands over an image or PDF of a template that must be completed. Covers
  rendering and extracting embedded images from PDFs (PyMuPDF), reading them at full
  resolution, transcribing the template structure and fine print exactly, then rebuilding
  it (TikZ / Markdown / table) with the user's content. Hands the filled structure to a
  domain skill (e.g. idea-validation) for the actual content.
---

# Framework-Extraction Skill

## Purpose

Get an accurate, machine-usable copy of a visual template out of a photo or PDF so it can
be reproduced and filled in. Two failure modes to avoid: (1) misreading the fine print, and
(2) reproducing a vague approximation instead of the real template. This skill is about
*faithfulness* — capture the exact wording, structure, and formula before filling anything.

## When to use

- A framework / template / canvas / form / diagram is locked inside an image or PDF.
- The user pastes a screenshot of slides and says "do this for my project".
- You need the *exact* template text (questions, labels, formula) before applying a domain
  skill such as `idea-validation`.

## Workflow

### 1. Inventory the source
- For a PDF, open it and list pages and embedded images. Saved-webpage and Gmail-draft PDFs
  often bury the real slides among hundreds of tiny UI sprites — sort by pixel area and look
  at the large ones.

### 2. Extract embedded images at native resolution (PyMuPDF)
```python
import fitz, os
doc = fitz.open("source.pdf")
out = "_extracted"; os.makedirs(out, exist_ok=True)
for pno in range(doc.page_count):
    for i, im in enumerate(doc[pno].get_images(full=True)):
        xref = im[0]
        pix = fitz.Pixmap(doc, xref)
        if pix.n - pix.alpha >= 4:            # CMYK / odd colourspaces → RGB
            pix = fitz.Pixmap(fitz.csRGB, pix)
        pix.save(f"{out}/p{pno}_img{i}_{pix.width}x{pix.height}.png")
```
- The framework slides are the **large, content-rich** PNGs (hundreds of px on a side, not
  the 1×1 / 30×30 sprites). Read those.
- If extraction yields only blanks (full-window captures), instead **render the page** at
  high DPI and crop the regions: `page.get_pixmap(dpi=300)`.
- Install with `python -m pip install pymupdf --quiet` if `import fitz` fails. Pillow helps
  for cropping/upscaling.

### 3. Transcribe the template exactly
- Capture every label, question, the **exact fill-in formula**, and any source/attribution
  line (e.g. "Source: …" or a copyright credit) — it tells you which framework it is.
- Note the visual structure: circles + overlaps, boxes + connectors, columns, color coding.
- Zoom (upscale a crop) if the fine print is unreadable at native size.

### 4. Reproduce it
- Rebuild the structure in editable form: **TikZ** for Venn diagrams / box-and-connector
  templates, **tables** for canvases, **Markdown** for question lists.
- Preserve the original palette and layout so the result reads as a completed version of
  the same template.

### 5. Hand off for content
- Pass the faithful structure to the relevant domain skill to fill it (idea-validation for
  DVF / empathy / problem / impact; others as needed). Keep extraction and content separate.

### 6. Clean up
- Remove the scratch `_extracted/` folder when done unless the user wants the crops.

## Quality checklist

- [ ] Identified the framework from its labels / source line, not a guess.
- [ ] Transcribed the exact formula and every question/label.
- [ ] Reproduction matches the original structure and color coding.
- [ ] Scratch files removed.

## Invariants

- Faithfulness first: never paraphrase a template's wording when the exact text is readable.
- Separate *extraction* (this skill) from *filling* (domain skill).
- Don't delete or overwrite the user's source file; write reproductions as new files.
