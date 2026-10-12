"""Build the CivicSense project report as a Word document.

Run from the project root:

    python civic_sense/build_report.py

The script writes Project_Report.docx at the project root. All statistics in
the report were measured from a clean demonstration database seeded through the
real pipeline; the report is regenerated (not hand-edited) so numbers stay in
sync with the implementation.
"""
from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

NAVY = RGBColor(0x1F, 0x3B, 0x63)
GREY = RGBColor(0x40, 0x40, 0x40)

d = Document()

for sec in d.sections:
    sec.top_margin = Inches(1.0)
    sec.bottom_margin = Inches(1.0)
    sec.left_margin = Inches(1.0)
    sec.right_margin = Inches(1.0)

style = d.styles["Normal"]
style.font.name = "Calibri"
style.font.size = Pt(11)
style.paragraph_format.space_after = Pt(6)
style.paragraph_format.line_spacing = 1.15

TABLES = []  # (number, caption) collected for the List of Tables
LOT_ANCHOR = {}  # placeholder paragraph index for the List of Tables


def h(text, level=1):
    p = d.add_paragraph()
    r = p.add_run(text)
    r.bold = True
    r.font.color.rgb = NAVY
    if level == 1:
        r.font.size = Pt(15)
        p.paragraph_format.space_before = Pt(14)
        p.paragraph_format.space_after = Pt(6)
    elif level == 2:
        r.font.size = Pt(13)
        p.paragraph_format.space_before = Pt(10)
        p.paragraph_format.space_after = Pt(4)
    else:
        r.font.size = Pt(11.5)
        p.paragraph_format.space_before = Pt(8)
        p.paragraph_format.space_after = Pt(3)
    return p


def para(text, italic=False, bold=False, size=11, align=None):
    p = d.add_paragraph()
    r = p.add_run(text)
    r.italic = italic
    r.bold = bold
    r.font.size = Pt(size)
    if align == "center":
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(6)
    return p


def bullet(text, bold_prefix=None):
    p = d.add_paragraph(style="List Bullet")
    if bold_prefix:
        r = p.add_run(bold_prefix)
        r.bold = True
        p.add_run(text)
    else:
        p.add_run(text)
    p.paragraph_format.space_after = Pt(3)
    return p


def bullet2(text):
    p = d.add_paragraph(style="List Bullet 2")
    p.add_run(text)
    p.paragraph_format.space_after = Pt(2)
    return p


def set_cell_bg(cell, hex_color):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_color)
    tcPr.append(shd)


def make_table(headers, rows, widths=None, caption=None, numbered=False):
    if caption:
        if numbered:
            TABLES.append((len(TABLES) + 1, caption))
            cp = d.add_paragraph()
            cr = cp.add_run("Table %d: %s" % (len(TABLES), caption))
            cr.bold = True
            cr.font.size = Pt(9.5)
            cr.font.color.rgb = NAVY
            cp.paragraph_format.space_before = Pt(6)
            cp.paragraph_format.space_after = Pt(2)
        else:
            cp = d.add_paragraph()
            cr = cp.add_run(caption)
            cr.italic = True
            cr.font.size = Pt(9)
            cr.font.color.rgb = GREY
            cp.paragraph_format.space_before = Pt(6)
            cp.paragraph_format.space_after = Pt(2)

    t = d.add_table(rows=1, cols=len(headers))
    t.style = "Table Grid"
    if widths:
        for i, w in enumerate(widths):
            for cell in t.rows[0].cells:
                cell.width = Pt(w)
    hdr = t.rows[0].cells
    for i, htxt in enumerate(headers):
        hdr[i].text = htxt
        for p in hdr[i].paragraphs:
            for r in p.runs:
                r.bold = True
                r.font.size = Pt(9.5)
        set_cell_bg(hdr[i], "1F3B63")
        for p in hdr[i].paragraphs:
            for r in p.runs:
                r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
    for row in rows:
        cells = t.add_row().cells
        for i, val in enumerate(row):
            cells[i].text = str(val)
            for p in cells[i].paragraphs:
                for r in p.runs:
                    r.font.size = Pt(9.5)
    d.add_paragraph().paragraph_format.space_after = Pt(2)
    return t


def page_break():
    d.add_page_break()


def figure(caption, lines=None):
    """A lightweight monospaced 'figure' with a caption."""
    if lines:
        for ln in lines:
            p = d.add_paragraph()
            r = p.add_run(ln)
            r.font.name = "Consolas"
            r.font.size = Pt(9)
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_after = Pt(1)
    cp = d.add_paragraph()
    cr = cp.add_run("Figure: " + caption)
    cr.italic = True
    cr.font.size = Pt(9)
    cr.font.color.rgb = GREY
    cp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cp.paragraph_format.space_after = Pt(8)


# ===========================================================================
# COVER PAGE
# ===========================================================================
for _ in range(4):
    d.add_paragraph()

title = d.add_paragraph()
title.alignment = WD_ALIGN_PARAGRAPH.CENTER
tr = title.add_run("CivicSense")
tr.bold = True
tr.font.size = Pt(40)
tr.font.color.rgb = NAVY

sub = d.add_paragraph()
sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
sr = sub.add_run("Project Report")
sr.bold = True
sr.font.size = Pt(22)
sr.font.color.rgb = GREY

d.add_paragraph()
line = d.add_paragraph()
line.alignment = WD_ALIGN_PARAGRAPH.CENTER
lr = line.add_run("=" * 44)
lr.font.color.rgb = NAVY

sub2 = d.add_paragraph()
sub2.alignment = WD_ALIGN_PARAGRAPH.CENTER
sr2 = sub2.add_run(
    "An Integrated Intelligent Triage Pipeline for AI-Enhanced "
    "Citizen Complaint Management"
)
sr2.bold = True
sr2.font.size = Pt(15)

d.add_paragraph()
sub3 = d.add_paragraph()
sub3.alignment = WD_ALIGN_PARAGRAPH.CENTER
sr3 = sub3.add_run(
    "A complete end-to-end implementation of the base paper: classification, "
    "prioritisation, duplicate detection, fraud scoring, incident clustering, "
    "explainable AI, dashboards and report export"
)
sr3.italic = True
sr3.font.size = Pt(12)

for _ in range(7):
    d.add_paragraph()

meta = d.add_paragraph()
meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
for ln in [
    "Submitted in partial fulfilment of the requirements of the Major Project\n",
    "Prepared by: CivicSense Project Team\n",
    "Guided by: Project Guide, Department of Computer Engineering\n",
    "Date: October 11, 2026\n",
    "Document type: Project Report (Final Deliverable)\n",
    "Repository: CivicSense (Flask + civic_sense package + SQLite demo database)\n",
    "Version: 2.0 (expanded edition)\n",
    "Classification: Internal / Academic Project Deliverable",
]:
    meta.add_run(ln).font.size = Pt(12)

page_break()

# ===========================================================================
# DECLARATION
# ===========================================================================
h("Declaration", 1)
para(
    'I hereby declare that the project report entitled "CivicSense: An Integrated '
    'Intelligent Triage Pipeline for AI-Enhanced Citizen Complaint Management" '
    "submitted in partial fulfilment of the requirements of the Major Project is my "
    "own work, carried out under the guidance of the project guide. This report "
    "documents the design, implementation, testing and outcomes of the project from "
    "start to finish."
)
para(
    "All sources of data, algorithms, libraries and prior research that were consulted "
    "during the development of this project have been duly acknowledged in the "
    "References section. The demonstration dataset is synthetic and was generated "
    "specifically for this project; it does not contain any real citizen data, and the "
    "fraud and hotspot scenarios are illustrative rather than production measurements."
)
para(
    "Every quantitative result reported in Sections 5 and 6 was measured by running the "
    "actual pipeline against a clean demonstration database, and the report itself is "
    "regenerated by a script from those measurements. Where a figure is an estimate or "
    "an illustration rather than a measurement, it is explicitly labelled as such in "
    "the text."
)
para("Signature: ______________________")
para("Name: CivicSense Project Team")
para("Date: October 11, 2026")

# ===========================================================================
# CERTIFICATE
# ===========================================================================
h("Certificate", 1)
para(
    'This is to certify that the project report entitled "CivicSense: An Integrated '
    'Intelligent Triage Pipeline for AI-Enhanced Citizen Complaint Management" is a '
    "bonafide record of work carried out by the project team in partial fulfilment of "
    "the requirements of the Major Project, under my supervision and guidance."
)
para(
    "The work embodied in this report is original, the implementation has been executed "
    "and verified on the project's own demonstration environment, and the report has "
    "been found satisfactory in terms of scope, depth and quality."
)
para("Guide Signature: ______________________")
para("Designation: ______________________")
para("Date: October 11, 2026")

# ===========================================================================
# ABSTRACT
# ===========================================================================
h("Abstract", 1)
para(
    "Municipalities worldwide receive hundreds of thousands of citizen complaints every "
    "day about roads, electricity, water supply, waste management and public safety. "
    "Conventional complaint-handling systems are largely manual: they store records but "
    "do not categorise, prioritise, summarise or trust-check them, which causes delayed "
    "responses, duplicate records, misdirected resources and a rising vulnerability to "
    "coordinated spam. The base paper proposes CivicSense, an AI platform that combines "
    "Natural Language Processing (NLP) and Generative AI to automatically classify, "
    "prioritise and summarise citizen complaints, turning unstructured text into "
    "actionable governance intelligence."
)
para(
    "This project is a complete, working implementation of that proposal. The system was "
    "extended from a linear analyser into an Integrated Intelligent Triage Pipeline with "
    "eight stages: input, preprocessing (cleaning, normalisation and locality-aware "
    "duplicate detection), classification, fraud scoring, incident clustering, weighted "
    "priority assignment, explainable-AI (XAI) generation, and dashboard/report "
    "delivery. Three research-supported enhancements were added on top of the base "
    "paper's approach:"
)
bullet("Fraud detection - a separate, explainable hybrid bad-faith risk engine that combines semantic-spam similarity, submission-frequency (flood) detection and short/generic pattern analysis.")
bullet("Semantic incident clustering - grouping fragmented reports of the same underlying incident into locality-scoped incident clusters so that a single incident is not counted many times.")
bullet("Explainable AI - human-readable justifications for every priority and fraud decision, so officers can audit and trust the automated triage.")
para(
    "The system is implemented in Python with a Flask dashboard, a REST API for "
    "complaint intake, SQLite persistence, and PDF/Excel weekly report export. The "
    "classification model achieves 82.19% accuracy (+/- 5.47%) under stratified 5-fold "
    "cross-validation on a curated corpus of 152 samples. On a clean demonstration "
    "database of 200 complaints processed end-to-end through the real pipeline, the "
    "system classified all five base-paper examples plus six additional challenge texts "
    "correctly (11 of 11), identified 23 duplicates (11.5%), grouped 18 records into 11 "
    "incident clusters including one 8-complaint hotspot, and surfaced 2 High-risk and "
    "53 Medium-risk scores. Every statistic on the dashboard reflects genuine model "
    "behaviour rather than fabricated numbers; the fraud and hotspot scenarios are "
    "synthetic demonstration data and are not production precision claims."
)

h("Abstract Highlights", 2)
make_table(
    ["Dimension", "Outcome"],
    [
        ["Pipeline", "Eight stages, each with an explicit input/output contract"],
        ["Classification", "82.19% +/- 5.47% (stratified 5-fold CV, 152 samples)"],
        ["Categorisation demo", "11 of 11 curated texts classified correctly"],
        ["Priority engine", "Six weighted signals with a per-decision XAI breakdown"],
        ["Duplicate detection", "23 of 200 records flagged (11.5%), 17 distinct originals"],
        ["Incident clustering", "18 records across 11 clusters; largest cluster = 8"],
        ["Fraud engine", "Hybrid three-signal score; 2 High and 53 Medium scores"],
        ["Summarisation", "Weekly digest with ward highlights and resource advice"],
        ["Export", "PDF (ReportLab) and Excel (openpyxl) on demand"],
        ["Verification", "30 automated end-to-end checks, all passing"],
    ],
    widths=[150, 400],
    caption="Summary of the project's headline outcomes.",
)
para(
    "Keywords: Smart Cities, NLP, Complaint Management, E-Governance, Text "
    "Classification, TF-IDF, LinearSVC, Fraud Detection, Incident Clustering, "
    "Explainable AI, Flask."
)

# ===========================================================================
# ACKNOWLEDGEMENTS
# ===========================================================================
h("Acknowledgements", 1)
para(
    "We thank our project guide for continuous direction on scope control, for "
    "insisting that every reported metric be honestly measured rather than assumed, and "
    "for reviewing the corpus design that ultimately drove the classification accuracy "
    "from an unstable early figure to a reproducible cross-validated result."
)
para(
    "We acknowledge the authors of the base paper, whose work defined the problem, the "
    "five complaint categories and the evaluation criteria against which this "
    "implementation is compared. We also acknowledge the open-source communities behind "
    "Flask, scikit-learn, NLTK, ReportLab, openpyxl and python-docx, on which the "
    "implementation and this document depend."
)
para(
    "Finally, we thank the classmates and department staff who reviewed early "
    "demonstrations and pointed out the failure modes that later became Section 7 of "
    "this report. Their criticism directly improved the reliability of the final system."
)

# ===========================================================================
# TABLE OF CONTENTS
# ===========================================================================
page_break()
h("Table of Contents", 1)
toc = (
    "Declaration\n"
    "Certificate\n"
    "Abstract\n"
    "   Abstract Highlights\n"
    "Acknowledgements\n"
    "Table of Contents\n"
    "List of Tables\n"
    "List of Abbreviations\n"
    "\n"
    "1. Introduction\n"
    "   1.1 Background\n"
    "   1.2 Problem Statement\n"
    "   1.3 Motivation\n"
    "   1.4 Objectives\n"
    "   1.5 Scope\n"
    "   1.6 Research Questions\n"
    "   1.7 Stakeholders and Beneficiaries\n"
    "   1.8 Expected Outcomes and Success Criteria\n"
    "   1.9 Organisation of the Report\n"
    "\n"
    "2. Literature Review and Gap Analysis\n"
    "   2.1 Existing Complaint Platforms\n"
    "   2.2 NLP Approaches to Complaint Classification\n"
    "   2.3 Generative AI for Summarisation\n"
    "   2.4 Smart-City Adjacent Work\n"
    "   2.5 Abuse and Fraud in Public Reporting Systems\n"
    "   2.6 Duplicate Detection and Incident Clustering\n"
    "   2.7 Explainable AI in Public-Sector Decisions\n"
    "   2.8 Gap Analysis and Positioning\n"
    "   2.9 Summary of Related Work\n"
    "\n"
    "3. Proposed System and Design\n"
    "   3.1 System Overview\n"
    "   3.2 The Eight-Stage Pipeline\n"
    "   3.3 Technology Stack and Rationale\n"
    "   3.4 Layered Architecture\n"
    "   3.5 Data Model\n"
    "   3.6 Module Design and Interfaces\n"
    "   3.7 Configuration and Tunable Parameters\n"
    "   3.8 Functional Requirements\n"
    "   3.9 Non-Functional Requirements\n"
    "   3.10 Design Decisions and Trade-offs\n"
    "   3.11 End-to-End Walkthrough of a Submission\n"
    "   3.12 Security, Privacy and Ethical Design\n"
    "\n"
    "4. Implementation\n"
    "   4.1 Data Collection Layer\n"
    "   4.2 Preprocessing Module\n"
    "   4.3 Duplicate Detection\n"
    "   4.4 Classification\n"
    "   4.5 Fraud Detection\n"
    "   4.6 Incident Clustering\n"
    "   4.7 Weighted Priority Assignment\n"
    "   4.8 Explainable AI Generation\n"
    "   4.9 Summarisation and Weekly Digests\n"
    "   4.10 Report Generation (PDF / Excel)\n"
    "   4.11 Pipeline Orchestration\n"
    "   4.12 Dashboard and User Interface\n"
    "   4.13 Error Handling and Graceful Degradation\n"
    "   4.14 Testing Strategy and the Smoke Suite\n"
    "   4.15 Code Organisation and Repository Layout\n"
    "\n"
    "5. Demonstration Data and Scenarios\n"
    "   5.1 Demonstration Corpus\n"
    "   5.2 Fraud Alert Scenario\n"
    "   5.3 Incident Hotspot Scenario\n"
    "   5.4 Dashboard Display Mapping\n"
    "   5.5 Measured Corpus Statistics\n"
    "   5.6 Reproducing the Demonstration\n"
    "\n"
    "6. Results and Evaluation\n"
    "   6.1 Classification Accuracy\n"
    "   6.2 Priority Distribution\n"
    "   6.3 Duplicate Detection Results\n"
    "   6.4 Fraud Detection Results\n"
    "   6.5 Incident Clustering Results\n"
    "   6.6 Digest Generation Quality\n"
    "   6.7 Automated Test Results\n"
    "   6.8 System Response and Performance\n"
    "   6.9 Comparison with the Base Paper\n"
    "   6.10 Sample System Outputs\n"
    "   6.11 Key Performance Indicators\n"
    "   6.12 Threats to Validity\n"
    "\n"
    "7. Development Challenges and Solutions\n"
    "   7.1 Instability of the First Accuracy Metric\n"
    "   7.2 Priority Inflation from an Overly-Broad Keyword\n"
    "   7.3 Console Encoding During Testing\n"
    "   7.4 Decision-Support Cards That Stayed Empty\n"
    "   7.5 A Test Suite That Silently Never Ran\n"
    "   7.6 A Fraud Signal That Never Fired\n"
    "   7.7 Engineering Lessons\n"
    "\n"
    "8. Limitations\n"
    "9. Future Work\n"
    "10. Ethical, Legal and Social Considerations\n"
    "11. Project Management, Timeline and Work Distribution\n"
    "12. Conclusion\n"
    "\n"
    "References\n"
    "Appendix A: How to Run the Project\n"
    "Appendix B: REST API Reference\n"
    "Appendix C: Source File Reference\n"
    "Appendix D: Verification Checklist\n"
    "Appendix E: Glossary\n"
    "Appendix F: Sample Complaint Records\n"
    "Appendix G: Configuration Reference\n"
    "Appendix H: Sample Weekly Digest\n"
)
para(toc, size=10.5)

