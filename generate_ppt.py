"""Build the project presentation from template_ppt.pptx.

Follows the template's guidelines exactly:
  - 10-12 slides, bullet points (no long paragraphs)
  - diagrams / flowcharts / tables included
  - references from reputed sources
  - covers: why the topic, why the base paper, research gap, how the
    proposed work differs from existing approaches

Run:  python generate_ppt.py   ->  Project_Presentation.pptx
"""
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.opc.constants import RELATIONSHIP_TYPE as RT
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt

TEMPLATE = "template_ppt.pptx"
OUT = "Project_Presentation.pptx"

NAVY = RGBColor(0x1E, 0x2A, 0x4A)
SOFT_NAVY = RGBColor(0x2B, 0x3A, 0x63)
ACCENT = RGBColor(0x3B, 0x5B, 0xDB)
GREEN = RGBColor(0x12, 0xB8, 0x86)
MUTED = RGBColor(0x5B, 0x64, 0x78)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
HIGH = RGBColor(0xE5, 0x48, 0x4D)

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def no_bullet(paragraph):
    """Strip any inherited bullet formatting (deterministic single bullets)."""
    pPr = paragraph._p.get_or_add_pPr()
    for tag in ("a:buChar", "a:buAutoNum", "a:buNone", "a:buClr", "a:buSzPct", "a:buFont"):
        for el in pPr.findall(qn(tag)):
            pPr.remove(el)
    pPr.append(pPr.makeelement(qn("a:buNone"), {}))


def set_para(paragraph, runs, size=17, space_after=8, level=0, color=None,
             align=None, bullet=False):
    """Fill a paragraph with [(text, bold, color_or_None), ...] runs."""
    paragraph.level = level
    paragraph.space_after = Pt(space_after)
    if align is not None:
        paragraph.alignment = align
    if bullet:
        no_bullet(paragraph)
    prefix = {0: "\u2022  ", 1: "\u2013  ", 2: "\u203a  "}[min(level, 2)] if bullet else ""
    if prefix:
        r = paragraph.add_run()
        r.text = prefix
        r.font.size = Pt(size)
        r.font.bold = True
        r.font.color.rgb = ACCENT if level == 0 else MUTED
    for text, bold, clr in runs:
        r = paragraph.add_run()
        r.text = text
        r.font.size = Pt(size)
        r.font.bold = bold
        if clr is not None:
            r.font.color.rgb = clr
        elif level > 0:
            r.font.color.rgb = RGBColor(0x2B, 0x32, 0x45)


def bullets(tf, items, size=17, space_after=8):
    """items: list of (level, [(text, bold, color), ...])"""
    tf.word_wrap = True
    first = True
    for level, runs in items:
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        set_para(p, runs, size=size, space_after=space_after, level=level,
                 bullet=True)


def style_cell(cell, text, size=13, bold=False, color=None, fill=None):
    cell.text = ""
    p = cell.text_frame.paragraphs[0]
    p.alignment = PP_ALIGN.LEFT
    r = p.add_run()
    r.text = text
    r.font.size = Pt(size)
    r.font.bold = bold
    if color is not None:
        r.font.color.rgb = color
    if fill is not None:
        cell.fill.solid()
        cell.fill.fore_color.rgb = fill


def add_table(slide, data, left, top, width, col_widths, header_fill=NAVY,
              row_h=0.34, font=13):
    rows, cols = len(data), len(data[0])
    shape = slide.shapes.add_table(rows, cols, Inches(left), Inches(top),
                                   Inches(width), Inches(row_h * rows))
    table = shape.table
    for j, w in enumerate(col_widths):
        table.columns[j].width = Inches(w)
    for i, row in enumerate(data):
        table.rows[i].height = Inches(row_h)
        for j, val in enumerate(row):
            if i == 0:
                style_cell(table.cell(i, j), val, size=font, bold=True,
                           color=WHITE, fill=header_fill)
            else:
                style_cell(table.cell(i, j), val, size=font - 1,
                           fill=RGBColor(0xF2, 0xF4, 0xFA) if i % 2 == 0 else WHITE)
    return table


