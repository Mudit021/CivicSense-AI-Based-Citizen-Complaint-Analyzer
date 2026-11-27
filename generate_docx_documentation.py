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

def add_bullet_list(doc, items, after=Pt(3)):
    for item in items:
        p = doc.add_paragraph(style="List Bullet")
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = after
        p.paragraph_format.line_spacing = 1.15
        p.paragraph_format.left_indent = Inches(0.5)
        r = p.add_run(item)
        r.font.name = "Arial"
        r.font.size = Pt(10)
        r.font.color.rgb = RGBColor(30, 41, 59)

def add_table_with_header(doc, headers, rows, header_bg="1A2B4C", header_fnt_color="FFFFFF",
                          row_alt_bg="F8FAFC", row_even_bg="FFFFFF", col_widths=None,
                          font_size=9):
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    if col_widths:
        for i, w in enumerate(col_widths):
            table.columns[i].width = Inches(w)
    for col_idx, h_text in enumerate(headers):
        cell = table.cell(0, col_idx)
        set_cell_background(cell, header_bg)
        p = cell.paragraphs[0]
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)
        r = p.add_run(h_text)
        r.font.name = "Arial"
        r.font.size = Pt(font_size)
        r.font.bold = True
        r.font.color.rgb = RGBColor(255, 255, 255)
    for row_idx, row_data in enumerate(rows, start=1):
        for col_idx, text in enumerate(row_data):
            cell = table.cell(row_idx, col_idx)
            if row_idx % 2 == 0:
                bg = row_even_bg
            else:
                bg = row_alt_bg
            set_cell_background(cell, bg)
            set_cell_margins(cell, 50, 50, 70, 70)
            p = cell.paragraphs[0]
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(0)
            r = p.add_run(text)
            r.font.name = "Arial"
            r.font.size = Pt(font_size)
            r.font.color.rgb = RGBColor(30, 41, 59)
    return table

def add_simple_table(doc, headers, rows, col_widths=None):
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    if col_widths:
        for i, w in enumerate(col_widths):
            table.columns[i].width = Inches(w)
    for col_idx, h_text in enumerate(headers):
        cell = table.cell(0, col_idx)
        p = cell.paragraphs[0]
        r = p.add_run(h_text)
        r.font.name = "Arial"
        r.font.size = Pt(9)
        r.font.bold = True
    for row_idx, row_data in enumerate(rows, start=1):
        for col_idx, text in enumerate(row_data):
            cell = table.cell(row_idx, col_idx)
            p = cell.paragraphs[0]
            r = p.add_run(text)
            r.font.name = "Arial"
            r.font.size = Pt(8.5)
    return table

def save_document(doc, path):
    doc.save(str(path))
    resolved = Path(path).resolve()
    print(f"Successfully generated Word Document at: {resolved}")
    return len(doc.paragraphs)

def add_heading_with_level(doc, text, level, color=None):
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

def add_body_text(doc, text, bold_prefix=None, space_after=Pt(5)):
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

def add_callout_box(doc, text, title="KEY ARCHITECTURAL HIGHLIGHT:"):
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
def add_heading_with_level(doc, text, level, color=None):
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

def add_body_text(doc, text, bold_prefix=None, space_after=Pt(5)):
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

def add_callout_box(doc, text, title="KEY ARCHITECTURAL HIGHLIGHT:"):
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = tbl.cell(0, 0)
    cell.width = Inches(6.5)
    set_cell_background(cell, "F8FAFC")
    set_cell_margins(cell, 80, 80, 120, 120)
    tcPr = cell._tc.get_or_add_tcPr()
    borders = parse_xml(f"<w:tcBorders {nsdecls("w")}"><w:left w:val="single" w:sz="24" w:space="0" w:color="3B5BDB"/><w:top w:val="none"/><w:right w:val="none"/><w:bottom w:val="none"/></w:tcBorders>")
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