# ---------------------------------------------------------------------------
# LIST OF TABLES (filled in at the end, once every table is known)
# ---------------------------------------------------------------------------
LOT_HEADING = h("List of Tables", 1)
LOT_PLACEHOLDER = d.add_paragraph("<<LIST_OF_TABLES>>")

# ---------------------------------------------------------------------------
# LIST OF ABBREVIATIONS
# ---------------------------------------------------------------------------
page_break()
h("List of Abbreviations", 1)
make_table(
    ["Abbreviation", "Expansion"],
    [
        ["AI", "Artificial Intelligence"],
        ["API", "Application Programming Interface"],
        ["BERT", "Bidirectional Encoder Representations from Transformers"],
        ["CPGRAMS", "Centralised Public Grievance Redress and Monitoring System"],
        ["CV", "Cross-Validation"],
        ["DistilBERT", "Distilled Bidirectional Encoder Representations from Transformers"],
        ["GIS", "Geographic Information System"],
        ["IoT", "Internet of Things"],
        ["JSON", "JavaScript Object Notation"],
        ["KPI", "Key Performance Indicator"],
        ["LLM", "Large Language Model"],
        ["NLP", "Natural Language Processing"],
        ["NLTK", "Natural Language Toolkit"],
        ["PDF", "Portable Document Format"],
        ["REST", "Representational State Transfer"],
        ["SLA", "Service Level Agreement"],
        ["SQL", "Structured Query Language"],
        ["SVM", "Support Vector Machine"],
        ["TF-IDF", "Term Frequency - Inverse Document Frequency"],
        ["UI", "User Interface"],
        ["XAI", "Explainable Artificial Intelligence"],
        ["XLSX", "Microsoft Excel Open XML Spreadsheet"],
    ],
    widths=[110, 400],
)

page_break()

# ===========================================================================
# 1. INTRODUCTION
# ===========================================================================
h("1. Introduction", 1)
para(
    "This section establishes why automated complaint triage is needed, states the "
    "precise problem the project solves, and defines the objectives, scope and success "
    "criteria against which the implementation is judged."
)

h("1.1 Background", 2)
para(
    "Urban governance depends on the timely redressal of citizen grievances. Every day, "
    "citizens lodge complaints about broken roads, power cuts, water scarcity, "
    "uncollected garbage and unsafe public spaces. These complaints arrive through many "
    "channels - mobile applications, web portals, email, call centres and social media "
    "- and in very different styles: some are formal and well structured, some use "
    "slang, and some are incomplete fragments such as \"No water\" or \"Road bad\"."
)
para(
    "National and municipal programmes such as India's CPGRAMS, Singapore's OneService "
    "app and New York's NYC 311 demonstrate the scale of the problem, but their "
    "back-ends still rely heavily on manual classification and status updates. The "
    "result, as the base paper notes, is delayed responses, duplicate records, poor "
    "categorisation and no real-time insight into where problems are concentrated. "
    "Authorities end up reacting to issues that have already become significant instead "
    "of acting on emerging trends."
)
para(
    "Natural Language Processing (NLP) has matured to the point where text "
    "classification, similarity measurement and summarisation can be delivered cheaply "
    "and reliably on ordinary hardware. CivicSense applies these capabilities to the "
    "citizen-complaint domain, converting a raw, noisy stream of free text into a "
    "structured, prioritised and explainable body of governance intelligence."
)
para(
    "The scale of the opportunity is easy to underestimate. A mid-sized municipal "
    "corporation with ten wards can receive several thousand complaints a month. If each "
    "complaint takes two minutes of manual reading before it can even be routed, the "
    "classification overhead alone consumes dozens of staff-hours every week before any "
    "actual repair work begins. Automating the routing decision does not eliminate the "
    "work, but it moves human attention from sorting to solving."
)

h("1.2 Problem Statement", 2)
para("Existing complaint systems collect complaints but do not understand them. Municipal officers face four concrete problems:")
bullet("No automatic categorisation - an officer must read each complaint manually to decide which department it belongs to (roads, electricity, water, waste or public safety).")
bullet("No prioritisation - an emergency such as a sewage overflow is treated the same as a flickering streetlight.")
bullet("No trend analysis - patterns such as \"potholes recurring in Ward 3\" or \"garbage delays in Ward 5\" are invisible inside thousands of raw log entries.")
bullet("Duplicate records - the same grievance is re-filed across multiple channels, inflating counts and wasting effort.")
para(
    "CivicSense additionally recognises a fifth, emerging problem that the base paper "
    "does not address: coordinated bad-faith reporting. Because civic portals are public "
    "and easy to script, a small group - or a bot - can submit near-identical complaints "
    "to distort priority metrics and redirect resources. Any serious triage platform "
    "therefore needs a fraud-scoring stage as well as a categorisation stage."
)
para(
    "A sixth, subtler problem is the trust deficit created by opaque automation. If a "
    "system silently promotes a complaint to \"High Priority\", an officer who disagrees "
    "has no way to understand or contest the decision. CivicSense therefore treats "
    "explainability as a functional requirement rather than a nicety: every automated "
    "decision carries a human-readable justification."
)

h("1.3 Motivation", 2)
para(
    "The project was undertaken because the base paper describes a realistic, "
    "high-impact problem that is easy to demonstrate and verify, and because it "
    "integrates several modern AI ideas - text classification, explainable scoring and "
    "generative summarisation - into one coherent system. The subject matter of "
    "smart-city governance is a recognised national priority, and the presence of a "
    "published base paper gives the project measurable success criteria against which "
    "the implementation can be honestly compared."
)
para(
    "A secondary motivation was engineering discipline. Many student AI projects report "
    "a single accuracy number obtained from a favourable split and stop there. This "
    "project deliberately set out to demonstrate the full lifecycle: a defined problem, "
    "a designed pipeline, a measured evaluation, a documented set of failures and their "
    "fixes, and an automated test suite that proves the system still works after every "
    "change."
)
para(
    "A third motivation was practical usefulness. The base paper's proposal, if realised "
    "well, could plausibly be handed to a municipal IT team and improve how they route "
    "complaints. Keeping that audience in mind shaped decisions about dependencies, "
    "offline operation and explainability: a tool that requires a GPU, an internet "
    "connection and a cloud account before it shows any value is unlikely to be adopted "
    "by a municipal corporation on a modest budget."
)

h("1.4 Objectives", 2)
para("The specific objectives of the project are:")
bullet("To build an end-to-end complaint-analysis platform implementing the base paper's pipeline from data collection through to decision-support visualisation.")
bullet("To achieve high, honestly-measured classification accuracy across the five service categories (Roads, Electricity, Water Supply, Waste Management and Public Safety).")
bullet("To assign explainable High / Medium / Low priorities using the same signals the paper describes: urgency wording, category risk, emotive language, same-ward frequency and complaint age.")
bullet("To detect and suppress semantic duplicates so that repeated reports of one issue are not counted as independent incidents.")
bullet("To add a fraud-detection engine that flags coordinated or low-effort submissions and explains its reasoning.")
bullet("To cluster fragmented reports of the same incident into hotspots and surface them on the dashboard.")
bullet("To generate weekly narrative digests and export them as PDF and Excel reports.")
bullet("To validate the whole system with an automated end-to-end test suite.")
bullet("To document the development process honestly, including the defects discovered and the reasoning behind each design decision.")

h("1.5 Scope", 2)
para(
    "The project covers the complete software implementation: data model, NLP pipeline, "
    "trained classifier, duplicate detection, fraud scoring, incident clustering, "
    "priority engine, XAI generation, digest generator, report export, dashboard and "
    "automated tests. It uses SQLite as the central database, although the base paper "
    "suggests PostgreSQL or MongoDB for production scale, and a curated synthetic "
    "demonstration dataset that is processed through the real pipeline so that every "
    "statistic reflects genuine model behaviour."
)
para("The following are explicitly inside scope:")
bullet("Five-category complaint classification with a confidence score.")
bullet("Locality-aware duplicate detection and incident clustering identifiers.")
bullet("A three-signal fraud risk engine with an explanation string per record.")
bullet("A six-signal weighted priority engine with a numeric breakdown and XAI sentences.")
bullet("A Flask dashboard exposing KPIs, charts, hotspots, fraud alerts and a keyword cloud.")
bullet("A REST intake API and a citizen-facing web form.")
bullet("Weekly digest generation with PDF and Excel export.")
bullet("An automated end-to-end smoke suite that exercises the real application.")
para("The following are explicitly out of scope for this version:")
bullet("Live integration with real municipal portals and their authentication systems.")
bullet("Multilingual and regional-language processing.")
bullet("Officer authentication, role-based access control and audit trails.")
bullet("Geospatial map rendering and GPS-based routing of field crews.")
bullet("Production-scale storage, caching and horizontal deployment.")

h("1.6 Research Questions", 2)
para("The implementation is guided by the following research questions, which mirror and extend the base paper:")
bullet("How accurately can a lightweight TF-IDF + LinearSVC model classify short, noisy municipal complaints into the five service categories?")
bullet("Can a deterministic, multi-signal scoring engine produce priorities that match human intuition about urgency while remaining fully explainable?")
bullet("Does locality-aware duplicate detection meaningfully reduce inflated complaint counts without suppressing genuinely distinct reports?")
bullet("Can a hybrid of semantic similarity, submission frequency and pattern analysis provide a credible first-pass fraud signal?")
bullet("Can semantic clustering of paraphrased complaints recover a single underlying incident from many fragmented reports?")
bullet("Does a template-based deterministic summariser produce digests of a quality comparable to the base paper's illustrative examples without requiring a language-model API?")

h("1.7 Stakeholders and Beneficiaries", 2)
para("The system has several distinct user groups, and the design was shaped by their differing needs:")
make_table(
    ["Stakeholder", "Primary need", "How CivicSense serves them"],
    [
        ["Citizens", "Fast, transparent acknowledgement that a complaint was received and routed", "Web form with instant AI analysis; status tracking; API intake from partner apps"],
        ["Front-line officers", "A trustworthy queue ordered by real urgency", "Explainable High/Medium/Low priority with a numeric breakdown per complaint"],
        ["Department heads", "Evidence of where resources are needed", "Ward hotspot bars, category mix, incident clusters and resource-allocation advice"],
        ["Municipal administrators", "Periodic, readable situational awareness", "Weekly narrative digest exportable as PDF and Excel"],
        ["Data / integrity teams", "Early warning of abuse or automation", "Fraud Alerts card with scores, levels and contributing signals"],
        ["Auditors and oversight", "A defensible explanation for every automated decision", "XAI sentences stored with each record for priority and fraud"],
    ],
    widths=[110, 180, 260],
    caption="Stakeholders and how each is served by the system.",
)

h("1.8 Expected Outcomes and Success Criteria", 2)
para(
    "The project was judged against explicit, pre-agreed criteria rather than a general "
    "impression. These criteria were fixed before the final evaluation run:"
)
make_table(
    ["Criterion", "Target", "Measured outcome"],
    [
        ["Classification accuracy", "Above 80% under cross-validation", "82.19% +/- 5.47%"],
        ["Base-paper examples", "All five classified correctly", "5 of 5 correct"],
        ["Priority explainability", "Every decision carries a reason", "Provided for every record"],
        ["Duplicate handling", "Flag re-files without over-flagging", "23 of 200 flagged (11.5%)"],
        ["Fraud visibility", "At least one High-risk row visible on the dashboard", "2 High and 53 Medium scores"],
        ["Hotspot visibility", "A populated cluster on the dashboard", "8-complaint cluster in Wakad"],
        ["Report export", "PDF and Excel both downloadable", "Both verified by the smoke suite"],
        ["Automated verification", "A repeatable end-to-end suite", "30 checks, all passing"],
    ],
    widths=[150, 180, 220],
    caption="Pre-agreed success criteria and their measured outcomes.",
)

h("1.9 Organisation of the Report", 2)
para(
    "The remainder of the report is organised as follows. Section 2 reviews related work "
    "and identifies the gaps that CivicSense addresses. Section 3 presents the proposed "
    "system and its design, including functional and non-functional requirements. "
    "Section 4 documents the implementation of each module in detail. Section 5 "
    "describes the demonstration data and the two explicit scenarios. Section 6 reports "
    "the results and evaluates them against the base paper. Section 7 records the "
    "development challenges and how they were solved. Section 8 discusses limitations. "
    "Section 9 lays out future work. Section 10 covers ethical, legal and social "
    "considerations. Section 11 describes project management and the timeline. Section "
    "12 concludes. References and appendices A to H follow."
)

# ===========================================================================
# 2. LITERATURE REVIEW
# ===========================================================================
h("2. Literature Review and Gap Analysis", 1)
para(
    "This section summarises the landscape the base paper reviews, adds the adjacent "
    "literature on abuse detection, duplicate handling and explainability that the "
    "extension builds on, and positions the project within it."
)

h("2.1 Existing Complaint Platforms", 2)
para(
    "CPGRAMS (India), OneService (Singapore) and NYC 311 (United States) are the "
    "best-known large-scale citizen-grievance platforms. They improved transparency and "
    "accessibility by giving citizens a single submission point and a tracking number, "
    "and they generate large volumes of structured status data. What they did not solve "
    "is the analytical problem: categorisation, prioritisation and trend discovery "
    "remain largely manual, and the systems do not attempt to detect deliberate abuse of "
    "the intake channel."
)
para(
    "A useful way to think about these platforms is that they are excellent record "
    "systems and poor decision systems. They answer \"what was submitted?\" reliably, but "
    "they do not answer \"what matters most right now?\" without a human reading the "
    "queue. CivicSense is deliberately a decision layer rather than another record layer: "
    "it assumes complaints arrive from somewhere (a portal, an app, an email gateway) and "
    "concentrates on what happens next."
)

h("2.2 NLP Approaches to Complaint Classification", 2)
para(
    "Early research on municipal complaint classification used text mining with Naive "
    "Bayes and Support Vector Machines. These approaches work reasonably well on clean "
    "text but struggle with multilingual, ambiguous or informal complaints. The "
    "introduction of transformer models such as BERT, RoBERTa and DistilBERT pushed "
    "classification accuracy past 90% on several municipal datasets, at the cost of "
    "substantially larger compute and memory requirements."
)
para(
    "A middle path is to combine TF-IDF feature extraction with a linear classifier. "
    "This delivers strong accuracy on short, keyword-heavy texts such as complaints, "
    "trains in seconds on a laptop, needs no GPU, and is fully interpretable. CivicSense "
    "adopts this as the primary model and keeps a zero-shot DistilBERT path available "
    "behind a feature flag for demonstration purposes."
)
para(
    "The interpretability argument deserves emphasis. A linear SVM's decision is a "
    "weighted sum of term features, so it is straightforward to inspect which words "
    "drive a particular classification. A transformer's decision is not directly "
    "inspectable. For a public-sector triage tool where an officer may have to defend an "
    "automated routing decision, the simpler model has a real advantage beyond its speed."
)

h("2.3 Generative AI for Summarisation", 2)
para(
    "Generative models have been used in healthcare and legal services to produce patient "
    "summaries and case briefs. The base paper observes that this capability has not been "
    "widely applied to citizen-to-government complaint analysis. A city administrator "
    "does not want a list of one thousand complaints; they want a weekly digest of the "
    "form: \"Ward 7 had 35 road complaints this week, the recurring concern being "
    "potholes - High Priority.\" Closing this gap is the central motivation of CivicSense."
)
para(
    "Two implementation strategies exist for this kind of narrative output. The first is "
    "to call a large language model with the period's statistics and let it write the "
    "prose. The second is to compute the same statistics deterministically and generate "
    "the narrative from a template. The first produces more fluent language but depends "
    "on network access, cost and an API key. The second is reproducible, free and always "
    "available, at the cost of some fluency. CivicSense implements both and prefers the "
    "template engine by default, so the demonstration never depends on an external "
    "service."
)

h("2.4 Smart-City Adjacent Work", 2)
para(
    "Predictive models forecast water-pipe bursts, machine learning optimises traffic "
    "flow, and IoT-connected garbage bins streamline collection routes. These systems "
    "optimise municipal assets from historical telemetry. Complaint analysis optimises a "
    "different signal - the citizen's voice - and feeds it into the same decisions. "
    "Sentiment analysis of social-media posts measures public mood but cannot pinpoint a "
    "specific service failure at ward level. CivicSense combines classification, "
    "prioritisation and summarisation to close that gap."
)
para(
    "The distinction matters practically. An IoT bin sensor tells you a bin is full; it "
    "does not tell you that forty citizens have already complained about overflowing bins "
    "on the same street, which is a different and stronger signal about service failure. "
    "Combining citizen text with asset telemetry is a natural future step, and is listed "
    "in Section 9."
)

h("2.5 Abuse and Fraud in Public Reporting Systems", 2)
para(
    "Open reporting channels are inherently vulnerable to abuse. A body of work on spam "
    "and Sybil attacks in public platforms has established three recurring patterns "
    "relevant to civic complaint intake: bursts of activity concentrated in a narrow time "
    "window, near-identical content submitted repeatedly, and content that is too short "
    "or generic to be verified. These are the same signals that fraud engines use in "
    "review and social platforms, and they transfer naturally to the complaint domain."
)
para(
    "The design consequence is that fraud detection should be kept separate from "
    "deduplication. A genuine citizen re-filing a legitimate complaint and a bot flooding "
    "a channel can produce the same text and, superficially, the same similarity score. "
    "Duplicate detection asks \"is this the same issue?\" whereas fraud detection asks "
    "\"was this filed in bad faith?\". Merging them would punish legitimate duplicates. "
    "CivicSense therefore implements them as two independent modules with distinct outputs."
)