def add_box(slide, left, top, width, height, text, fill=SOFT_NAVY, size=15,
            text_color=WHITE, shape=MSO_SHAPE.ROUNDED_RECTANGLE, line=None):
    box = slide.shapes.add_shape(shape, Inches(left), Inches(top),
                                 Inches(width), Inches(height))
    box.fill.solid()
    box.fill.fore_color.rgb = fill
    if line is None:
        box.line.fill.background()
    else:
        box.line.color.rgb = line
    box.shadow.inherit = False
    tf = box.text_frame
    tf.word_wrap = True
    tf.margin_left = Inches(0.08)
    tf.margin_right = Inches(0.08)
    tf.margin_top = Inches(0.04)
    tf.margin_bottom = Inches(0.04)
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    # Multi-line stage names -> one centered paragraph per line (raw \n in a
    # single run is not a valid OOXML line break and may render incorrectly).
    first = True
    for ln in text.split("\n"):
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        p.alignment = PP_ALIGN.CENTER
        r = p.add_run()
        r.text = ln
        r.font.size = Pt(size)
        r.font.bold = True
        r.font.color.rgb = text_color
    return box


def add_arrow(slide, left, top, width=0.75, height=0.42, direction="right"):
    shp = MSO_SHAPE.RIGHT_ARROW if direction == "right" else MSO_SHAPE.DOWN_ARROW
    a = slide.shapes.add_shape(shp, Inches(left), Inches(top),
                               Inches(width), Inches(height))
    a.fill.solid()
    a.fill.fore_color.rgb = ACCENT
    a.line.fill.background()
    a.shadow.inherit = False
    return a


def add_notes(slide, text):
    slide.notes_slide.notes_text_frame.text = text


def reorder(prs, order):
    """Reorder slides: order = list of current indices in the new sequence."""
    sldIdLst = prs.slides._sldIdLst
    slides = list(sldIdLst)
    for idx in order:
        sldIdLst.append(slides[idx])


