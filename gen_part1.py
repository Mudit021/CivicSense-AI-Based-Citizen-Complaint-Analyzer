#!/usr/bin/env python3
"""Generator for CIVICSENSE_COMPREHENSIVE_PROJECT_DOCUMENTATION.docx"""

import os
from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls

def set_cell_background(cell, fill_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(f'<w:tcMar {nsdecls("w")}><w:top w:w="{top}" w:type="dxa"/><w:bottom w:w="{bottom}" w:type="dxa"/><w:left w:w="{left}" w:type="dxa"/><w:right w:w="{right}" w:type="dxa"/></w:tcMar>')
    tcPr.append(tcMar)

def add_heading_with_run(doc, text, level, color=None):
    if color is None:
        color = RGBColor(26, 43, 76)
    h = doc.add_paragraph()
    h.paragraph_format.space_before = Pt(14 if level == 1 else 10)
    h.paragraph_format.space_after = Pt(6)
    h.paragraph_format.line_spacing = 1.15
    r = h.add_run(text)
    r.font.name = "Arial"
    r.font.size = Pt(14 if level == 1 else 11.5 if level == 2 else 10.5 if level == 3 else 10)
    r.font.bold = True if level <= 2 else False
    r.font.color.rgb = color
    return h

def add_body(doc, text, bold_prefix=None, space_after=Pt(5)):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = space_after
    p.paragraph_format.line_spacing = 1.15
    if bold_prefix:
        rb = p.add_run(bold_prefix)
        rb.font.name = "Arial"
        rb.font.size = Pt(10)
        rb.font.bold = True
        rb.font.color.rgb = RGBColor(30, 41, 59)
    r = p.add_run(text)
    r.font.name = "Arial"
    r.font.size = Pt(10)
    r.font.color.rgb = RGBColor(30, 41, 59)
    return p

def add_callout(doc, text, title="KEY ARCHITECTURAL HIGHLIGHT:"):
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = tbl.cell(0, 0)
    cell.width = Inches(6.5)
    set_cell_background(cell, "F8FAFC")
    set_cell_margins(cell, 80, 80, 120, 120)
    tcPr = cell._tc.get_or_add_tcPr()
    borders = parse_xml(f'<w:tcBorders {nsdecls("w")}><w:left w:val="single" w:sz="24" w:space="0" w:color="3B5BDB"/><w:top w:val="none"/><w:right w:val="none"/><w:bottom w:val="none"/></w:tcBorders>')
    tcPr.append(borders)
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(0)
    rt = p.add_run(title)
    rt.font.name = "Arial"
    rt.font.size = Pt(9.5)
    rt.font.bold = True
    rt.font.color.rgb = RGBColor(59, 91, 219)
    r = p.add_run(text)
    r.font.name = "Arial"
    r.font.size = Pt(9.5)
    r.font.color.rgb = RGBColor(30, 41, 59)

def save_document(doc, path):
    """Save the document and print confirmation."""
    doc.save(str(path))
    resolved = Path(path).resolve()
    print(f"Successfully generated Word Document at: {resolved}")
    return len(doc.paragraphs)

def create_document():
    doc = Document()

    # Page Margins: Standard 1 inch
    for section in doc.sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)

    # Color Palette
    COLOR_PRIMARY = RGBColor(26, 43, 76)      # Navy #1A2B4C
    COLOR_SECONDARY = RGBColor(59, 91, 219)   # Accent Blue #3B5BDB
    COLOR_DARK = RGBColor(30, 41, 59)         # Ink #1E293B
    COLOR_MUTED = RGBColor(100, 116, 139)     # Slate #64748B
    COLOR_EMERALD = RGBColor(43, 138, 62)     # Success Green #2B8A3E
    COLOR_WARNING = RGBColor(217, 83, 79)     # Danger Red #D9534F
    COLOR_SKY = RGBColor(100, 149, 237)       # Sky Blue #6495ED