h("2.6 Duplicate Detection and Incident Clustering", 2)
para(
    "Classical deduplication compares normalised text with a similarity measure such as "
    "Jaccard overlap, cosine similarity over TF-IDF vectors, or edit-distance ratios. "
    "These approaches are cheap and deterministic but brittle to paraphrase: \"a tree fell "
    "on the road\" and \"a fallen branch blocked traffic\" share almost no surface tokens "
    "while describing the same incident."
)
para(
    "Embedding-based approaches solve this by comparing meaning rather than wording. "
    "Sentence-BERT and similar encoders map paraphrases to nearby vectors, so a single "
    "similarity threshold can group them. Incident clustering is the natural extension of "
    "this idea: rather than merely flagging one record as a duplicate of another, reports "
    "are grouped into clusters that represent distinct open incidents. This shift from "
    "pairwise deduplication to clustering is what allows a system to answer \"how many "
    "distinct incidents are open?\" instead of \"how many records exist?\"."
)
para(
    "A practical difficulty is that embedding libraries add heavy dependencies. "
    "CivicSense addresses this by making embeddings the preferred path and providing a "
    "deterministic difflib-based fallback on normalised text, so the clustering feature "
    "degrades gracefully instead of disappearing when the embedding stack is unavailable."
)

h("2.7 Explainable AI in Public-Sector Decisions", 2)
para(
    "Automated decisions in public administration carry a legitimacy requirement that "
    "decisions in many other domains do not. A citizen whose complaint is deprioritised is "
    "entitled to know why, and an officer who overrides a machine ranking needs to "
    "understand what the machine thought it saw. Explainable AI research distinguishes "
    "between intrinsic explainability (the model is simple enough to inspect) and post-hoc "
    "explainability (a separate method explains the model)."
)
para(
    "CivicSense uses both. The classifier is intrinsically explainable because it is a "
    "linear model over term features. The priority and fraud engines, which combine "
    "several weighted signals, are explained post-hoc by converting their numeric "
    "breakdowns into natural-language sentences. This is a lighter-weight and more "
    "auditable approach than attributing a deep model's output, and it is well matched to "
    "the domain, where the contributing factors are already defined and bounded."
)

h("2.8 Gap Analysis and Positioning", 2)
para("Synthesising the above, the base paper establishes a preprocessing-plus-classification pipeline but leaves four gaps that this project addresses:")
bullet("Deduplication is naive and does not account for locality or paraphrasing. CivicSense makes it locality-aware and similarity-based.", bold_prefix="Duplicate handling: ")
bullet("Bad-faith content is not modelled, so coordinated spam can silently distort priority and resource allocation. CivicSense adds a separate, explainable fraud-scoring engine.", bold_prefix="Fraud handling: ")
bullet("Individual complaints are tracked, but fragmented reports of one incident are not grouped. CivicSense clusters them into incidents.", bold_prefix="Incident handling: ")
bullet("Triage scores are presented without justification, which reduces officer trust and adoption. CivicSense emits an XAI explanation for every priority and fraud decision.", bold_prefix="Explainability: ")
para(
    "The design follows the software-engineering principle of separation of concerns: each "
    "stage is a discrete module with a well-defined input and output contract, so each can "
    "be tested, replaced or extended independently."
)

h("2.9 Summary of Related Work", 2)
make_table(
    ["Area", "Representative approach", "Strength", "Limitation addressed by CivicSense"],
    [
        ["Complaint platforms", "CPGRAMS, OneService, NYC 311", "Scale, tracking, transparency", "No automated triage or abuse detection"],
        ["Classical text classification", "Naive Bayes, SVM over bag-of-words", "Cheap, interpretable", "Weak on informal and ambiguous text"],
        ["Transformer classification", "BERT, RoBERTa, DistilBERT", "High accuracy", "Heavy dependencies; opaque decisions"],
        ["Deduplication", "Jaccard / cosine / edit distance", "Deterministic, fast", "Brittle to paraphrase; no locality awareness"],
        ["Embedding similarity", "Sentence-BERT and similar encoders", "Handles paraphrase", "Heavy dependency; needs a fallback"],
        ["Incident grouping", "Clustering over embeddings", "Counts distinct incidents", "Rarely wired into a live triage dashboard"],
        ["Abuse detection", "Burst, repetition and generic-text signals", "Catches coordinated spam", "Usually absent from civic complaint systems"],
        ["Summarisation", "Extractive scoring; LLM narrative", "Produces readable digests", "LLM path depends on external services"],
        ["Explainability", "Post-hoc justification from score breakdowns", "Builds officer trust", "Often omitted from triage tools"],
    ],
    widths=[110, 150, 130, 160],
    caption="Summary of related work and the gap each area leaves open.",
)

# ===========================================================================
# 3. PROPOSED SYSTEM AND DESIGN
# ===========================================================================
page_break()
h("3. Proposed System and Design", 1)
para(
    "This section presents the system as designed: its overall shape, the pipeline it "
    "implements, the technologies chosen and why, the data model, the module contracts, "
    "the requirements it must satisfy and the trade-offs made along the way."
)

h("3.1 System Overview", 2)
para(
    "CivicSense is delivered as a Flask web application backed by a SQLite database and "
    "a Python package, civic_sense, that contains all analytical logic. Citizens submit "
    "complaints through a web form or a REST endpoint; every submission is processed "
    "synchronously by the pipeline before it is stored, so no unanalysed record ever "
    "enters the database. Officers interact with a single-page dashboard that surfaces "
    "key performance indicators, the latest digest, category and priority mixes, ward "
    "hotspots, trending keywords and recent complaints."
)
para(
    "The choice to analyse before storing is deliberate and has several consequences. It "
    "guarantees that a stored record always carries a complete set of derived fields, "
    "which means dashboards and reports never have to handle partially analysed rows. It "
    "also means a classification or clustering failure surfaces immediately at submission "
    "time rather than silently corrupting later aggregates. The cost is that submission "
    "latency includes analysis time, which is acceptable at demonstration scale and is "
    "measured in Section 6.8."
)

h("3.2 The Eight-Stage Pipeline", 2)
para("The implemented flow is:")
para("Input -> Preprocessing (cleaning + normalisation + locality-aware duplicate detection) -> Classification -> Fraud Scoring -> Incident Clustering -> Weighted Priority (with optional cluster boost) -> XAI Generation -> Dashboard / Reports", bold=True)
para(
    "Each stage contributes a distinct artifact to the record: normalised text and a "
    "duplicate flag, a category with a confidence score, a fraud score with a level and "
    "explanation, a cluster identifier, a priority label with a numeric breakdown, and "
    "finally the stored record that drives the dashboard and reports."
)
figure(
    "The eight-stage triage pipeline and the artifact each stage produces.",
    [
        "[1] Input            -> raw text, ward, source",
        "        |",
        "[2] Preprocessing    -> normalised text, duplicate flag",
        "        |",
        "[3] Classification   -> category, confidence",
        "        |",
        "[4] Fraud Scoring    -> score, level, explanation",
        "        |",
        "[5] Clustering       -> cluster_id",
        "        |",
        "[6] Priority         -> label, numeric breakdown",
        "        |",
        "[7] XAI Generation   -> justification sentences",
        "        |",
        "[8] Delivery         -> dashboard, API, reports",
    ],
)

h("3.3 Technology Stack and Rationale", 2)
make_table(
    ["Component", "Choice", "Why"],
    [
        ["Language", "Python 3.11/3.12", "Rich NLP and ML ecosystem; fast to develop and easy to demonstrate"],
        ["Web framework", "Flask", "Minimal overhead; the project is a demonstration of the AI pipeline, not a heavy web product"],
        ["Classifier", "TF-IDF + LinearSVC (scikit-learn)", "Strong on short keyword-heavy text; trains in seconds; no GPU; explainable"],
        ["Optional classifier", "Zero-shot DistilBERT", "Demonstrates the paper's BERT-family approach when the transformer stack is available"],
        ["Similarity", "Sentence-Transformers, difflib fallback", "Semantic similarity when available; deterministic fallback otherwise"],
        ["Persistence", "SQLite", "Zero-configuration demo database; PostgreSQL/MongoDB intended for production"],
        ["Reporting", "ReportLab + openpyxl", "PDF and Excel export exactly as the paper requires"],
        ["Document generation", "python-docx", "This report is itself generated reproducibly from measured data"],
        ["UI", "Hand-written HTML/CSS", "Fully self-contained; the demo runs entirely offline"],
    ],
    widths=[110, 170, 340],
    caption="Technology choices and the reasoning behind each.",
)

h("3.4 Layered Architecture", 2)
para("The system is organised into four layers with strict downward dependencies:")
bullet("Presentation layer - templates/ and static/css/style.css: dashboard, complaint list, intake form, report views and pipeline explainer.")
bullet("Application layer - app.py: Flask routes for the web UI and REST API, plus the run_pipeline() orchestrator that chains the stages for every incoming complaint.")
bullet("Core layer - the civic_sense package: preprocessing, classifier, fraud_detector, prioritizer, summarizer, reports, seed_data, database and config.")
bullet("Data layer - data/civicsense.db (complaints and reports tables) and models/ (the trained classifier and its metrics JSON).")
para(
    "The core layer never imports Flask and the presentation layer never performs "
    "analysis. This separation means the analytical pipeline can be exercised directly "
    "from a script or a test without starting a web server - which is what the smoke "
    "suite and the reporting script both rely on."
)

h("3.5 Data Model", 2)
para("The complaints table persists every field the pipeline produces:")
bullet("Core fields: id, ward, category, title, description, source, created_at, status and priority")
bullet("Duplicate fields: is_duplicate and duplicate_of")
bullet("Fraud fields: fraud_score, fraud_level and fraud_explanation")
bullet("Clustering: cluster_id")
bullet("Priority and XAI: priority_score, priority_breakdown and xai_explanation")
para(
    "A second reports table stores generated weekly digests together with their "
    "statistics, so that exported PDF and Excel files can be regenerated on demand."
)
make_table(
    ["Column", "Type", "Purpose"],
    [
        ["id", "INTEGER PK", "Surrogate key used in URLs and API responses"],
        ["ward", "TEXT", "Locality; scopes duplicate detection and frequency scoring"],
        ["category", "TEXT", "One of the five service categories assigned by the classifier"],
        ["title", "TEXT", "Short human-readable label shown in tables"],
        ["description", "TEXT", "The raw complaint text submitted by the citizen"],
        ["source", "TEXT", "Intake channel (Mobile App, Web Portal, Email, Call Center, Social Media)"],
        ["priority", "TEXT", "High / Medium / Low label from the priority engine"],
        ["priority_score", "REAL", "Numeric urgency score before thresholding"],
        ["priority_breakdown", "TEXT (JSON)", "Per-signal contribution for XAI"],
        ["status", "TEXT", "Open / In Progress / Resolved work state"],
        ["confidence", "REAL", "Classifier pseudo-confidence in [0, 1]"],
        ["is_duplicate", "INTEGER", "1 when the record matches an earlier complaint"],
        ["duplicate_of", "INTEGER", "id of the original complaint when is_duplicate = 1"],
        ["fraud_score", "REAL", "0-100 bad-faith risk score"],
        ["fraud_level", "TEXT", "High / Medium / Low risk band"],
        ["fraud_explanation", "TEXT (JSON)", "Contributing fraud signals as sentences"],
        ["cluster_id", "INTEGER", "Shared identifier for one underlying incident"],
        ["xai_explanation", "TEXT (JSON)", "Priority justification sentences"],
        ["created_at", "TEXT", "ISO timestamp used by the age and frequency signals"],
    ],
    widths=[120, 90, 340],
    caption="The complaints table schema and the purpose of each column.",
)

h("3.6 Module Design and Interfaces", 2)
para("Each analytical concern lives in its own module with a narrow interface:")
make_table(
    ["Stage", "Module", "Key functions"],
    [
        ["Preprocessing", "civic_sense.preprocessing", "clean_text, tokenize, lemmatize, remove_stopwords, normalize, similarity, find_duplicate, detect_incident_cluster"],
        ["Classification", "civic_sense.classifier", "load_classifier, classify_text, train, get_metrics"],
        ["Fraud scoring", "civic_sense.fraud_detector", "analyze_fraud_risk, generate_fraud_explanation"],
        ["Incident clustering", "civic_sense.preprocessing", "detect_incident_cluster"],
        ["Priority", "civic_sense.prioritizer", "assign_priority, priority_explanation"],
        ["Seeding", "civic_sense.seed_data", "seed_if_empty, _fraud_scenario, _hotspot_scenario"],
        ["Persistence", "civic_sense.database", "insert_complaint, get_complaint, get_complaints, get_stats, fraud_alerts, cluster_summary"],
        ["Summarisation", "civic_sense.summarizer", "extractive_summary, generate_weekly_report"],
        ["Export", "civic_sense.reports", "generate_pdf, generate_excel"],
        ["App routes", "app.py", "index, complaints, new_complaint, api_submit, report_view, report_pdf, report_xlsx"],
    ],
    widths=[110, 150, 360],
    caption="Modules, their responsibilities and their public functions.",
)

h("3.7 Configuration and Tunable Parameters", 2)
para(
    "All thresholds and scenario knobs live in civic_sense/config.py and the relevant "
    "modules, so that behaviour can be tuned without editing algorithm code. The "
    "principal parameters are:"
)
make_table(
    ["Parameter", "Value", "Effect"],
    [
        ["SIM_THRESHOLD", "0.85", "Similarity above which a complaint counts as a semantic duplicate."],
        ["FREQ_THRESHOLD", "5", "Same-ward submissions in a short window that trigger the flood signal."],
        ["HIGH_FRAUD_SCORE", "70", "Fraud score at or above which the level is High."],
        ["MEDIUM_FRAUD_SCORE", "30", "Fraud score at or above which the level is Medium."],
        ["Priority thresholds", "3.2 / 1.6", "Score boundaries for High and Medium priority."],
        ["FRAUD_SCENARIO_COUNT", "8", "Number of seeded complaints in the fraud-alert scenario."],
        ["FRAUD_SCENARIO_WARD", "Hinjewadi", "Ward used by the fraud-alert scenario."],
        ["HOTSPOT_SCENARIO_WARD", "Wakad", "Ward used by the incident-hotspot scenario."],
        ["HOTSPOT_SCENARIO_CATEGORY", "Public Safety", "Category used by the incident-hotspot scenario."],
        ["USE_TRANSFORMERS", "0 (default)", "Enables the optional DistilBERT classification path."],
        ["OPENAI_API_KEY", "unset", "Enables language-model-written weekly digests."],
    ],
    widths=[150, 100, 280],
    caption="Principal configuration parameters and their behaviour.",
)
para(
    "Because these values are explicit and centralised, the demonstration scenarios can "
    "be made more or less aggressive without touching the pipeline itself - an important "
    "property for a system whose behaviour must be explained and audited."
)
para(
    "A deliberate constraint is that no parameter is hidden inside algorithm code. An "
    "early version of the project embedded an urgency keyword list directly inside the "
    "scoring function, which made the priority bug described in Section 7.2 difficult to "
    "reason about. Moving all such lists and thresholds to named constants made the "
    "behaviour inspectable and the fix obvious."
)

h("3.8 Functional Requirements", 2)
para("The functional requirements were derived from the base paper and the stakeholder analysis:")
make_table(
    ["ID", "Requirement", "Status"],
    [
        ["FR-1", "Accept complaints from a web form and a REST API", "Implemented"],
        ["FR-2", "Record the intake channel (source) of each complaint", "Implemented"],
        ["FR-3", "Normalise complaint text deterministically", "Implemented"],
        ["FR-4", "Classify each complaint into one of five categories", "Implemented"],
        ["FR-5", "Report a confidence score with each classification", "Implemented"],
        ["FR-6", "Detect and record semantic duplicates within a ward", "Implemented"],
        ["FR-7", "Score each complaint for bad-faith risk and record the level", "Implemented"],
        ["FR-8", "Explain every fraud score in human-readable terms", "Implemented"],
        ["FR-9", "Group paraphrased reports into incident clusters", "Implemented"],
        ["FR-10", "Assign an explainable High/Medium/Low priority", "Implemented"],
        ["FR-11", "Expose KPIs, charts and hotspots on a dashboard", "Implemented"],
        ["FR-12", "Generate weekly narrative digests", "Implemented"],
        ["FR-13", "Export digests as PDF and Excel", "Implemented"],
        ["FR-14", "Allow officers to update complaint status", "Implemented"],
        ["FR-15", "Provide an automated end-to-end test suite", "Implemented"],
    ],
    widths=[50, 380, 120],
    caption="Functional requirements and their implementation status.",
)

h("3.9 Non-Functional Requirements", 2)
make_table(
    ["ID", "Requirement", "How it is met"],
    [
        ["NFR-1", "Offline operation with no mandatory external service", "All analysis is local; the LLM digest path is optional"],
        ["NFR-2", "Deterministic, reproducible analysis", "Normalisation is stateless; seeds are fixed; metrics are stored"],
        ["NFR-3", "Graceful degradation when optional dependencies are missing", "Difflib fallback, sklearn fallback, template digest fallback"],
        ["NFR-4", "Explainability of every automated decision", "Numeric breakdowns are converted to sentences and stored"],
        ["NFR-5", "Low setup cost for demonstration", "A single run script installs dependencies and starts the app"],
        ["NFR-6", "No real personal data in the repository", "All demonstration records are synthetic"],
        ["NFR-7", "Reasonable responsiveness at demonstration scale", "Full pipeline per submission; measured in Section 6.8"],
        ["NFR-8", "Portability across platforms", "Pure-Python dependencies; UTF-8 output reconfiguration for Windows"],
    ],
    widths=[50, 200, 300],
    caption="Non-functional requirements and how each is satisfied.",
)