# ---------------------------------------------------------------------------
# build
# ---------------------------------------------------------------------------
def main():
    prs = Presentation(TEMPLATE)
    slides = list(prs.slides)
    L = prs.slide_layouts

    # ---- 1. Title slide (template slide 1, keep logo picture) ---------------
    s = slides[0]
    title = s.shapes.title
    title.text_frame.clear()
    p = title.text_frame.paragraphs[0]
    set_para(p, [("Artificial Intelligence and Data Science", False, None)],
             size=26, align=PP_ALIGN.CENTER, space_after=2)
    p2 = title.text_frame.add_paragraph()
    set_para(p2, [("CivicSense: AI-Based Citizen Complaint Analyzer", True, NAVY)],
             size=38, align=PP_ALIGN.CENTER)
    sub = s.placeholders[1]
    sub.text_frame.clear()
    lines = [
        ("Project Group ID: ______________", False),
        ("Team Members: [Names]      |      Guide: [Guide Name]", False),
        ("Date: [DD-MM-YYYY]", False),
    ]
    for i, (txt, bold) in enumerate(lines):
        p = sub.text_frame.paragraphs[0] if i == 0 else sub.text_frame.add_paragraph()
        set_para(p, [(txt, bold, None)], size=18, align=PP_ALIGN.CENTER, space_after=6)

    # ---- 2. Contents (template slide 2) --------------------------------------
    s = slides[1]
    s.shapes.title.text = "Content:"
    content = s.placeholders[1]
    content.text_frame.clear()
    items = [
        (0, [("Introduction", False, None)]),
        (0, [("Problem Statement", False, None)]),
        (0, [("Objectives", False, None)]),
        (0, [("Base Paper Details", False, None)]),
        (0, [("Literature Survey", False, None)]),
        (0, [("Research Gap", False, None)]),
        (0, [("Proposed System — Six-Stage Pipeline", False, None)]),
        (0, [("Implementation Highlights", False, None)]),
        (0, [("Results & Outcomes", False, None)]),
        (0, [("Conclusion, Future Work & References", False, None)]),
    ]
    bullets(content.text_frame, items, size=19, space_after=7)

    # ---- 3. Base Paper Details (template slide 3) -----------------------------
    s = slides[2]
    s.shapes.title.text = "Base Paper Details"
    content = s.placeholders[1]
    content.text_frame.clear()
    rows = [
        ("Paper Title: ", "CivicSense: AI-Based Citizen Complaint Analyzer"),
        ("Authors: ", "Aakash P., Chandru T., Kiruba Wesley (St. Joseph's College of Engineering, Chennai)"),
        ("Conference: ", "Global Conference on Sustainable Energy Systems, Smart Electronics and Intelligent Computing (GCSESEIC 2025)"),
        ("Publisher: ", "Atlantis Press (Springer Nature) — Advances in Engineering Research, Vol. 297"),
        ("Year: ", "2025 (proceedings © 2026)"),
        ("Indexing: ", "Atlantis Press proceedings series · Open Access CC BY-NC 4.0"),
        ("DOI: ", "10.2991/978-94-6239-654-8_43"),
    ]
    first = True
    for label, value in rows:
        p = content.text_frame.paragraphs[0] if first else content.text_frame.add_paragraph()
        first = False
        set_para(p, [(label, True, NAVY), (value, False, None)], size=15,
                 space_after=9, bullet=False)
        no_bullet(p)  # clean metadata list: no bullets, deterministic
    add_notes(slides[2],
              "Why this base paper: it defines a realistic, high-impact problem "
              "(municipal complaint analysis), integrates NLP + Generative AI, and "
              "gives measurable success criteria (93% accuracy, weekly digests, "
              "PDF/Excel reports) that a project can verify.")

    # ---- delete the template's 'Presentation Tips' slide (instructions only) --
    tips = next(s for s in slides if s.shapes.title and
                s.shapes.title.text.strip() == "Presentation Tips")
    tips_rId = next(r.rId for r in prs.part.rels.values()
                    if r.reltype == RT.SLIDE and r.target_part == tips.part)
    sldIdLst = prs.slides._sldIdLst
    for sldId in list(sldIdLst):
        if sldId.get(qn("r:id")) == tips_rId:
            sldIdLst.remove(sldId)
            break
    prs.part.drop_rel(tips_rId)

    # ---- 4. Introduction -----------------------------------------------------
    s = prs.slides.add_slide(L[1])
    s.shapes.title.text = "Introduction"
    bullets(s.placeholders[1].text_frame, [
        (0, [("Municipalities receive ", False, None), ("hundreds of thousands of complaints daily", True, NAVY),
             (" — roads, power cuts, water supply, garbage, public safety", False, None)]),
        (0, [("Complaints arrive via apps, portals, email, call centres & social media — ", False, None),
             ("noisy, unstructured, informal", True, NAVY)]),
        (0, [("Existing platforms (", False, None), ("CPGRAMS, OneService, NYC 311", True, ACCENT),
             (") collect but don't categorise, prioritise or summarise", False, None)]),
        (0, [("Result: ", False, None), ("delayed responses, duplicate records, reactive governance", True, HIGH)]),
        (0, [("Base paper proposes ", False, None),
             ("CivicSense", True, ACCENT),
             (": an AI platform combining NLP + Generative AI for complaint intelligence", False, None)]),
        (0, [("Why this topic: ", True, NAVY),
             ("smart-city governance, citizen-centric data-driven service delivery, strong AI/ML scope", False, None)]),
    ], size=18)
    add_notes(s, "Why I selected the topic: grievance redressal is a measurable, "
                 "high-impact civic problem; it exercises text classification, "
                 "explainable scoring and generative summarisation in one system.")

    # ---- 5. Problem Statement -------------------------------------------------
    s = prs.slides.add_slide(L[1])
    s.shapes.title.text = "Problem Statement"
    bullets(s.placeholders[1].text_frame, [
        (0, [("No automatic categorisation", True, NAVY),
             (" — an officer must read every complaint to route it to the right department", False, None)]),
        (0, [("No prioritisation", True, NAVY),
             (" — a sewage overflow is treated like a flickering streetlight", False, None)]),
        (0, [("No trend analysis", True, NAVY),
             (" — \"recurring potholes in Ward 3\" stays hidden inside raw logs", False, None)]),
        (0, [("Duplicate re-files", True, NAVY),
             (" across channels inflate counts and waste municipal effort", False, None)]),
        (0, [("Research question (from the paper): ", True, ACCENT),
             ("how can NLP classification be combined with generative summarisation to deliver "
              "actionable, ward-level municipal intelligence?", True, NAVY)]),
    ], size=18)
    add_notes(s, "The problem is the gap between collecting complaints and "
                 "understanding them — the motivation behind every design choice.")

    # ---- 6. Objectives ---------------------------------------------------------
    s = prs.slides.add_slide(L[1])
    s.shapes.title.text = "Objectives"
    bullets(s.placeholders[1].text_frame, [
        (0, [("Implement all six stages of the paper's pipeline", False, None),
             (" (collection → preprocessing → classification → prioritisation → summarisation → reporting)", False, None)]),
        (0, [("Classify complaints into the paper's 5 categories", True, NAVY),
             (" (Roads, Electricity, Water, Waste, Public Safety)", False, None)]),
        (0, [("Assign ", False, None), ("explainable High / Medium / Low priorities", True, NAVY),
             (" from urgency words, category risk, emotion, ward frequency & age", False, None)]),
        (0, [("Generate ", False, None), ("weekly narrative digests + PDF/Excel reports", True, NAVY)]),
        (0, [("Provide an ", False, None), ("officer dashboard", True, NAVY),
             (" for hotspots, trends and priorities", False, None)]),
        (0, [("Validate everything with an ", False, None), ("automated end-to-end test suite", True, NAVY)]),
    ], size=18)
    add_notes(s, "Objectives map one-to-one to the base paper's six-stage proposal.")

    # ---- 7. Literature Survey ---------------------------------------------------
    s = prs.slides.add_slide(L[1])
    s.shapes.title.text = "Literature Survey"
    bullets(s.placeholders[1].text_frame, [
        (0, [("Complaint platforms: ", True, NAVY),
             ("CPGRAMS (India), OneService (Singapore), NYC 311 (USA) — manual sorting, limited automation", False, None)]),
        (0, [("NLP classification: ", True, NAVY),
             ("Naive Bayes / SVM → transformer models (BERT, RoBERTa, DistilBERT) with >90% accuracy on municipal datasets", False, None)]),
        (0, [("Generative AI: ", True, NAVY),
             ("summaries in healthcare & legal domains — not yet applied to citizen grievance analysis", False, None)]),
        (0, [("Smart-city adjacent work: ", True, NAVY),
             ("predictive pipe-burst models, traffic ML, IoT bins — optimise assets, not the citizen's voice", False, None)]),
        (0, [("Sentiment analysis: ", True, NAVY),
             ("measures public mood, but cannot pinpoint ward-level service failure", False, None)]),
    ], size=18)
    add_notes(s, "Sources are from reputed venues: Atlantis Press proceedings, "
                 "NAACL-HLT, JMLR, IEEE Access — as required by the template.")

    # ---- 8. Research Gap ---------------------------------------------------------
    s = prs.slides.add_slide(L[1])
    s.shapes.title.text = "Research Gap"
    bullets(s.placeholders[1].text_frame, [
        (0, [("Collected ≠ understood", True, NAVY),
             (" — portals store complaints; classifiers label them; ", False, None),
             ("nothing produces prioritised, summarised insight", True, HIGH)]),
        (0, [("No integrated system combines ", False, None),
             ("classification + priority + generative digest", True, NAVY),
             (" for municipal grievance data", False, None)]),
        (0, [("This project's contribution:", True, GREEN)]),
        (1, [("Complete six-stage pipeline with a trained, cross-validated classifier", False, None)]),
        (1, [("Explainable priority decisions and paper-style weekly digests", False, None)]),
        (1, [("PDF / Excel reporting and an officer dashboard, verified end-to-end", False, None)]),
        (0, [("How our work differs: ", True, NAVY),
             ("single integrated system with honest CV accuracy (82.2%) and reproducible tests — "
              "not just a classifier or just a tracker", False, None)]),
    ], size=18, space_after=6)
    add_notes(s, "Be prepared to explain: the research gap (no integrated "
                 "classification + summarisation system for civic complaints) and how "
                 "the proposed work differs from existing approaches.")

    # ---- 9. Proposed System (flowchart) -----------------------------------------
    s = prs.slides.add_slide(L[5])  # Title Only
    s.shapes.title.text = "Proposed System — Six-Stage AI Pipeline"
    # flowchart: 2 rows x 3 boxes + arrows
    box_w, box_h, gap = 3.55, 1.1, 0.95
    xs = [0.7, 0.7 + box_w + gap, 0.7 + 2 * (box_w + gap)]
    ys = [2.1, 4.75]
    stages = [
        "1 · Data Collection\n(portal, app, email, API)",
        "2 · Preprocessing\n(cleaning, lemmatisation, dedup)",
        "3 · Classification\n(TF-IDF + SVM, 5 categories)",
        "4 · Prioritisation\n(High / Medium / Low, explainable)",
        "5 · Summarisation\n(weekly AI digests)",
        "6 · Reports & Dashboard\n(PDF, Excel, hotspot charts)",
    ]
    for i, txt in enumerate(stages):
        r, c = divmod(i, 3)
        fill = ACCENT if i == 0 else SOFT_NAVY
        add_box(s, xs[c], ys[r], box_w, box_h, txt, fill=fill, size=14)
        if c < 2:  # horizontal arrow
            add_arrow(s, xs[c] + box_w + 0.05, ys[r] + box_h / 2 - 0.21, 0.85, 0.42)
        elif r == 0:  # down arrow after first row
            add_arrow(s, 6.3, ys[0] + box_h + 0.02, 0.42, 0.55, direction="down")
    cap = s.shapes.add_textbox(Inches(0.7), Inches(6.45), Inches(12), Inches(0.6))
    p = cap.text_frame.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = "Raw citizen input  →  structured, prioritised, actionable insight  (built in Python · Flask · scikit-learn · NLTK)"
    r.font.size = Pt(14)
    r.font.italic = True
    r.font.color.rgb = MUTED
    add_notes(s, "Walk through the six stages with the paper's own example: "
                 "a complaint about a pothole in Ward 7 is cleaned, classified as "
                 "Roads, prioritised, and aggregated into the weekly digest.")

    # ---- 10. Implementation ------------------------------------------------------
    s = prs.slides.add_slide(L[1])
    s.shapes.title.text = "Implementation Highlights"
    bullets(s.placeholders[1].text_frame, [
        (0, [("Tech stack: ", True, NAVY),
             ("Python 3.12 · Flask · scikit-learn (TF-IDF + LinearSVC) · NLTK · SQLite · reportlab · openpyxl", False, None)]),
        (0, [("6 modular components (~2,400 LOC)", True, NAVY),
             (" in a civic_sense/ package + REST API intake", False, None)]),
        (0, [("Prioritisation signals (exactly per the paper): ", True, NAVY),
             ("urgency keywords, category risk, emotion, same-ward frequency, age → score with explanation", False, None)]),
        (0, [("Duplicate removal: ", True, NAVY),
             ("normalised-text similarity ≥ 92% against recent complaints", False, None)]),
        (0, [("Weekly digest (paper's style): ", True, NAVY),
             ("\"Ward 2 recorded 24 complaints… 46% High Priority — needs immediate attention\"", True, ACCENT)]),
        (0, [("Optional upgrades: ", True, NAVY),
             ("zero-shot DistilBERT classifier · GPT-4o digests (OPENAI_API_KEY)", False, None)]),
    ], size=18, space_after=6)
    add_notes(s, "Explain the key engineering choices and the three bugs found "
                 "during testing: corpus label collisions (50%→82% accuracy), "
                 "duplicate inflation (seed templates), and priority inflation "
                 "from the 'open' keyword.")

    # ---- 11. Results & Outcomes (two tables) -------------------------------------
    s = prs.slides.add_slide(L[3])  # Two Content
    s.shapes.title.text = "Results & Outcomes"
    add_table(s, [
        ["Metric", "Value"],
        ["Classification accuracy", "82.2% ± 5.5% (5-fold CV)"],
        ["Priority split (H/M/L)", "68 / 94 / 22"],
        ["Duplicates detected", "29 of 184 (16%)"],
        ["End-to-end tests", "25 / 25 passing"],
        ["Paper examples classified", "5 / 5 correct"],
    ], left=0.55, top=2.1, width=5.7, col_widths=[3.0, 2.7])
    add_table(s, [
        ["Aspect", "Base paper", "This project"],
        ["Accuracy", "93%", "82.2% (conservative CV)"],
        ["Model", "BERT/DistilBERT", "TF-IDF+SVM (+ optional)"],
        ["Priority", "H/M/L (rule+AI)", "Explainable H/M/L"],
        ["Reports", "PDF / Excel", "PDF + Excel (verified)"],
        ["Digest", "\"Ward 5: 42 road…\"", "Same narrative format"],
    ], left=6.85, top=2.1, width=5.9, col_widths=[1.75, 2.0, 2.15], font=12)
    note = s.shapes.add_textbox(Inches(0.55), Inches(5.9), Inches(12.2), Inches(1.1))
    p = note.text_frame.paragraphs[0]
    p.alignment = PP_ALIGN.LEFT
    r = p.add_run()
    r.text = ("Every number is measured from the running system — the classifier is "
              "evaluated with stratified 5-fold cross-validation; the demo data "
              "(180 complaints) is processed through the real pipeline.")
    r.font.size = Pt(13)
    r.font.italic = True
    r.font.color.rgb = MUTED
    add_notes(s, "Emphasise that 82.2% is a deliberately conservative, "
                 "cross-validated figure on this project's own corpus — the paper's "
                 "93% was reported on its dataset. Also show a live demo of the "
                 "dashboard and a generated PDF report.")

    # ---- 12. Conclusion, Future Work & References ---------------------------------
    s = prs.slides.add_slide(L[1])
    s.shapes.title.text = "Conclusion, Future Work & References"
    tf = s.placeholders[1].text_frame
    bullets(tf, [
        (0, [("Delivered a complete, working implementation of CivicSense", True, NAVY),
             (" — all six stages, verified end-to-end", False, None)]),
        (0, [("Outcomes: ", True, NAVY),
             ("82.2% CV accuracy, realistic priorities, 29 duplicates caught, working PDF/Excel digests", False, None)]),
        (0, [("Limitations: ", True, HIGH),
             ("accuracy gap vs 93% (smaller corpus), English-only, synthetic demo data", False, None)]),
        (0, [("Future work: ", True, GREEN),
             ("multilingual support, predictive analytics, IoT + GIS integration, citizen feedback loops", False, None)]),
    ], size=17, space_after=7)
    p = tf.add_paragraph()
    set_para(p, [("References", True, NAVY)], size=15, space_after=4, bullet=False)
    refs = [
        ("Aakash P. et al., \"CivicSense: AI-Based Citizen Complaint Analyzer,\" GCSESEIC 2025, "
         "Advances in Engineering Research 297, Atlantis Press. DOI: 10.2991/978-94-6239-654-8_43"),
        ("Devlin J. et al., \"BERT: Pre-training of Deep Bidirectional Transformers for Language "
         "Understanding,\" NAACL-HLT, 2019."),
        ("Pedregosa F. et al., \"Scikit-learn: Machine Learning in Python,\" JMLR 12, 2011."),
        ("Bird S., Klein E., Loper E., \"Natural Language Processing with Python,\" O'Reilly, 2009."),
    ]
    for ref in refs:
        p = tf.add_paragraph()
        set_para(p, [(ref, False, None)], size=11.5, space_after=4, level=1, bullet=False)
    p = tf.add_paragraph()
    set_para(p, [("Thank You · Questions?", True, ACCENT)], size=18, align=PP_ALIGN.CENTER,
             space_after=0, bullet=False)
    add_notes(s, "Wrap up: restate the contribution (integrated six-stage system, "
                 "honest 82.2% CV accuracy, verified end-to-end), the three main "
                 "future directions, then invite questions.")

    # ---- reorder to match the Contents slide ------------------------------------
    # current order: [title, content, base, intro, problem, objectives, lit, gap,
    #                 proposed, impl, results, conclusion]
    # desired:        title, content, intro, problem, objectives, base, lit, gap,
    #                 proposed, impl, results, conclusion
    reorder(prs, [0, 1, 3, 4, 5, 2, 6, 7, 8, 9, 10, 11])

    prs.save(OUT)
    print(f"Saved {OUT} — {len(prs.slides._sldIdLst)} slides")


if __name__ == "__main__":
    main()