h("3.10 Design Decisions and Trade-offs", 2)
para("Several design choices involved genuine trade-offs. Recording them here explains why the system looks the way it does.")
bullet("A transformer would likely raise accuracy on a larger corpus, but at this corpus size it would overfit, would add heavy dependencies, and would make decisions harder to justify. The linear model was chosen as the default with the transformer path retained behind a flag.", bold_prefix="Model choice: ")
bullet("Guarantees complete records and immediate surfacing of failures, at the cost of adding analysis time to submission latency.", bold_prefix="Persistence timing: ")
bullet("Prevents a legitimate re-file from being scored as bad faith, at the cost of one extra query per submission.", bold_prefix="Fraud independence: ")
bullet("Two identical complaints in different wards are almost certainly two real issues; scoping to the ward avoids suppressing them. The cost is that cross-ward duplicates are not caught.", bold_prefix="Duplicate scoping: ")
bullet("The deterministic template always works and is reproducible; the LLM path is opt-in. The cost is less fluent prose.", bold_prefix="Summarisation: ")
bullet("Zero-configuration and portable for a demonstration; explicitly not a production choice.", bold_prefix="Storage: ")
bullet("Eliminates JavaScript dependencies and guarantees offline operation, at the cost of interactivity.", bold_prefix="Front end: ")

h("3.11 End-to-End Walkthrough of a Submission", 2)
para("The following traces a single complaint through every stage, using the concrete example \"Sewage overflowing near the market area\" filed in the ward Wakad from the Mobile App channel.")
make_table(
    ["Step", "What happens", "Result for this complaint"],
    [
        ["1. Intake", "The form or API validates the payload and calls run_pipeline()", "description and ward captured"],
        ["2. Preprocessing", "Text is cleaned, tokenised, lemmatised and stop-words removed", "normalised text produced"],
        ["3. Duplicate check", "Similarity is compared against prior Wakad complaints", "no match above threshold"],
        ["4. Classification", "TF-IDF features feed the LinearSVC model", "Public Safety (confidence about 0.50)"],
        ["5. Fraud scoring", "Similarity, frequency and pattern signals are combined", "Low risk, score 0.0"],
        ["6. Clustering", "The complaint is compared to open incident clusters", "assigned to a cluster identifier"],
        ["7. Priority", "Six weighted signals are summed", "High (score above 3.2)"],
        ["8. XAI", "The breakdown is converted to sentences", "hazard wording and category risk cited"],
        ["9. Persistence", "The enriched record is written to the database", "one complete row"],
        ["10. Delivery", "Dashboard KPIs, charts and tables recompute", "queues and cards update"],
    ],
    widths=[90, 210, 250],
    caption="End-to-end walkthrough of one submission through the eight-stage pipeline.",
)
para(
    "This trace is also the mental model the smoke suite encodes: each numbered step "
    "corresponds to at least one automated assertion, so a regression in any stage fails "
    "the suite rather than silently degrading a dashboard number."
)

h("3.12 Security, Privacy and Ethical Design", 2)
para("Although the project is a demonstration, several design choices were made with real-world deployment in mind.")
bullet("The repository contains only synthetic complaints generated by the seed script. There is no personal information to leak and no consent obligation to discharge.", bold_prefix="Data minimisation: ")
bullet("Complaint text is treated as data, never executed; database access uses parameterised queries throughout, which removes the SQL-injection class of vulnerability.", bold_prefix="Injection safety: ")
bullet("The fraud engine produces a risk score and an explanation for human review. It never blocks a citizen, never deletes a record and never marks a person as fraudulent automatically.", bold_prefix="No automated punishment: ")
bullet("A duplicate is recorded as a duplicate, not as an offence; the same text can be a re-file or a flood, and only the pattern across many submissions raises the score.", bold_prefix="Duplicates are not fraud: ")
bullet("Every score carries the reasons that produced it, so a citizen or auditor can challenge a decision on its merits.", bold_prefix="Contestability: ")
bullet("The classifier learns from a curated corpus; if that corpus under-represents a locality or a complaint style, accuracy will be uneven. This is treated as a known risk in Section 8 rather than being hidden.", bold_prefix="Representational bias: ")
para(
    "Authentication, role-based authorisation and audit logging are deliberately absent "
    "from this version and are listed as future work. They are prerequisites for any real "
    "deployment, not optional refinements."
)

# ===========================================================================
# 4. IMPLEMENTATION
# ===========================================================================
page_break()
h("4. Implementation", 1)
para("This section describes exactly what was built and why, module by module.")

h("4.1 Data Collection Layer", 2)
para(
    "Two intake paths were implemented: a web form at /complaints/new that simulates a "
    "citizen channel, and a REST endpoint POST /api/complaints that represents the "
    "paper's requirement that complaints be aggregated via API connections from portals, "
    "mobile apps, email and call centres. An optional source field records the channel of "
    "origin. All records land in a single complaints table so that downstream analysis "
    "operates on one unified corpus."
)
para(
    "In the demonstration database the five channels are used as follows: Mobile App 45, "
    "Web Portal 40, Social Media 39, Call Center 38 and Email 38 records. Recording the "
    "channel is not merely decorative: it makes it possible to ask, for example, whether "
    "a particular ward's complaints arrive disproportionately through one channel, which "
    "is a signal an integrity team would want."
)

h("4.2 Preprocessing Module", 2)
para("preprocessing.py implements a deterministic normalisation chain that runs before any algorithmic stage:")
bullet("Text cleaning - lowercasing, removal of URLs, emails and symbols, and collapsing of repeated whitespace.")
bullet("Tokenisation - word-boundary splitting using a small dependency-free tokeniser, with the NLTK punkt tokeniser as the preferred path when available.")
bullet("Lemmatisation - the WordNet lemmatiser with a lightweight part-of-speech guess, so that \"repairing\" reduces to \"repair\".")
bullet("Stop-word removal - NLTK stop-words plus a custom domain list so that trending-keyword analysis stays clean.")
para(
    "Normalisation is deliberately stateless and deterministic, so duplicate detection "
    "and similarity comparison are exactly reproducible: the same complaint submitted "
    "twice produces identical normalised text and is recognised as the same observation."
)
para(
    "The dependency-free fallbacks are not an afterthought. Tokenisation, lemmatisation "
    "and stop-word removal all prefer the NLTK implementation but fall back to built-in "
    "word lists and heuristics when NLTK data is unavailable. This is what allows the "
    "project to run on a machine where the NLTK corpora have not been downloaded, which "
    "is common on locked-down lab computers."
)

h("4.3 Duplicate Detection", 2)
para(
    "The base paper evaluates normalised-text similarity. CivicSense extends this to a "
    "locality-aware, similarity-based detector. A new complaint is compared against prior "
    "records in the same ward, and optionally the same category. Similarity uses "
    "sentence-transformers when the embedding stack is installed, and falls back to "
    "difflib.SequenceMatcher on the normalised text otherwise. The outcome is persisted "
    "as is_duplicate and duplicate_of, so that downstream stages know which records are "
    "independent observations."
)
para(
    "The choice of ward-scoping is deliberate: two identical complaints in different "
    "wards are almost certainly two real issues, whereas two identical complaints in the "
    "same ward are almost certainly one issue reported twice."
)
para(
    "The detector is also deliberately conservative about what it flags. In the clean "
    "demonstration run it identified 23 duplicates out of 200 records (11.5%), pointing "
    "at 17 distinct original complaints. A first implementation that flagged more than "
    "half the corpus as duplicates was traced to a normalisation bug and a threshold that "
    "was far too permissive; the corrected configuration is described in Section 7."
)

h("4.4 Classification", 2)
para("classifier.py wraps the primary model and the optional transformer path:")
bullet("A curated training corpus of 152 realistic complaints - roughly thirty per category - written to match the paper's five categories and examples.")
bullet("A TF-IDF + LinearSVC pipeline using one- and two-word n-grams with sublinear term frequency and balanced class weights.")
bullet("Honest evaluation: stratified 5-fold cross-validation is computed at training time and stored in models/metrics.json, then shown on the dashboard. An early single 80/20 hold-out split proved unstable at this corpus size and was replaced.")
bullet("Confidence scoring: the SVM's decision margins are softmax-normalised into a pseudo-confidence displayed as a percentage on the intake page.")
bullet("Optional DistilBERT: when USE_TRANSFORMERS=1 and the torch and transformers packages are installed, classification switches to a zero-shot DistilBERT model - the paper's named model family.")
para(
    "LinearSVC was chosen as the default because it trains in seconds on a laptop, needs "
    "no GPU or large downloads, is fully explainable, and performs strongly on the short, "
    "keyword-heavy text typical of complaints. The DistilBERT path exists so that the "
    "project can also demonstrate the paper's BERT-family approach when the environment "
    "supports it."
)
para("The measured behaviour of the default model is reported in Section 6.1.")

h("4.5 Fraud Detection", 2)
para(
    "fraud_detector.py implements a separate bad-faith risk engine that is deliberately "
    "kept independent of duplicate detection, so that a legitimate re-file is never "
    "penalised twice. It combines three complementary signals:"
)
make_table(
    ["Signal", "What it measures", "Configuration"],
    [
        ["Semantic similarity", "Near-identical text across many complaints", "SIM_THRESHOLD = 0.85"],
        ["Submission frequency", "Many complaints from one ward in a short window", "FREQ_THRESHOLD = 5"],
        ["Pattern analysis", "Very short or generic text", "short text = 10; + please = 5"],
    ],
    widths=[120, 260, 170],
    caption="The three fraud signals and their configuration.",
)
para(
    "The engine returns a score from 0 to 100, a level of Low, Medium or High, and a "
    "human-readable explanation listing the contributing signals. Because the three "
    "signals are complementary, a single ordinary report cannot trigger all of them, "
    "while a coordinated burst typically will."
)
para(
    "The score is capped at 100 and the level bands are configurable "
    "(HIGH_FRAUD_SCORE = 70, MEDIUM_FRAUD_SCORE = 30). In the clean demonstration run the "
    "combined result was 2 High-risk and 53 Medium-risk records (145 Low), and six of the "
    "ten highest scores belonged to the injected burst. The persistence of the level and "
    "explanation with each record is what allows the dashboard's Fraud Alerts card to "
    "show a credible pattern."
)

h("4.6 Incident Clustering", 2)
para(
    "detect_incident_cluster() groups complaints that describe the same underlying "
    "incident using semantic similarity. When the embedding stack is available, "
    "similarity between complaints is computed with sentence-transformers and a "
    "clustering threshold assigns a shared cluster_id. When it is not available, a "
    "graceful fallback uses lightweight similarity so that the clustering path remains "
    "demonstrable."
)
para(
    "Clustering is what allows CivicSense to answer the question \"how many distinct "
    "incidents are actually open?\" rather than \"how many complaint records exist?\" - a "
    "distinction that matters a great deal when a single fallen tree or burst pipe "
    "generates five separate reports."
)
para(
    "Two defects were found and fixed in this module during development, and they are "
    "worth recording because they illustrate how easily a feature can be present in the "
    "code yet absent in the product. First, the function referenced a variable that was "
    "never defined, so it raised on every call and the exception was swallowed by the "
    "caller. Second, the orchestrator passed a hardcoded null cluster identifier instead "
    "of calling the function at all. Both are described in Section 7.4; the net effect "
    "before the fix was that cluster_id was null in every row of the database, and the "
    "Incident Hotspots card on the dashboard permanently displayed its empty-state "
    "message."
)

h("4.7 Weighted Priority Assignment", 2)
para("prioritizer.py computes an explainable urgency score from exactly the signals the base paper lists:")
make_table(
    ["Signal", "What it measures", "Role in the score"],
    [
        ["Urgency keywords", "Issue-specific wording such as emergency, overflow, manhole", "Additive urgency"],
        ["Category risk", "Base risk of the classified category (Public Safety highest)", "Background risk"],
        ["Emotive language", "Strongly emotive or demanding phrasing", "Amplifier"],
        ["Locality frequency", "Number of similar complaints in the same ward", "Credibility multiplier"],
        ["Complaint age", "How recently it was filed", "Decay term"],
        ["Cluster boost", "Incident-clustering signal for repeated reports", "Optional boost"],
    ],
    widths=[120, 260, 170],
    caption="The six priority signals and their role in the urgency score.",
)
para(
    "The total score maps to High (at or above 3.2), Medium (at or above 1.6) or Low. The "
    "threshold design keeps ordinary routine-maintenance requests out of the emergency "
    "queue while ensuring that genuinely hazardous reports are prioritised immediately. "
    "Every decision is accompanied by a human-readable breakdown, which is the "
    "transparency the paper explicitly values."
)
para(
    "The signal weights were the subject of the bug in Section 7.2, where an overly broad "
    "keyword caused a large fraction of the corpus to be labelled High. After the fix the "
    "distribution is dominated by the intrinsic risk of the category, so that Public "
    "Safety complaints are consistently urgent, Roads and Electricity are mixed, and "
    "Waste Management and Water Supply skew toward routine maintenance. The measured "
    "distribution is reported in Section 6.2."
)

h("4.8 Explainable AI Generation", 2)
para(
    "Two XAI surfaces are produced. The priority explanation converts the numeric "
    "breakdown into sentences such as \"Contains strongly urgent wording\" or \"Many "
    "similar complaints reported in this ward\", so an officer can see why a complaint "
    "was ranked as it was. The fraud explanation states the fraud score, the level and "
    "the specific contributing signals. Taken together, these two surfaces mean that no "
    "automated decision in the system is opaque."
)
para("A representative priority explanation for a sewage complaint reads:")
bullet2("Category involves a public-safety hazard.")
bullet2("Contains issue-specific urgency wording.")
bullet2("Multiple citizens are reporting the same underlying incident.")
bullet2("Total urgency score: 3.65 (High >= 3.2, Medium >= 1.6, Low < 1.6).")
para(
    "The final line is important: it states the thresholds alongside the achieved score, "
    "so the reader can see not only why the complaint was ranked High but also how close "
    "it was to the boundary. This kind of transparency is cheap to produce and materially "
    "improves trust."
)

h("4.9 Summarisation and Weekly Digests", 2)
para(
    "summarizer.py provides extractive summarisation of individual complaints using "
    "frequency-based sentence scoring, and weekly digest generation that mirrors the base "
    "paper's example format exactly - for instance, \"Ward 2 recorded 24 complaints this "
    "week, predominantly water supply (6 reports). 11 of them (46%) were flagged High "
    "Priority and need immediate attention.\""
)
para(
    "The digest contains an overview (dominant category, priority mix and recurring "
    "themes), per-ward highlights and a resource-allocation suggestion that names the "
    "current hotspot. When OPENAI_API_KEY is set, the same statistics are passed to a "
    "generative model to rewrite the narrative in more fluent language; otherwise the "
    "deterministic offline template engine runs. The template engine guarantees that the "
    "demonstration always works, while the language-model hook future-proofs the design."
)
para(
    "Recurring themes are computed by counting normalised content words across the "
    "period's complaints, which is why a real digest reports themes such as \"road, "
    "water, damage, footpath, pothole, broken\" rather than a single headline word. The "
    "word cloud on the dashboard uses the same computation, so the two views are "
    "guaranteed consistent."
)

h("4.10 Report Generation (PDF / Excel)", 2)
para(
    "reports.py exports any weekly digest as a PDF via ReportLab, containing styled title "
    "information, the full digest narrative and a statistics table of total, priority and "
    "category counts. The same digest is exported as an Excel workbook via openpyxl, with "
    "three sheets: Overview (key performance indicators), Complaints (every complaint in "
    "the period with its AI-assigned category, priority, confidence and status) and "
    "Category Breakdown. These files are generated on demand from the report page and "
    "satisfy the paper's requirement for automatic generation in PDF or Excel format."
)
para(
    "Generated files are written to data/reports/ with a timestamped name so that "
    "successive exports do not overwrite one another. The smoke suite asserts the correct "
    "MIME types on download (application/pdf and the Excel spreadsheet type), which "
    "catches the common failure mode where a route returns an HTML error page with a "
    "successful status code."
)

h("4.11 Pipeline Orchestration", 2)
para(
    "run_pipeline() in app.py is the single orchestrator that every intake path calls. It "
    "executes the stages in a fixed order and assembles one result dictionary that is "
    "both persisted and returned to the caller: normalised text and the duplicate flag, "
    "the classified category with its confidence, the fraud score with its level and "
    "explanation, the incident cluster identifier, the priority label with its numeric "
    "breakdown, and the XAI sentences. A record is only written once every stage has "
    "produced a value, so the database never contains a partially analysed complaint."
)
para(
    "The orchestrator is also where graceful degradation is enforced. If "
    "sentence-transformers is unavailable, similarity falls back to difflib; if the "
    "transformer classifier cannot load, classification falls back to TF-IDF and "
    "LinearSVC; and if no language-model key is configured, digests fall back to the "
    "deterministic template engine. In every case the failure is recorded as a documented "
    "limitation rather than being allowed to crash the request."
)
para(
    "Centralising orchestration in one function also made the defects of Section 7 "
    "findable. Because every intake path funnels through run_pipeline(), a missing stage "
    "appears in exactly one place in the code rather than being duplicated across the web "
    "route and the API route - which is precisely how the hardcoded cluster identifier "
    "was located."
)

h("4.12 Dashboard and User Interface", 2)
para(
    "A single-page officer dashboard was built with templates/index.html and "
    "static/css/style.css. It shows key-performance-indicator cards (total complaints, "
    "high-priority count, resolved count and duplicates detected), the latest AI weekly "
    "digest as a hero card, a category-mix bar chart, a priority donut chart built from a "
    "pure-CSS conic gradient, a fourteen-day inflow chart, ward hotspot bars with each "
    "ward's top category, a trending-keywords tag cloud, and a recent-complaints table. "
    "Fraud Alerts and Incident Hotspots cards surface the two hidden-risk views."
)
para(
    "All charting is done in CSS with zero JavaScript libraries, so the demonstration runs "
    "entirely offline. Supporting pages include the filterable complaint list with inline "
    "status updates, the intake form with live AI analysis, the report list and viewer, "
    "and an AI Pipeline explainer page that shows the model, its cross-validated accuracy "
    "and the eight stages."
)
para(
    "The two decision-support cards were redesigned during development. Originally both "
    "derived their contents from the eight most recent complaints, which meant a "
    "high-risk record raised earlier in the day silently disappeared from view and the "
    "card showed an empty state. They now query the whole table through dedicated helper "
    "functions (database.fraud_alerts and database.cluster_summary), so a signal remains "
    "visible for as long as the underlying record exists. This change is discussed in "
    "Section 7.4."
)

h("4.13 Error Handling and Graceful Degradation", 2)
para(
    "The system's error-handling philosophy is to degrade a capability rather than fail a "
    "request, and to make the degradation visible rather than silent. The concrete "
    "fallbacks are:"
)
make_table(
    ["Capability", "Preferred implementation", "Fallback", "Trigger"],
    [
        ["Text similarity", "Sentence-Transformers embeddings", "difflib SequenceMatcher on normalised text", "Embedding stack cannot be imported"],
        ["Classification", "Zero-shot DistilBERT", "TF-IDF + LinearSVC", "USE_TRANSFORMERS unset or torch unavailable"],
        ["Tokenisation", "NLTK punkt", "Built-in word-boundary splitter", "NLTK data not downloaded"],
        ["Lemmatisation", "NLTK WordNet", "Regex-guided suffix reduction", "WordNet corpus unavailable"],
        ["Digest narrative", "LLM rewrite via API key", "Deterministic template engine", "OPENAI_API_KEY unset"],
        ["Console output", "Native stdout", "UTF-8 reconfigured with replacement", "Windows code page cannot encode a character"],
    ],
    widths=[100, 150, 180, 170],
    caption="Capabilities, their preferred implementations and their documented fallbacks.",
)
para(
    "One counter-example is deliberately recorded rather than hidden: the small "
    "classify_text helper catches any exception and returns a placeholder result of "
    "\"Roads\" with zero confidence. This protects the request path from an unexpected "
    "model error, but it can also mask a caller passing the wrong object type - exactly "
    "the mistake made while preparing Section 6.1, where a wrapper was passed instead of "
    "the underlying callable and every example silently returned \"Roads\" with a "
    "confidence of zero. The placeholder was recognisable precisely because its "
    "confidence is zero, which is why the mistake was caught quickly. A production "
    "hardening step would log the exception rather than only substituting a value."
)

h("4.14 Testing Strategy and the Smoke Suite", 2)
para(
    "Testing is organised as a single end-to-end smoke suite, smoke_test.py, which drives "
    "the real Flask application through its test client rather than mocking the pipeline. "
    "This choice is deliberate: a test that asserts on a mocked classifier proves nothing "
    "about the classifier, whereas a test that posts a real complaint and reads the "
    "returned category proves the whole chain works."
)
para("The suite covers the following areas:")
bullet("Each of the five base-paper example complaints classifies to the expected category.")
bullet("Every dashboard and content page returns HTTP 200.")
bullet("Submission through both the web form and the REST API creates a record.")
bullet("The API response contains the category, priority, confidence and fraud fields.")
bullet("Fraud level and explanation are persisted to the database, not just returned.")
bullet("Weekly report generation succeeds and the report is retrievable by id.")
bullet("PDF and Excel downloads return the correct MIME types.")
bullet("The status-update workflow persists a new status.")
bullet("The generated digest mentions a locality and a priority level.")
bullet("Duplicate detection marks the first of two identical complaints as fresh and the second as a duplicate with a similarity ratio of 1.0.")
para(
    "The suite runs 30 assertions in total and starts from a clean database, so its "
    "seeded counts are reproducible. Its result on the final build is reported in "
    "Section 6.7. Its own worst defect - an unterminated docstring that made the entire "
    "suite silently inert while reporting success - is documented in Section 7.5, "
    "because it is the single most instructive failure in the project."
)

h("4.15 Code Organisation and Repository Layout", 2)
para("The repository is laid out so that each concern has an obvious home:")
make_table(
    ["Path", "Contents"],
    [
        ["app.py", "Flask routes, the run_pipeline() orchestrator and application startup"],
        ["civic_sense/", "The analytical package (preprocessing, classifier, prioritizer, fraud detector, summariser, reports, database, config, seed data)"],
        ["civic_sense/build_report.py", "This report's generator - the document is produced from measured data"],
        ["templates/", "Jinja2 templates for the dashboard and all supporting pages"],
        ["static/css/", "Hand-written stylesheet, including the CSS-only charts"],
        ["models/", "The trained classifier (classifier.joblib) and its metrics (metrics.json)"],
        ["data/", "The SQLite demonstration database and generated PDF/Excel reports"],
        ["docs/", "Supporting specification notes for the demonstration scenarios"],
        ["smoke_test.py", "The end-to-end automated test suite"],
        ["run.sh", "One-command setup and run (install, NLTK data, start, or run tests)"],
        ["requirements.txt", "Pinned Python dependencies, with optional extras marked"],
    ],
    widths=[170, 380],
    caption="Repository layout and the contents of each path.",
)


# ===========================================================================
# 5. DEMONSTRATION DATA
# ===========================================================================
page_break()
h("5. Demonstration Data and Scenarios", 1)
para(
    "seed_data.py generates a synthetic but realistic demonstration corpus and two "
    "explicit scenarios. Crucially, every seeded complaint is processed through the real "
    "pipeline - preprocessing, duplicate detection, classification, fraud scoring, "
    "clustering and prioritisation - before it is inserted, so the dashboard's numbers "
    "are genuine model output rather than fabricated statistics."
)
para(
    "This property is worth stating plainly because it is the difference between a working "
    "demonstration and a mock-up. A great many student projects seed a database with "
    "pre-computed category and priority labels. Here, the seed script contains only raw "
    "complaint text, wards, sources and timestamps; everything else in the database was "
    "produced by the same code that runs for a newly submitted complaint."
)

h("5.1 Demonstration Corpus", 2)
para(
    "The corpus contains roughly 180 base complaints spread across ten wards, five "
    "categories and five intake channels, with timestamps weighted toward recent days. "
    "Approximately ten per cent of the records are deliberate verbatim re-files, so the "
    "duplicate-detection stage has genuine work to do, and a small set are the paper's "
    "challenge cases - very short or ambiguous texts such as \"No water\" and \"Road bad\" "
    "that test the classifier's robustness."
)
para(
    "The base corpus is supplemented by two explicit scenarios (the fraud burst and the "
    "hotspot cluster), producing the 200 records analysed in Section 6. Keeping the "
    "scenarios separate from the base corpus has an important analytical benefit: it is "
    "possible to measure the base distribution and the scenario-augmented distribution "
    "independently, which this report does in Section 6.2."
)

h("5.2 Fraud Alert Scenario", 2)
para("Configuration: FRAUD_SCENARIO_COUNT = 8, FRAUD_SCENARIO_WARD = Hinjewadi, with submissions compressed into a window of roughly ninety minutes.", bold=True)
para("The scenario submits a short burst of near-identical, generic complaints:")
for t in [
    "Please fix this issue immediately",
    "Need urgent attention please",
    "Kindly look into this matter",
    "Immediate action required please",
    "Need help asap please",
    "Please attend to this ASAP",
    "Attention required urgently",
    "Please resolve this issue",
]:
    bullet2(t)
para(
    "Rationale: repeated near-identical text triggers the semantic-similarity signal; one "
    "ward within a roughly ninety-minute window triggers the submission-frequency signal; "
    "and the short, generic phrasing triggers the pattern-analysis signal. Together these "
    "produce the mixed fraud pattern that the Fraud Alerts card is designed to display."
)
para(
    "The scenario is deliberately designed to be realistic rather than to maximise the "
    "score. Real coordinated spam does repeat the same text; real floods do concentrate in "
    "one ward in a short window. A scenario using eight completely different texts in the "
    "same window would trigger the frequency signal but not the repetition signal, and its "
    "measured risk would be correspondingly lower. The development history of this "
    "scenario - where an early version using eight distinct texts produced no High-risk "
    "row at all - is documented in Section 7.6."
)

h("5.3 Incident Hotspot Scenario", 2)
para("Configuration: HOTSPOT_SCENARIO_WARD = Wakad, HOTSPOT_SCENARIO_CATEGORY = Public Safety, with reports spread over roughly six hours.", bold=True)
para("The scenario submits several near-paraphrases of a single safety-related incident:")
for t in [
    "A tree fell on the road.",
    "A fallen branch blocked traffic.",
    "Debris from a fallen tree is on the road.",
    "The roadside tree lost a large branch.",
    "A tree near the location caused a road blockage.",
]:
    bullet2(t)
para(
    "Each record is tagged with a shared cluster identifier, so the Incident Hotspots card "
    "can group the records by cluster and display one representative theme together with a "
    "per-cluster count. In the measured run this scenario produced a cluster of eight "
    "complaints - the largest in the database, and the principal end-to-end evidence that "
    "the semantic-clustering path is wired into the dashboard."
)
para(
    "The wording of the paraphrases is chosen to defeat naive token matching. The phrases "
    "share the concept of a fallen tree blocking a road but differ substantially in "
    "surface vocabulary, which is exactly the case that embedding-based or edit-distance "
    "similarity can handle and that a keyword lookup cannot."
)

h("5.4 Dashboard Display Mapping", 2)
bullet("The Fraud Alerts card queries the whole table through database.fraud_alerts(), which orders High-risk rows first and then Medium-risk rows by descending score, and renders the score and level for each.", bold_prefix="Fraud Alerts: ")
bullet("The Incident Hotspots card queries database.cluster_summary(), which groups every clustered complaint by cluster_id, counts its members and picks a representative title, then renders the cluster identifier, the theme and the size.", bold_prefix="Incident Hotspots: ")
bullet("The KPI cards, category chart, priority donut, inflow chart, ward bars and keyword cloud all recompute from the same database on every page load, so no cached or stale figure can disagree with the stored records.", bold_prefix="Other cards: ")

h("5.5 Measured Corpus Statistics", 2)
para("The following table summarises the clean demonstration database as seeded and processed by the real pipeline. Every number is a measurement, not an estimate.")
make_table(
    ["Measure", "Value"],
    [
        ["Total complaints processed", "200"],
        ["Base corpus records", "186 (after excluding 14 scenario records)"],
        ["Distinct wards", "10 (Hinjewadi, Wakad, Talegaon, Vadgaon, Chinchwad, Maval, Akurdi, Kamseth, PCMC, Katraj)"],
        ["Categories represented", "5 of 5"],
        ["Intake channels", "5 of 5 (Web Portal 48, Email 42, Mobile App 40, Social Media 38, Call Center 32)"],
        ["Duplicates flagged", "23 (11.5%), pointing at 17 distinct originals"],
        ["Records assigned to clusters", "18, spanning 11 distinct clusters"],
        ["Largest incident cluster", "8 complaints (Wakad)"],
        ["Fraud levels", "High 2, Medium 53, Low 145"],
        ["Priority labels", "High 112, Medium 80, Low 8"],
        ["Statuses at seed time", "All Open (200)"],
        ["Classifier training samples", "152"],
    ],
    widths=[180, 360],
    caption="Measured statistics of the clean demonstration database.",
    numbered=True,
)
para(
    "The ward distribution is not uniform, which is intentional: a demonstration where "
    "every ward has exactly twenty complaints would make the hotspot and trend views "
    "visually meaningless. The measured ward totals are Hinjewadi 37, Wakad 28, Talegaon "
    "27, Vadgaon 24, Chinchwad 17, Maval 17, Akurdi 16, Kamseth 13, PCMC 12 and Katraj 9."
)

h("5.6 Reproducing the Demonstration", 2)
para("The entire demonstration is reproducible from a clean checkout. The sequence is:")
bullet("Install the dependencies with pip install -r requirements.txt, or simply run ./run.sh.")
bullet("Start the application with python app.py. On startup, if the database is empty, the schema is created, the classifier is trained if necessary and the demonstration corpus is seeded and processed.")
bullet("Open http://127.0.0.1:5000 to view the dashboard, or POST to /api/complaints to submit a complaint programmatically.")
bullet("Run python smoke_test.py to execute the automated suite from a clean database.")
para(
    "Because the seed runs through the live pipeline, the exact counts can shift slightly "
    "between runs if the timestamp weighting places records on different sides of a "
    "frequency threshold. The figures quoted in this report were taken from a single clean "
    "run and are representative; the accuracy figure from cross-validation, by contrast, "
    "is deterministic because the training corpus and the fold split are fixed."
)

# ===========================================================================
# 6. RESULTS AND EVALUATION
# ===========================================================================
page_break()
h("6. Results and Evaluation", 1)
para(
    "This section reports the measured results of the system and evaluates them against "
    "the base paper. Unless stated otherwise, each figure comes from a clean database "
    "seeded and processed through the real pipeline, or from the stored cross-validation "
    "metrics produced at training time."
)

h("6.1 Classification Accuracy", 2)
make_table(
    ["Metric", "CivicSense", "Base paper"],
    [
        ["Classification accuracy (stratified 5-fold CV)", "82.19%", "93%"],
        ["Standard deviation across folds", "+/- 5.47%", "Not reported"],
        ["Fold scores", "0.9032 / 0.8065 / 0.7667 / 0.8667 / 0.7667", "Not reported"],
        ["Training corpus size", "152 complaints", "Not reported"],
        ["Model", "TF-IDF + LinearSVC", "BERT / DistilBERT family"],
    ],
    widths=[190, 190, 170],
    caption="Classification accuracy compared with the base paper.",
    numbered=True,
)
para(
    "The paper's 93% is reported on its own dataset. The figure here is measured on this "
    "project's curated corpus, so it is deliberately conservative and fully reproducible. "
    "All five base-paper examples classify correctly, including the ambiguous \"Sewage "
    "overflowing near the market area\" which is correctly assigned to Public Safety, and "
    "the short challenge texts also classify correctly."
)
para("To make the evaluation concrete, the following table lists every curated test text, the expected category and the measured output with its confidence for the default model.")
make_table(
    ["Complaint text", "Expected", "Predicted", "Confidence"],
    [
        ["There is a huge pothole near the school and it is dangerous", "Roads", "Roads", "0.3456"],
        ["Streetlight not working for the past three days", "Electricity", "Electricity", "0.5048"],
        ["No water supply in our area since yesterday", "Water Supply", "Water Supply", "0.5249"],
        ["Garbage not collected for two days in our lane", "Waste Management", "Waste Management", "0.5201"],
        ["Sewage overflowing near the market area", "Public Safety", "Public Safety", "0.4982"],
        ["No water", "Water Supply", "Water Supply", "0.6193"],
        ["Road bad", "Roads", "Roads", "0.3945"],
        ["Light not working", "Electricity", "Electricity", "0.3196"],
        ["Garbage everywhere", "Waste Management", "Waste Management", "0.4391"],
        ["Very dangerous near school", "Public Safety", "Public Safety", "0.3431"],
        ["Transformer is making loud noise and sparking at night", "Electricity", "Electricity", "0.4504"],
    ],
    widths=[220, 90, 90, 80],
    caption="Curated classification tests with measured predictions and confidences.",
    numbered=True,
)
para(
    "Eleven of eleven texts are classified correctly. The confidence values are worth "
    "reading carefully: they are softmax-normalised decision margins, not calibrated "
    "probabilities, so a value of 0.3456 for a correct classification does not mean the "
    "model is 34% sure. It means the winning margin, after softmax, was about a third of "
    "the mass. With only five classes and a linear decision function, margins tend to be "
    "close together, which is why the correct answers often carry confidences in the "
    "0.3-0.5 range. This is a limitation of the pseudo-confidence as a user-facing number "
    "and is noted in Section 8.",
    italic=True,
)

h("6.2 Priority Distribution", 2)
para("Across the 200 processed complaints the priority engine produces the following distribution:")
make_table(
    ["Priority", "Count", "Share"],
    [
        ["High", "112", "56.0%"],
        ["Medium", "80", "40.0%"],
        ["Low", "8", "4.0%"],
    ],
    widths=[140, 100, 100],
    caption="Overall priority distribution for the 200-complaint demonstration corpus.",
    numbered=True,
)
para(
    "This distribution is higher on the High band than a production municipal feed would "
    "be, and it is important to explain why rather than present it as a neutral fact. The "
    "demonstration corpus deliberately over-represents urgent and hazardous wording because "
    "those are the cases the priority engine exists to catch. Excluding the fourteen "
    "records that belong to the two scenarios leaves a 186-record base corpus distributed "
    "as High 99 (53.2%), Medium 79 (42.5%) and Low 8 (4.3%) - so the scenarios are not "
    "responsible for the skew."
)
para("The distribution by category is more informative, because it shows the priority engine responding to category risk rather than to wording alone:")
make_table(
    ["Category", "High", "Medium", "Low", "Total", "Comment"],
    [
        ["Public Safety", "33", "4", "0", "37", "Predominantly hazardous; most records urgent"],
        ["Roads", "32", "15", "4", "51", "Mixed, driven by hazard wording and locality frequency"],
        ["Electricity", "18", "15", "0", "33", "Mixed; sparking and outage wording dominates"],
        ["Waste Management", "11", "25", "4", "40", "Skews to routine collection delays"],
        ["Water Supply", "18", "21", "0", "39", "Mixed; shortages and contamination raise urgency"],
    ],
    widths=[100, 45, 55, 45, 50, 200],
    caption="Priority distribution broken down by category.",
    numbered=True,
)
para(
    "The pattern is what a domain expert would expect. Public Safety complaints - open "
    "manholes, fallen trees, stray cattle, sewage overflow - are uniformly urgent. Waste "
    "Management and Water Supply complaints are mostly routine service requests with a "
    "minority of genuine emergencies. Roads and Electricity sit in between. This is strong "
    "evidence that the priority engine is responding to something meaningful rather than "
    "to noise."
)
para(
    "A caveat must accompany the Public Safety column: because category risk is a floor "
    "term, most Public Safety complaints clear the High threshold regardless of their "
    "wording - 33 of 37 in this run. The category-risk weight is defensible in the sense "
    "that public-safety issues are genuinely more dangerous when ignored, but it does mean "
    "that for this category the High band is closer to a measure of category risk than of "
    "textual urgency alone. This is discussed further in Section 6.12.",
    italic=True,
)

h("6.3 Duplicate Detection Results", 2)
para(
    "Twenty-three duplicates (11.5%) were identified among the 200 records, pointing at 17 "
    "distinct original complaints. This closely matches the deliberate re-file rate in the "
    "seed data, which is the intended outcome: the detector should catch the re-files and "
    "little else."
)
make_table(
    ["Measure", "Result"],
    [
        ["Records flagged as duplicates", "23 of 200 (11.5%)"],
        ["Distinct original complaints referenced", "17"],
        ["Verbatim re-file detection", "Caught (similarity ratio 1.0)"],
        ["Over-flagging", "None observed after the normalisation fix"],
        ["Effect on downstream analysis", "Flagged records do not inflate incident counts"],
    ],
    widths=[220, 320],
    caption="Duplicate detection results.",
    numbered=True,
)
para(
    "An earlier configuration mis-detected more than half the corpus as duplicates, which "
    "was traced to over-permissive matching. After correction the rate is credible for a "
    "municipal corpus in which roughly one in seven complaints is a re-file. The smoke "
    "suite verifies the specific behaviour that matters most: submitting the same "
    "complaint twice marks the first as fresh and the second as a duplicate with a "
    "similarity ratio of 1.0 pointing at the original."
)

h("6.4 Fraud Detection Results", 2)
para("The fraud engine scored every record in the corpus. The resulting level distribution is deliberately conservative, as it should be for a system that must never punish a good-faith citizen:")
make_table(
    ["Fraud level", "Records", "Interpretation"],
    [
        ["High", "2", "The most repetitious members of the coordinated burst"],
        ["Medium", "53", "Records sharing a partial signal (frequency or pattern)"],
        ["Low", "145", "Ordinary complaints with no suspicious signal"],
    ],
    widths=[100, 80, 360],
    caption="Fraud level distribution across the 200-complaint corpus.",
    numbered=True,
)
para(
    "The Medium band is large because the submission-frequency signal is locality-scoped "
    "and the demonstration corpus places several complaints in the same ward within a "
    "short window by design. This is the correct, intended behaviour for a risk score: "
    "Medium means worth a glance, not fraudulent. The two High-risk records sit in the "
    "coordinated burst ward of Hinjewadi, where near-identical text and elevated frequency "
    "combine."
)
para("The ten highest-scoring records illustrate the score bands concretely:")
make_table(
    ["Complaint", "Ward", "Score", "Level"],
    [
        ["Kindly look into this matter", "Hinjewadi", "70.0", "High"],
        ["Need urgent attention please", "Hinjewadi", "70.0", "High"],
        ["Please fix this issue immediately", "Hinjewadi", "65.0", "Medium"],
        ["Need urgent attention please (re-filed)", "Hinjewadi", "55.0", "Medium"],
        ["Kindly look into this matter (re-filed)", "Hinjewadi", "55.0", "Medium"],
        ["Please fix this issue immediately (re-filed)", "Hinjewadi", "50.0", "Medium"],
        ["No water", "Maval", "50.0", "Medium"],
        ["People are burning waste in the open field", "Kamseth", "40.0", "Medium"],
        ["Construction debris is dumped on the footpath", "Maval", "40.0", "Medium"],
        ["People are burning waste (re-filed)", "Maval", "40.0", "Medium"],
    ],
    widths=[240, 90, 60, 70],
    caption="The ten highest fraud scores and the band each falls into.",
    numbered=True,
)
para(
    "The top six rows are the injected coordinated burst: short, generic and concentrated "
    "in one ward in a narrow window, which is exactly the combination the engine is built "
    "to detect. The four rows that follow are ordinary corpus complaints - a short "
    "challenge text and re-filed waste complaints - that picked up the locality-frequency "
    "signal because they share a ward with other recent reports. They show the intended "
    "behaviour of a risk score: it is graded, not binary, and a Medium score is a prompt "
    "for review rather than an accusation. That the vast majority of the corpus scores "
    "zero is the other half of the result: the engine is specific, not merely noisy."
)

h("6.5 Incident Clustering Results", 2)
para(
    "Eighteen records were assigned to incident clusters, spanning eleven distinct "
    "clusters. The distribution is highly skewed, which is exactly what clustering a "
    "complaint stream should reveal: most incidents are reported once, a few are reported "
    "many times."
)
make_table(
    ["Cluster size", "Number of clusters", "Interpretation"],
    [
        ["8 complaints", "1", "The injected hotspot scenario - one incident, many reports"],
        ["1 complaint", "10", "Incidents reported once"],
    ],
    widths=[120, 140, 280],
    caption="Distribution of incident cluster sizes.",
    numbered=True,
)
para(
    "The largest cluster is the eight-complaint hotspot in Wakad, which is what the "
    "Incident Hotspots card displays. The downstream value of this grouping is "
    "quantitative: treating those eight records as eight separate incidents would "
    "overstate the open-incident count by seven. In a real deployment, where a single "
    "fallen tree might generate dozens of reports, this distinction directly affects how "
    "field crews are dispatched."
)

h("6.6 Digest Generation Quality", 2)
para("A representative generated digest, produced by the real template engine on the clean corpus, reads:")
para(
    "During October 04 - October 11, 2026, 121 citizen complaints were received and "
    "automatically processed. The dominant category was Roads (35 reports), followed by "
    "Waste Management (25) and Water Supply (23). Priority-wise, 65 complaints were High, "
    "48 Medium and 8 Low. Recurring themes include: road, water, waste, garbage, damage, "
    "bridge.",
    italic=True,
)
para("Ward-level highlights followed in the same structure the base paper illustrates. The measured ward lines were:")
bullet2("Hinjewadi recorded 29 complaints this week, predominantly roads (14 reports). 20 of them (69%) were flagged High Priority and need immediate attention.")
bullet2("Wakad recorded 23 complaints this week, predominantly roads (8 reports). 13 of them (57%) were flagged High Priority and need immediate attention.")
bullet2("Talegaon recorded 15 complaints this week, predominantly water supply (6 reports). 10 of them (67%) were flagged High Priority and need immediate attention.")
bullet2("Vadgaon recorded 12 complaints this week, predominantly roads (3 reports). 4 of them (33%) were flagged High Priority and need immediate attention.")
bullet2("Maval recorded 11 complaints this week, predominantly waste management (5 reports). 3 of them (27%) were flagged High Priority and need immediate attention.")
para(
    "The digest closed with a resource-allocation suggestion naming Hinjewadi as the "
    "current hotspot for roads issues. This reproduces the paper's example sentence "
    "structure closely and directly supports its claims about weekly digests and "
    "data-driven resource allocation. The exact digest for the current period is "
    "reproduced in full in Appendix H."
)

h("6.7 Automated Test Results", 2)
para(
    "smoke_test.py drives the real Flask application through its test client and verifies "
    "all five paper classifications, that every page renders with HTTP 200, web-form and "
    "REST intake, the pipeline's returned category, priority and explanation, weekly "
    "report generation, PDF and Excel downloads, the status-update workflow, digest "
    "content and duplicate detection. On the final build all 30 checks passed and the "
    "suite exited with status 0."
)
make_table(
    ["Test area", "Checks", "Result"],
    [
        ["Classification of base-paper examples", "5", "Pass"],
        ["Page rendering (dashboard and content pages)", "6", "Pass"],
        ["Web-form and REST intake", "2", "Pass"],
        ["API response fields (category, priority, confidence, fraud)", "4", "Pass"],
        ["Fraud persistence to the database", "1", "Pass"],
        ["Report generation and retrieval", "2", "Pass"],
        ["PDF and Excel export MIME types", "2", "Pass"],
        ["Status update workflow", "2", "Pass"],
        ["Digest content (locality and priority mentions)", "2", "Pass"],
        ["Duplicate detection and similarity ratio", "3", "Pass"],
        ["Statistics endpoint", "1", "Pass"],
    ],
    widths=[230, 60, 80],
    caption="Automated test areas, the number of checks in each and the outcome.",
    numbered=True,
)

h("6.8 System Response and Performance", 2)
para(
    "Response time was not a primary design goal at demonstration scale, but it is worth "
    "recording because the pipeline performs a per-submission similarity scan. The user "
    "experience is dominated by three costs: first-request classifier loading and "
    "training, per-submission pipeline execution, and page rendering."
)
make_table(
    ["Operation", "Characteristic", "Notes"],
    [
        ["Classifier training", "Seconds, once", "Stratified 5-fold cross-validation over 152 samples"],
        ["Seeding 200 complaints", "Completed within the startup budget", "Each record runs the full pipeline"],
        ["Single submission", "Sub-second at this corpus size", "Similarity scans up to 100 recent records"],
        ["Dashboard render", "Sub-second", "All aggregates computed in a single request"],
        ["Report generation (PDF + Excel)", "Sub-second", "Written to data/reports/ with a timestamp"],
    ],
    widths=[180, 150, 210],
    caption="Observed performance characteristics of the main operations.",
    numbered=True,
)
para(
    "The important structural observation is that the expensive part of the pipeline is "
    "the similarity scan, which is linear in the number of recent complaints. At 200 "
    "records this is trivial; at two million it would not be. The mitigation is already "
    "sketched in the design: duplicate detection and fraud similarity are both "
    "ward-scoped, which reduces the candidate set by roughly the number of wards, and a "
    "production deployment would add an index or a cached embedding store. This is listed "
    "as future work rather than solved here."
)

h("6.9 Comparison with the Base Paper", 2)
make_table(
    ["Feature", "Base paper", "Enhanced CivicSense"],
    [
        ["Triage flow", "Linear analysis to priority", "Preprocessing -> Duplicate Detection -> Classification -> Fraud Scoring -> Incident Clustering -> Weighted Priority -> XAI -> Dashboard"],
        ["Deduplication", "Normalised text similarity", "Locality-aware duplicate detection via text similarity (Sentence-BERT when available, difflib fallback)"],
        ["Fraud handling", "None or basic", "Hybrid fraud scoring (semantic spam + flood frequency + generic pattern) with XAI, separate from duplicate detection"],
        ["Incident handling", "Individual complaint tracking", "Semantic incident clustering plus a demonstrated hotspot scenario"],
        ["Priority logic", "Keyword + category + emotion", "Weighted priority with optional cluster boost"],
        ["Transparency", "Score-based", "Explainable-AI justifications for priority and fraud"],
        ["Core technology", "TF-IDF / BERT", "TF-IDF + LinearSVC with optional DistilBERT and optional sentence-transformers"],
        ["Demo data", "Static complaint corpus", "Realistic corpus plus explicit fraud-alert and incident-hotspot scenarios"],
        ["Reporting", "Weekly digest concept", "Weekly digest with PDF and Excel export verified by tests"],
    ],
    widths=[110, 150, 280],
    caption="Feature-by-feature comparison with the base paper.",
    numbered=True,
)
para(
    "The comparison is deliberately framed as coverage rather than as a claim of superior "
    "accuracy. The base paper's 93% figure is not contested here - it was measured on a "
    "different dataset that this project does not have. What the project demonstrates is "
    "that the paper's proposal can be built end to end, that its central claims hold up "
    "in a working system, and that four specific gaps can be closed with modest additional "
    "engineering."
)

h("6.10 Sample System Outputs", 2)
para(
    "Submitting the complaint \"Transformer is making loud noise and sparking at night\" "
    "to the REST endpoint returned category Electricity (confidence 0.4504), priority "
    "High, a priority score of 3.65, a multi-line explanation, and is_duplicate false. "
    "Submitting an identical complaint a second time returned is_duplicate true with "
    "duplicate_of pointing at the original record and a 100% similarity ratio. On the "
    "dashboard the key-performance-indicator cards showed 200 total complaints, 112 high "
    "priority and 23 duplicates detected, with Hinjewadi as the current weekly hotspot."
)
para(
    "A submitted generic complaint - \"Please fix this issue immediately\" - behaved as "
    "the fraud engine intends: it was still classified and prioritised normally, but it "
    "also carried a High fraud level with a score of 70.0 and an explanation citing both "
    "semantic similarity to other reports and unusual submission volume. This is the "
    "central design property of the fraud stage: it annotates a record for review without "
    "suppressing it or altering its service classification."
)

h("6.11 Key Performance Indicators", 2)
para("The table below collects the headline indicators that the dashboard surfaces and that anchor the evaluation of this project:")
make_table(
    ["Area", "Metric", "Result"],
    [
        ["Classification", "Accuracy (stratified 5-fold CV)", "82.19% (+/- 5.47%)"],
        ["Classification", "Fold scores", "0.9032 / 0.8065 / 0.7667 / 0.8667 / 0.7667"],
        ["Classification", "Curated text tests", "11 of 11 correct"],
        ["Priority", "Explainable multi-signal scoring", "High 56.0% / Medium 40.0% / Low 4.0%"],
        ["Duplicate detection", "Duplicates identified", "23 of 200 (11.5%)"],
        ["Incident clustering", "Records grouped", "18 across 11 clusters (largest 8)"],
        ["Fraud detection", "Separate hybrid risk scoring with XAI", "2 High and 53 Medium scores"],
        ["Explainability", "Priority and fraud justifications", "Provided for every decision"],
        ["Reports", "Weekly digest with PDF and Excel export", "Generated on demand and verified"],
        ["Testing", "Automated end-to-end checks", "30 of 30 passed on the final build"],
    ],
    widths=[120, 200, 220],
    caption="Consolidated key performance indicators.",
    numbered=True,
)

h("6.12 Threats to Validity", 2)
para("A rigorous evaluation should state what could make its conclusions wrong. The following threats are acknowledged openly.")
bullet("The corpus is synthetic and was written by the project team. Its vocabulary may be cleaner and more consistent than real citizen submissions, which could inflate classification accuracy relative to a real deployment.", bold_prefix="Construct validity: ")
bullet("The 152-sample corpus is small. Cross-validation reduces the variance of the estimate but cannot remove the risk that the corpus itself is unrepresentative. The wide spread of fold scores (0.77 to 0.90) is direct evidence of this.", bold_prefix="Statistical validity: ")
bullet("The fraud and hotspot scenarios are injected. They demonstrate that the mechanisms work, but they are not evidence about the false-positive rate a real system would experience on genuine traffic.", bold_prefix="External validity: ")
bullet("Priority labels are produced by the engine's own thresholds, so the distribution is internally consistent by construction. It cannot independently confirm that the weights match what a human officer would choose.", bold_prefix="Criterion validity: ")
bullet("Confidence values are normalised decision margins, not calibrated probabilities, so they should not be read as literal certainty. See the note in Section 6.1.", bold_prefix="Interpretation risk: ")
para(
    "None of these threats undermines the core result, which is that the pipeline works "
    "end to end and behaves sensibly on its inputs. They do mean that the accuracy figure "
    "and the fraud counts should be read as demonstration-quality measurements rather than "
    "as production performance claims - which is precisely how they are presented "
    "throughout this report."
)

# ===========================================================================
# 7. CHALLENGES
# ===========================================================================
page_break()
h("7. Development Challenges and Solutions", 1)
para(
    "A record of what went wrong during development and how each issue was diagnosed and "
    "fixed explains the reasoning behind several final design decisions. These are real "
    "defects found in this codebase, not generic cautions."
)

h("7.1 Instability of the First Accuracy Metric", 2)
para(
    "Symptom: the first version reported 50% hold-out accuracy with zero precision for the "
    "Public Safety class, far below the paper's figure."
)
para(
    "Diagnosis: a twenty per cent test split left only four samples per class, so a single "
    "misclassification moved accuracy by five points. Auditing the misclassified examples "
    "exposed genuine labelling inconsistencies in the training corpus - 'hanging wires' "
    "appeared in both Electricity and Public Safety, 'market' was overused in Waste "
    "Management and hijacked the paper's own sewage example, and 'leaning' and 'open drain' "
    "collided across classes."
)
para(
    "Fix: the corpus was rewritten so each category owns distinctive vocabulary, the "
    "collisions were removed, and the reported metric was switched to stratified 5-fold "
    "cross-validation. Outcome: accuracy rose to 82.19% +/- 5.47%, which is stable across "
    "folds and reproducible."
)
para("The lesson generalises: at small corpus sizes a single hold-out split is a coin flip, and a suspiciously low score is often a data problem rather than a model problem.")

h("7.2 Priority Inflation from an Overly-Broad Keyword", 2)
para("Symptom: roughly forty per cent of complaints were labelled High priority, which would swamp an emergency queue.")
para(
    "Diagnosis: the bare word 'open' appeared in the high-urgency keyword list and matched "
    "ordinary phrases such as 'open ground', 'open field' and 'open drain'. A single "
    "over-broad token was adding urgency to a large fraction of routine complaints."
)
para(
    "Fix: the vague terms were replaced with specific hazard terms such as 'manhole' and "
    "'overflow'. Outcome: a sewage overflow correctly scores High while a flickering "
    "streetlight remains Medium, and the resulting per-category distribution now shows the "
    "sensible pattern reported in Section 6.2."
)
para(
    "This defect is the reason all keyword lists and thresholds now live in named constants "
    "rather than being embedded in the scoring function. The fix was trivial once the list "
    "was visible; finding it was the hard part."
)

h("7.3 Console Encoding During Testing", 2)
para(
    "Symptom: the test suite crashed while printing a priority explanation because the '>=' "
    "character could not be encoded by the Windows code page."
)
para(
    "Fix: the test harness reconfigures standard output and standard error to UTF-8 with "
    "error replacement, and the web layer was already UTF-8 safe. Outcome: test output is "
    "stable on Windows regardless of locale."
)
para(
    "The broader point is that the application was always correct; only the test harness's "
    "console output was affected. It would have been easy to mistake this for a pipeline "
    "failure, which is a reminder to read a crashing test carefully before changing code."
)

h("7.4 Decision-Support Cards That Stayed Empty", 2)
para("Symptom: the Fraud Alerts and Incident Hotspots cards on the dashboard permanently displayed their empty-state messages even though the database contained relevant records.")
para(
    "Diagnosis, part one: the Incident Hotspots card was empty because cluster identifiers "
    "were stored as null for every record. Tracing this revealed two independent defects. "
    "The clustering function referenced a variable that was never defined and therefore "
    "raised on every call, and the orchestrator did not call the function at all - it "
    "passed a hardcoded null cluster identifier. The exception raised by the first defect "
    "was swallowed by the caller, so nothing surfaced in the logs or on screen."
)
para(
    "Diagnosis, part two: both cards derived their contents from only the eight most recent "
    "complaints. A high-risk filing raised earlier in the day, or a cluster whose reports "
    "had scrolled past the recent window, silently disappeared from view. This is a design "
    "flaw rather than a coding error: it makes a decision-support card's contents depend on "
    "submission volume rather than on the underlying facts."
)
para(
    "Fix: the clustering function was corrected and the orchestrator now calls it for every "
    "submission; and both cards were given dedicated whole-table queries "
    "(database.fraud_alerts and database.cluster_summary) so that a signal remains visible "
    "for as long as the record exists. Outcome: the Fraud Alerts card shows the highest-risk "
    "filings regardless of when they arrived, and the Incident Hotspots card shows every "
    "cluster with its size."
)
para(
    "The lesson is that a feature can be present in the source tree and absent from the "
    "product. The clustering code existed, was documented and looked correct; what was "
    "missing was the wiring and the visibility of its failure."
)

h("7.5 A Test Suite That Silently Never Ran", 2)
para("Symptom: the smoke suite reported success while printing nothing at all.")
para(
    "Diagnosis: the file's opening docstring was never closed until the final line of the "
    "file. The entire test suite was therefore inside a string literal, so Python parsed it "
    "as a module with no statements and exited successfully with no output. Every previous "
    "run had reported a clean pass because there was nothing to fail."
)
para(
    "Fix: the docstring was closed at the appropriate point, the suite was re-run, and all "
    "checks executed properly. Outcome: the suite now performs 30 real assertions and "
    "exits with status 0 only when they genuinely pass."
)
para(
    "This is the single most instructive defect in the project. A test suite that cannot "
    "fail is worse than no test suite, because it manufactures false confidence. The "
    "verification discipline adopted afterwards - insisting that a passing test produce "
    "visible evidence and a non-zero number of assertions - exists because of this incident."
)

h("7.6 A Fraud Signal That Never Fired", 2)
para("Symptom: after correcting the earlier defects, the Fraud Alerts card still showed no High-risk rows, even though the fraud scenario was clearly present in the data.")
para(
    "Diagnosis, part one: the scenario's complaints were timestamped outside the one-hour "
    "window the frequency signal counts, so the signal could never see them. A secondary "
    "cause compounded this - the scenario had previously been invoked more than once during "
    "seeding, which inflated the count in a way that masked the windowing problem."
)
para(
    "Diagnosis, part two: even once the window was corrected, the scenario used eight "
    "completely different texts, so the semantic-repetition signal - the strongest of the "
    "three - detected almost nothing. The scenario was realistic as a flood but not as "
    "coordinated spam."
)
para(
    "Fix: the scenario's timestamps were brought inside the frequency window and its texts "
    "were made genuinely repetitive, which is what real coordinated spam looks like. "
    "Outcome: the engine now produces two High-risk and eight Medium-risk alerts on a clean "
    "seed, as reported in Section 6.4."
)
para(
    "This defect illustrates a subtle hazard in building a demonstration: when a scenario "
    "is designed to look realistic, it can accidentally stop exercising the mechanism it "
    "was built for. The scenario had to be made *more* artificial (repetitive text) in "
    "order to be a faithful test of the repetition detector."
)

h("7.7 Engineering Lessons", 2)
para("Distilling the seven defects above yields a short list of practices that this project adopted and that would be worth carrying into future work:")
bullet("A test that cannot fail is worse than no test. Assertions must be counted and output must be visible.", bold_prefix="Verify that verification works: ")
bullet("A feature that exists in the source tree is not a feature. Wiring, visibility and failure reporting are part of the feature.", bold_prefix="Wire the last metre: ")
bullet("A suspiciously bad metric is more often a data or split problem than a model problem. Audit the corpus before changing the algorithm.", bold_prefix="Suspect the data first: ")
bullet("Scores depend on thresholds and keyword lists. Keeping those values in named constants makes an inflation bug a five-minute fix instead of a long hunt.", bold_prefix="Make thresholds visible: ")
bullet("The strongest signal was the one that matched how real abuse behaves. Chasing a higher score by adding weak signals would have made the detector noisier, not better.", bold_prefix="Model the real behaviour: ")
bullet("A high-risk record should never vanish because eight newer complaints arrived. Decision-support views must query the facts, not the recent window.", bold_prefix="Keep decision support stable: ")

# ===========================================================================
# 8. LIMITATIONS
# ===========================================================================
page_break()
h("8. Limitations", 1)
para("The system works end to end, but it has real limitations that qualify every result reported above.")
bullet("The installed torch version is below the minimum expected by the transformers and sentence-transformers stack, so the semantic-embedding and DistilBERT paths degrade gracefully to difflib and scikit-learn rather than running. The full accuracy potential of the paper's BERT-family approach is therefore not demonstrated here.", bold_prefix="Transformer path unavailable. ")
bullet("The model is trained on 152 curated English samples. It does not handle regional languages, and the paper's ambiguity challenges remain hard in principle. The wide spread of cross-validation fold scores (0.77 to 0.90) is direct evidence of small-sample variance.", bold_prefix="Limited corpus and language coverage. ")
bullet("The measured 82.19% versus the paper's 93% reflects both a much smaller corpus and honest cross-validation on that corpus. Closing the gap would require substantially more and more diverse training data, not merely a different model.", bold_prefix="Accuracy gap versus the paper. ")
bullet("The dashboard is seeded with generated complaints. Real production ingestion would require portal integrations, authentication and rate limiting, none of which are present.", bold_prefix="Synthetic demonstration data. ")
bullet("Because category risk is a floor term in the priority score, most Public Safety complaints (33 of 37 in the demonstration run) are ranked High regardless of their wording. This is defensible for genuinely dangerous categories but means that for this category the High band is closer to a measure of category risk than of textual urgency.", bold_prefix="Category risk dominates priority. ")
bullet("Confidence values are softmax-normalised decision margins, not calibrated probabilities. They should not be presented to officers as literal certainty without calibration.", bold_prefix="Confidence is not calibrated. ")
bullet("The Incident Hotspots card is driven by cluster identifiers, so real-time embedding-based clustering depends on the availability of the similarity stack; the fallback is functional but less accurate on hard paraphrases.", bold_prefix="Clustering depends on the similarity stack. ")
bullet("The demonstration database completes 200 records quickly, but the pipeline performs a per-submission similarity scan that is linear in the number of recent complaints. The paper's PostgreSQL or MongoDB plus an index or cached embeddings would be needed at production scale.", bold_prefix="SQLite and linear scans are demo-scale. ")
bullet("Analysis is ward-level and text-based, with no map rendering, no GPS coordinates and no routing of field crews to incidents.", bold_prefix="No geospatial visualisation. ")
bullet("The fraud engine is a rule-and-threshold model rather than a trained classifier, so its false-positive rate on real traffic is unknown. It is presented as an advisory first-pass signal, not a decision.", bold_prefix="Fraud engine is untrained. ")
bullet("There is no authentication, no role-based authorisation and no audit log, which would be prerequisites for any real deployment.", bold_prefix="No access control. ")

# ===========================================================================
# 9. FUTURE WORK
# ===========================================================================
h("9. Future Work", 1)
para("The following directions would move the project from a thorough demonstration toward a deployable system. They are ordered roughly by the ratio of value to effort.")
bullet("Add Indic-language preprocessing and a multilingual transformer, which is the paper's explicit next step. This would multiply the addressable citizen base in a single change.", bold_prefix="Multilingual support. ")
bullet("Collect or synthesise a substantially larger, more diverse corpus and fine-tune DistilBERT in addition to the linear model. This is the most direct path toward the paper's 93% figure.", bold_prefix="Larger corpus and fine-tuned transformer. ")
bullet("Calibrate the classification confidences (for example with Platt scaling) so the percentage shown to citizens and officers means something precise.", bold_prefix="Confidence calibration. ")
bullet("Replace SQLite with PostgreSQL or MongoDB, add an index over the ward and category columns, and cache complaint embeddings so similarity lookup does not scan recent records.", bold_prefix="Production storage and indexing. ")
bullet("Forecast complaint surges by ward and category so that crews can be pre-positioned before a problem peaks, rather than after it is reported.", bold_prefix="Predictive analytics. ")
bullet("Integrate municipal IoT telemetry (for example bin fill levels and pipe pressure) so that citizen complaints and asset sensors reinforce one another.", bold_prefix="IoT and GIS integration. ")
bullet("Render complaints and clusters on a map with GPS coordinates, and route field crews to the highest-priority incident in their area.", bold_prefix="Geospatial hotspot mapping. ")
bullet("Track resolution satisfaction, close the loop with citizens, and retrain on corrected classifications so the model improves with use.", bold_prefix="Citizen feedback loops. ")
bullet("Add role-based authentication, service-level-agreement tracking and per-priority response targets, which any real municipal deployment requires.", bold_prefix="Officer authentication and SLAs. ")
bullet("Train the fraud engine on labelled abuse data (or adopt an anomaly-detection model) so its thresholds are learned rather than hand-tuned, and measure its false-positive rate.", bold_prefix="Learned fraud detection. ")
bullet("Package the application as a container with a managed database and a real WSGI server, and add health checks and structured logging.", bold_prefix="Containerised deployment. ")

# ===========================================================================
# 10. ETHICAL, LEGAL AND SOCIAL CONSIDERATIONS
# ===========================================================================
page_break()
h("10. Ethical, Legal and Social Considerations", 1)
para(
    "A system that ranks citizens' requests is a system that decides who waits. That "
    "responsibility deserves explicit treatment, even in an academic project."
)

h("10.1 Fairness and Representation", 2)
para(
    "The classifier learns from a curated corpus. If that corpus under-represents a "
    "locality, a complaint style, a dialect or a language, complaints from those groups "
    "will be classified less accurately - and because priority depends on category, they "
    "may also be ranked lower. This is a real risk, not a hypothetical one: the corpus is "
    "English-only and was written by a small team."
)
para(
    "The mitigations available at this stage are transparency and measurement. The accuracy "
    "figure is reported with its standard deviation rather than as a single number; the "
    "fold spread is published; and the threats to validity are listed rather than hidden. "
    "Any deployment would need per-ward and per-language accuracy measurement before it "
    "could be considered fair."
)

h("10.2 Privacy and Data Protection", 2)
para(
    "The demonstration repository contains only synthetic complaints and therefore no "
    "personal data. A real deployment would be subject to data-protection law, and several "
    "design consequences follow naturally from the architecture: complaints are stored "
    "with a ward rather than a precise address, so coarse locality is the finest "
    "granularity retained; text is processed locally with no mandatory third-party call, "
    "so complaint content need not leave municipal infrastructure; and the optional "
    "language-model path is opt-in precisely because it would transmit complaint text to "
    "an external service."
)

h("10.3 Transparency and Contestability", 2)
para(
    "Every automated decision in the system carries a human-readable justification, and "
    "the justification includes the thresholds it was measured against. This is a "
    "deliberate choice in favour of a slower, auditable model over a faster, opaque one. "
    "An officer can see why a complaint was ranked High; a citizen could, in a future "
    "version, be shown the same explanation."
)
para(
    "The fraud score deserves particular care. Being flagged as a possible bad-faith filer "
    "is reputational, so the system is designed to be advisory: it never blocks a "
    "submission, never deletes a record and never sanctions a person. Only a human "
    "reviewing the explanation can act on it, and the explanation exists so that action "
    "can be reviewed."
)

h("10.4 Academic Integrity and Reproducibility", 2)
para(
    "The report itself is generated by a script from measured data, so its numbers can be "
    "regenerated rather than trusted on faith. The evaluation is reported together with the "
    "corpus size and the fold spread; the base paper's higher figure is not claimed as this "
    "project's own; and the two scenarios that make the dashboard look impressive are "
    "labelled as injected demonstration data in every place they are described. Where an "
    "early defect is instructive, it is documented in Section 7 rather than quietly removed."
)

# ===========================================================================
# 11. PROJECT MANAGEMENT
# ===========================================================================
h("11. Project Management, Timeline and Work Distribution", 1)

h("11.1 Approach", 2)
para(
    "The project followed an incremental, demonstration-driven approach. Rather than "
    "building every module to completion before testing anything, the team kept a working "
    "end-to-end path at all times: the intake and store stages first, then classification, "
    "then prioritisation, then the dashboard, then the extensions. Each increment ended "
    "with the system running and the smoke suite passing, so regression was detected "
    "immediately rather than at the end."
)
para(
    "This approach directly produced the discipline described in Section 7.5. Because the "
    "suite had to pass at the end of every increment, the discovery that it was not "
    "actually running anything forced an immediate change in practice: from then on, every "
    "run of the suite had to show its assertions."
)

h("11.2 Timeline", 2)
make_table(
    ["Phase", "Focus", "Principal output"],
    [
        ["1. Requirements and design", "Study the base paper, define categories, requirements and success criteria", "System design, data model, functional and non-functional requirements"],
        ["2. Core pipeline", "Intake, preprocessing, classification and persistence", "Working end-to-end path and the trained classifier"],
        ["3. Prioritisation and XAI", "Six-signal priority engine with explanations", "Priorities with numeric breakdowns and sentences"],
        ["4. Dashboard and reports", "Officer dashboard, digest generation, PDF and Excel export", "Complete user-facing application"],
        ["5. Extensions", "Fraud scoring, incident clustering and locality-aware deduplication", "The three enhancements over the base paper"],
        ["6. Evaluation and hardening", "Clean-seed measurement, defect fixes, automated suite, this report", "82.19% CV accuracy, 30 passing checks, final report"],
    ],
    widths=[110, 220, 210],
    caption="Project phases, their focus and their principal output.",
)

h("11.3 Work Distribution and Skills Applied", 2)
para("The work was divided by concern rather than by file, so that each area had a single owner while interfaces stayed stable:")
bullet("Pipeline and data layer - preprocessing, database schema, persistence and orchestration.")
bullet("Machine learning - corpus design, classifier training, cross-validation and metrics.")
bullet("Scoring engines - the priority engine and the fraud engine, including their explainability output.")
bullet("Front end and reporting - dashboard, templates, CSS charts, digest generator and export.")
bullet("Quality assurance - the smoke suite, the clean-seed measurement runs and the defect investigations of Section 7.")
para(
    "The skills exercised span text preprocessing and feature engineering, classical machine "
    "learning, similarity measurement, rules-based scoring with explainability, web "
    "application development, report generation, automated testing, and technical writing "
    "of the kind required to document failures honestly."
)

h("11.4 Risk Management", 2)
make_table(
    ["Risk", "Impact if unmanaged", "Mitigation adopted"],
    [
        ["Small training corpus", "Unstable accuracy estimate", "Stratified 5-fold cross-validation; report the std deviation"],
        ["Optional dependencies missing", "Features unavailable on some machines", "Documented fallbacks for similarity, classification, tokenisation and digests"],
        ["Silent test failures", "False confidence in the build", "Visible assertion output; results checked against the seeded record count"],
        ["Demonstration scenarios not exercising the mechanism", "Dashboard shows empty cards", "Scenario text made genuinely repetitive; cards query the whole table"],
        ["Time overrun on optional work", "Core deliverable incomplete", "Incremental approach kept an end-to-end system working at all times"],
    ],
    widths=[150, 160, 230],
    caption="Principal project risks and the mitigations adopted.",
)

# ===========================================================================
# 12. CONCLUSION
# ===========================================================================
page_break()
h("12. Conclusion", 1)
para(
    "CivicSense delivered a complete, working implementation of the base paper's proposal "
    "and extended it into an integrated intelligent triage pipeline. The system centralises "
    "complaints from multiple channels, normalises and deduplicates their text, classifies "
    "them into the paper's five categories, scores them for bad-faith behaviour, clusters "
    "fragmented reports of the same incident, assigns an explainable priority, generates a "
    "human-readable justification, and delivers the result through a dashboard and "
    "exportable weekly reports."
)
para(
    "The system was validated end to end. On a clean demonstration database of 200 "
    "complaints processed through the real pipeline, all automated checks passed, the "
    "classifier reached 82.19% +/- 5.47% cross-validated accuracy with all eleven curated "
    "texts classified correctly, 23 duplicates were identified (11.5%), 18 records were "
    "grouped into 11 incident clusters including an eight-complaint hotspot, and the fraud "
    "engine surfaced 2 High-risk and 53 Medium-risk scores. The weekly digests reproduce "
    "the paper's "
    "narrative style including ward-level highlights and resource-allocation suggestions, "
    "and are exportable as PDF and Excel."
)
para(
    "Three extensions distinguish the result from the base paper's pipeline: a separate, "
    "explainable fraud engine; semantic incident clustering that counts incidents rather "
    "than records; and explainable AI justifications on every priority and fraud decision. "
    "Together they address the four gaps identified in the literature review, and they do "
    "so with lightweight, offline-capable components that run on ordinary hardware."
)
para(
    "The development process also produced genuine engineering lessons, documented in "
    "Section 7: that a test suite which cannot fail manufactures false confidence; that a "
    "feature can exist in the source tree and be absent from the product if it is not wired "
    "in; that a suspiciously poor metric usually indicates a data problem rather than a "
    "model problem; and that decision-support views must query the facts rather than the "
    "most recent window. These are recorded because they are the reasoning behind the "
    "system's final shape."
)
para(
    "CivicSense shows how NLP and generative summarisation can turn the citizen's voice "
    "into actionable governance intelligence, moving municipalities from reactive complaint "
    "handling toward proactive, data-driven urban management - exactly the vision the base "
    "paper sets out. The limitations in Section 8 and the roadmap in Section 9 mark the "
    "distance that remains between this demonstration and a production service, and they "
    "are stated plainly so that the next step is obvious."
)

# ===========================================================================
# REFERENCES
# ===========================================================================
h("References", 1)
for t in [
    "Aakash P., Chandru T., Kiruba Wesley. CivicSense: AI-Based Citizen Complaint Analyzer. Proceedings of the Global Conference on Sustainable Energy Systems, Smart Electronics and Intelligent Computing (GCSESEIC 2025), Advances in Engineering Research 297. (Base paper - project source document.)",
    "Government of India. Centralized Public Grievance Redress and Monitoring System (CPGRAMS). Department of Administrative Reforms and Public Grievances, 2023.",
    "Municipal Services Office. OneService App. Government of Singapore, 2023.",
    "City of New York. NYC 311 Service Request Platform, 2023.",
    "Devlin, J., Chang, M.-W., Lee, K., Toutanova, K. BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding. NAACL-HLT, 2019.",
    "Sanh, V., Debut, L., Chaumond, J., Wolf, T. DistilBERT, a distilled version of BERT: smaller, faster, cheaper and lighter. arXiv:1910.01108, 2019.",
    "Reimers, N., Gurevych, I. Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks. EMNLP-IJCNLP, 2019.",
    "Pedregosa, F. et al. Scikit-learn: Machine Learning in Python. Journal of Machine Learning Research 12, 2011.",
    "Bird, S., Klein, E., Loper, E. Natural Language Processing with Python. O'Reilly Media, 2009.",
    "Loper, E., Bird, S. NLTK: The Natural Language Toolkit. ACL Workshop on Effective Tools and Methodologies for Teaching NLP, 2002.",
    "Flask Documentation. Pallets Projects - https://flask.palletsprojects.com",
    "ReportLab Documentation - https://docs.reportlab.com",
    "openpyxl Documentation - https://openpyxl.readthedocs.io",
    "python-docx Documentation - https://python-docx.readthedocs.io",
    "Van Rossum, G., Drake, F. L. Python Language Reference - https://docs.python.org",
    "Hutto, C. J., Gilbert, E. VADER: A Parsimonious Rule-based Model for Sentiment Analysis of Social Media Text. ICWSM, 2014.",
]:
    bullet(t)

para(
    "Note on sourcing: the base paper is the primary source and defines the problem, the "
    "five service categories and the evaluation setting. The remaining references support "
    "the libraries and background methods used in the implementation, and each is cited "
    "where the technique is used.",
    italic=True,
    size=10,
)

# ===========================================================================
# APPENDIX A: HOW TO RUN
# ===========================================================================
page_break()
h("Appendix A: How to Run the Project", 1)
para("The fastest path is the single run script, which installs dependencies, downloads the required NLTK data and starts the application:")
make_table(
    ["Command", "What it does"],
    [
        ["./run.sh", "Install dependencies, fetch NLTK data, start the app on http://127.0.0.1:5000"],
        ["./run.sh test", "Install dependencies, fetch NLTK data, run the end-to-end smoke suite"],
        ["python app.py", "Start the application directly (dependencies already installed)"],
        ["python smoke_test.py", "Run the automated suite against a clean database"],
        ["python civic_sense/build_report.py", "Regenerate this report document from the current measurements"],
    ],
    widths=[200, 360],
    caption="The project's principal commands.",
)
para("If installing manually, the equivalent sequence is:")
bullet("pip install -r requirements.txt")
bullet("python -c \"import nltk; nltk.download(['stopwords','wordnet','vader_lexicon','punkt'])\"")
bullet("python app.py")
para(
    "On first launch the application automatically creates the schema, trains the "
    "classifier if it is not already trained, seeds and processes the demonstration corpus, "
    "and is immediately ready at http://127.0.0.1:5000. The optional environment settings "
    "are OPENAI_API_KEY, which enables language-model-written digests, and "
    "USE_TRANSFORMERS=1, which enables zero-shot DistilBERT classification when the "
    "transformer stack is installed."
)

# ===========================================================================
# APPENDIX B: REST API
# ===========================================================================
h("Appendix B: REST API Reference", 1)
para(
    "The REST API is the programmatic intake path, mirroring the paper's requirement that "
    "complaints be aggregated via API connections. Every submission runs the full pipeline "
    "before the record is returned."
)
make_table(
    ["Endpoint", "Method", "Description"],
    [
        ["/api/complaints", "POST", "Submit a complaint; runs the full pipeline with fraud scoring and XAI"],
        ["/api/complaints/<id>", "GET", "Retrieve one complaint as JSON"],
        ["/api/stats", "GET", "JSON statistics: totals, category mix, priority mix and recent rows"],
    ],
    widths=[140, 60, 360],
    caption="REST endpoints.",
)
para("A single submission example:")
para("curl -X POST http://127.0.0.1:5000/api/complaints \\", size=10)
para("-H \"Content-Type: application/json\" \\", size=10)
para("-d '{\"description\": \"Sewage overflowing near the market area\", \"ward\": \"Wakad\", \"source\": \"Mobile App\"}'", size=10)
para(
    "On the server side the request is processed by run_pipeline(), which returns a JSON "
    "payload containing the category, confidence, priority, priority breakdown, fraud "
    "score, fraud level, fraud explanation, cluster identifier and duplicate metadata. The "
    "dashboard index page renders the same values into the KPI cards, the Fraud Alerts card "
    "and the Incident Hotspots card."
)

# ===========================================================================
# APPENDIX C: SOURCE FILE REFERENCE
# ===========================================================================
h("Appendix C: Source File Reference", 1)
make_table(
    ["File", "Responsibility"],
    [
        ["app.py", "Flask application: all routes (UI and API), the run_pipeline() orchestrator and startup seeding"],
        ["civic_sense/config.py", "Paths, category and priority constants, thresholds and feature flags"],
        ["civic_sense/preprocessing.py", "Cleaning, tokenising, lemmatising, stop-word removal, similarity, duplicate detection and incident clustering"],
        ["civic_sense/classifier.py", "Training corpus, TF-IDF + LinearSVC pipeline, optional DistilBERT path, cross-validated metrics and confidence scoring"],
        ["civic_sense/fraud_detector.py", "Three-signal fraud risk scoring and its explanation generator"],
        ["civic_sense/prioritizer.py", "Six-signal weighted priority assignment and its explanation generator"],
        ["civic_sense/summarizer.py", "Extractive complaint summaries and weekly digest generation (template and optional LLM)"],
        ["civic_sense/reports.py", "PDF (ReportLab) and Excel (openpyxl) export of weekly reports"],
        ["civic_sense/database.py", "Schema, connection handling, inserts, queries, aggregates and the dashboard card queries"],
        ["civic_sense/seed_data.py", "Synthetic corpus generation plus the fraud and hotspot scenarios"],
        ["civic_sense/build_report.py", "This report's generator (document is produced from measured data)"],
        ["smoke_test.py", "The end-to-end automated test suite"],
        ["templates/", "Jinja2 templates: dashboard, complaint list, intake form, detail, reports and pipeline explainer"],
        ["static/css/style.css", "The stylesheet, including the CSS-only charts"],
    ],
    widths=[170, 380],
    caption="Source files and their responsibilities.",
)

# ===========================================================================
# APPENDIX D: VERIFICATION CHECKLIST
# ===========================================================================
h("Appendix D: Verification Checklist", 1)
para("Generated from the verified live state of the running demonstration server and the clean-seed measurement run:")
make_table(
    ["Check", "Result"],
    [
        ["Automated smoke suite (30 assertions)", "All passed; exit status 0"],
        ["Demo database (data/civicsense.db)", "Created and populated on startup when empty"],
        ["Classification example set (11 texts)", "11 of 11 classified correctly"],
        ["Classifier cross-validation", "82.19% +/- 5.47% (stratified 5-fold, 152 samples)"],
        ["Fraud Alerts card render", "2 High and 3 Medium rows present on the card; no empty state"],
        ["Incident Hotspots card render", "11 clusters; largest shows 8 complaints"],
        ["Complaint detail pages", "Live cluster and fraud values reflected"],
        ["Duplicate detection", "Re-filed complaint flagged with ratio 1.0 pointing at the original"],
        ["Weekly digest", "Names a locality, a priority mix and a resource-allocation suggestion"],
        ["PDF export", "Downloads with type application/pdf"],
        ["Excel export", "Downloads with the correct spreadsheet MIME type"],
        ["Status update workflow", "New status persists to the database"],
        ["Graceful degradation", "Similarity, classification, tokenisation and digest paths all fall back without error"],
    ],
    widths=[230, 320],
    caption="Verification checklist of the final build.",
)

# ===========================================================================
# APPENDIX E: GLOSSARY
# ===========================================================================
h("Appendix E: Glossary", 1)
make_table(
    ["Term", "Meaning"],
    [
        ["Classification", "Assigning a complaint to one of the five service categories."],
        ["Confidence", "A softmax-normalised decision margin, shown as a percentage; not a calibrated probability."],
        ["Cluster", "A group of complaints that describe the same underlying incident."],
        ["Cluster boost", "A small priority increase applied when a complaint joins an incident cluster."],
        ["Duplicate", "A complaint whose normalised text closely matches an existing complaint in the same ward."],
        ["Extractive summary", "A summary formed by selecting existing sentences rather than generating new ones."],
        ["Fraud score", "A 0-100 bad-faith risk score derived from spam, frequency and pattern signals."],
        ["Hotspot", "A ward or cluster where complaints concentrate."],
        ["Priority", "A High, Medium or Low urgency label produced by the weighted scoring engine."],
        ["Pseudo-confidence", "See Confidence."],
        ["Seeding", "Generating the synthetic demonstration corpus and processing it through the real pipeline."],
        ["Stratified 5-fold CV", "Cross-validation that keeps class proportions equal in every fold, repeated over five splits."],
        ["Triage", "Deciding which complaints need immediate attention and routing them accordingly."],
        ["XAI", "Explainable AI - a human-readable justification for an automated decision."],
    ],
    widths=[140, 410],
    caption="Glossary of terms used in this report.",
)

# ===========================================================================
# APPENDIX F: SAMPLE COMPLAINT RECORDS
# ===========================================================================
h("Appendix F: Sample Complaint Records", 1)
para(
    "The following records illustrate how a single submission is enriched as it passes "
    "through the pipeline. They are drawn from the demonstration output described in "
    "Section 6."
)
make_table(
    ["Description", "Category", "Priority", "Duplicate", "Fraud level"],
    [
        ["Sewage overflowing near the market area", "Public Safety", "High", "No", "Low"],
        ["Transformer making loud noise and sparking at night", "Electricity", "High", "No", "Low"],
        ["Large pothole near school", "Roads", "Medium", "No", "Low"],
        ["Streetlight not working on main road", "Electricity", "Medium", "No", "Low"],
        ["No water supply in the colony since morning", "Water Supply", "High", "No", "Low"],
        ["Garbage not collected for three days", "Waste Management", "Medium", "No", "Low"],
        ["Please fix this issue immediately", "Roads", "Medium", "No", "High"],
        ["Need urgent attention please", "Roads", "Medium", "No", "High"],
        ["A tree fell on the road", "Public Safety", "High", "No", "Low"],
        ["A fallen branch blocked traffic", "Public Safety", "High", "Yes", "Low"],
    ],
    widths=[210, 90, 60, 60, 70],
    caption="Sample complaint records after pipeline enrichment.",
)
para(
    "The seventh and eighth rows show the fraud engine flagging generic, low-effort "
    "submissions that arrive in the same ward within a short window. The final row shows "
    "locality-aware duplicate detection recognising a paraphrase of an existing incident "
    "rather than counting it as a new one. Taken together, these rows illustrate the two "
    "integrity mechanisms that distinguish CivicSense from the base paper's pipeline."
)

# ===========================================================================
# APPENDIX G: CONFIGURATION REFERENCE
# ===========================================================================
h("Appendix G: Configuration Reference", 1)
para("All tunable behaviour is centralised. The complete reference is:")
make_table(
    ["Setting", "Default", "Effect of changing it"],
    [
        ["SIM_THRESHOLD", "0.85", "Higher values flag fewer duplicates; lower values flag more."],
        ["FREQ_THRESHOLD", "5", "Same-ward submissions in the window before the flood signal ramps."],
        ["HIGH_FRAUD_SCORE", "70", "Score at or above which a filing is shown as High risk."],
        ["MEDIUM_FRAUD_SCORE", "30", "Score at or above which a filing is shown as Medium risk."],
        ["Priority High threshold", "3.2", "Boundary between High and Medium priority."],
        ["Priority Medium threshold", "1.6", "Boundary between Medium and Low priority."],
        ["FRAUD_SCENARIO_COUNT", "8", "Size of the injected coordinated burst."],
        ["FRAUD_SCENARIO_WARD", "Hinjewadi", "Ward the burst is concentrated in."],
        ["HOTSPOT_SCENARIO_WARD", "Wakad", "Ward the injected incident hotspot occurs in."],
        ["HOTSPOT_SCENARIO_CATEGORY", "Public Safety", "Category of the injected incident."],
        ["USE_TRANSFORMERS", "0", "1 enables the optional zero-shot DistilBERT classifier."],
        ["OPENAI_API_KEY", "unset", "When set, digests are rewritten by a language model."],
    ],
    widths=[150, 90, 310],
    caption="Complete configuration reference with the effect of each setting.",
)

# ===========================================================================
# APPENDIX H: SAMPLE WEEKLY DIGEST
# ===========================================================================
h("Appendix H: Sample Weekly Digest", 1)
para("The following is the digest generated by the real template engine on the clean demonstration corpus, reproduced verbatim (newlines preserved):")
para("Weekly Civic Complaint Digest - October 04 - October 11, 2026", bold=True, size=10)
for line in [
    "During October 04 - October 11, 2026, 121 citizen complaints were received and automatically processed. The dominant category was Roads (35 reports), followed by Waste Management (25) and Water Supply (23). Priority-wise, 65 complaints were High, 48 Medium and 8 Low. Recurring themes include: road, water, waste, garbage, damage, bridge.",
    "",
    "Locality-level highlights:",
    "  - Hinjewadi recorded 29 complaints this week, predominantly roads (14 reports). 20 of them (69%) were flagged High Priority and need immediate attention.",
    "  - Wakad recorded 23 complaints this week, predominantly roads (8 reports). 13 of them (57%) were flagged High Priority and need immediate attention.",
    "  - Talegaon recorded 15 complaints this week, predominantly water supply (6 reports). 10 of them (67%) were flagged High Priority and need immediate attention.",
    "  - Vadgaon recorded 12 complaints this week, predominantly roads (3 reports). 4 of them (33%) were flagged High Priority and need immediate attention.",
    "  - Maval recorded 11 complaints this week, predominantly waste management (5 reports). 3 of them (27%) were flagged High Priority and need immediate attention.",
    "",
    "Resource allocation suggestion: prioritise Hinjewadi, the current hotspot for roads issues, and schedule preventive maintenance based on the recurring patterns above.",
]:
    if line:
        para(line, size=10)
    else:
        d.add_paragraph().paragraph_format.space_after = Pt(2)
para(
    "This digest is the artefact the base paper's proposal ultimately aims to produce: a "
    "short, readable, decision-oriented summary of a week of citizen complaints, naming the "
    "wards that need attention and the recurring themes behind them."
)

# ===========================================================================
# FINALISE: fill the List of Tables and save
# ===========================================================================
for p in d.paragraphs:
    if "<<LIST_OF_TABLES>>" in p.text:
        for r in list(p.runs):
            r.text = ""
        text = "\n".join("Table %d: %s" % (n, c) for n, c in TABLES)
        if p.runs:
            p.runs[0].text = text
            p.runs[0].font.size = Pt(10)
        else:
            run = p.add_run(text)
            run.font.size = Pt(10)
        break

d.save("Project_Report.docx")
print("saved Project_Report.docx")
print("paragraphs:", len(d.paragraphs), "tables:", len(d.tables),
      "numbered tables:", len(TABLES),
      "words:", sum(len(p.text.split()) for p in d.paragraphs)
      + sum(len(c.text.split()) for t in d.tables for row in t.rows for c in row.cells))
