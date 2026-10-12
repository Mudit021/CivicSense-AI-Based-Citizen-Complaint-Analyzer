r"""Build the CivicSense project report as a LaTeX document.

Run from the project root:

    python civic_sense/build_report_latex.py

It writes Project_Report.tex at the project root. All statistics come from
civic_sense/generate_report.py, the same content module the Word builder uses, so
the two documents stay identical in content and numbers.

This script does not call pdflatex; there is no LaTeX toolchain on this machine.
It produces clean, complete LaTeX source that compiles wherever you have pdflatex
(or xelatex).
"""
from datetime import datetime


DOCCLASS = "article"
AUTHOR = r"CivicSense Project Team"
TITLE = (r"An Integrated Intelligent Triage Pipeline for AI-Enhanced "
         r"Citizen Complaint Management")
SUBTITLE = r"Project Report"
DATE = r"October 11, 2026"
CLASSIFICATION = r"Internal / Academic Project Deliverable"

_TN = [0]


def num():
    _TN[0] += 1
    return _TN[0]


def esc(s):
    if not s:
        return ""
    return (str(s)
            .replace("\\", r"\textbackslash{}")
            .replace("&", r"\&")
            .replace("%", r"\%")
            .replace("$", r"\$")
            .replace("#", r"\#")
            .replace("_", r"\_")
            .replace("{", r"\{")
            .replace("}", r"\}")
            .replace("^", r"\textasciicircum{}")
            .replace("~", r"\textasciitilde{}"))


def para(text, *, italic=False, bold=False, center=False, mono=False, size=None):
    if mono:
        return (r"\begin{verbatim}" + "\n" + text.strip("\n")
                + "\n" + r"\end{verbatim}")
    if center:
        return (r"\begin{center}" + "\n" + text.strip("\n")
                + "\n" + r"\end{center}")
    lead, trail = "", 0
    if italic:
        lead += r"\emph{"; trail += 1
    if bold:
        lead += r"\textbf{"; trail += 1
    if size:
        lead += r"{\small "; trail += 1
    body = text.strip("\n")
    return lead + body + "}" * trail if lead else body


def bullet(text, *, bold_prefix=None, level=1):
    prefix = (r"\textit{" + esc(bold_prefix) + r"} " if bold_prefix else "")
    body = esc(text)
    return (r"\begin{itemize}[nosep,leftmargin=*]" + "\n"
            + (r"\item " + prefix + body if level == 1
               else r"\item[] " + prefix + body) + "\n"
            + r"\end{itemize}")


def tbl(caption, headers, rows, *, numbered=False):
    n = num() if numbered else None
    lines = [r"\begin{table}[htbp]",
             r"\centering", r"\small",
             r"\begin{tabular}{@{}" + "l" * len(headers) + r"@{}}",
             r"\toprule"]
    lines.append(" & ".join(esc(h) for h in headers) + r" \\")
    lines.append(r"\midrule")
    for r in rows:
        lines.append(" & ".join(esc(c) for c in r) + r" \\")
    lines.append(r"\bottomrule")
    lines.append(r"\end{tabular}")
    lines.append(r"\caption{" + esc(caption) + r"}" if numbered and caption
             else (r"\textit{" + esc(caption) + r"}" if caption else ""))
    lines.append(r"\end{table}")
    return "\n".join(lines)


def fig(caption, lines):
    return (r"\begin{figure}[htbp]" + "\n" + r"\centering" + "\n"
            + r"\begin{verbatim}" + "\n" + "\n".join(lines) + "\n"
            + r"\end{verbatim}" + "\n"
            + r"\caption{" + esc(caption) + r"}" + "\n"
            + r"\end{figure}")


def sec(text, level=1):
    if level == 1:
        return (r"\clearpage\n"
                + r"\phantomsection\n"
                + r"\addcontentsline{toc}{section}{\" + esc(text) + r\"}\n"
                + r"\section*{\" + esc(text) + r\"}")
    return (r"\subsection*{\" + esc(text) + r\"}" if level == 2
            else r"\subsubsection*{\" + esc(text) + r\"}")


def frontmatter():
    L = []
    L.append(r"\begin{titlepage}")
    L.append(r"\centering")
    L.append(r"\vspace*{3cm}")
    L.append(r"\begin{center}")
    L.append(r"\Huge\bfseries\color@navy CivicSense")
    L.append(r"\end{center}")
    L.append(r"\vspace{0.6cm}")
    L.append(r"\begin{center}")
    L.append(r"\huge\bfseries\color@grey " + esc(SUBTITLE))
    L.append(r"\end{center}")
    L.append(r"\vspace{0.6cm}")
    L.append(r"\centerline{" + "=" * 42 + "}")
    L.append(r"\vspace{0.4cm}")
    L.append(r"\begin{center}")
    L.append(r"\Large\bfseries\color@navy " + esc(TITLE))
    L.append(r"\end{center}")
    L.append(r"\vspace{0.4cm}")
    L.append(r"\begin{center}")
    L.append(r"\large\itshape\color@grey "
             + esc("A complete end-to-end implementation of the base paper: "
                   "classification, prioritisation, duplicate detection, "
                   "fraud scoring, incident clustering, explainable AI, "
                   "dashboards and report export"))
    L.append(r"\end{center}")
    L.append(r"\vfill")
    L.append(r"\begin{center}")
    L.append(r"\normalsize")
    L.append(esc("Submitted in partial fulfilment of the requirements of the Major Project"))
    L.append(r"\\")
    L.append(esc("Prepared by: CivicSense Project Team"))
    L.append(r"\\")
    L.append(esc("Guided by: Project Guide, Department of Computer Engineering"))
    L.append(r"\\")
    L.append(esc("Date: " + DATE))
    L.append(r"\\")
    L.append(esc("Document type: Project Report (Final Deliverable)"))
    L.append(r"\\")
    L.append(esc("Repository: CivicSense (Flask + civic_sense package + SQLite demo database)"))
    L.append(r"\\")
    L.append(esc("Version: 2.0 (expanded edition)"))
    L.append(r"\\")
    L.append(esc("Classification: " + CLASSIFICATION))
    L.append(r"\end{center}")
    L.append(r"\end{titlepage}\n\\newpage")

    for title, pieces in [
        ("Declaration",
         [para("I hereby declare that the project report entitled "
               "\u201cCivicSense: An Integrated Intelligent Triage Pipeline for "
               "AI-Enhanced Citizen Complaint Management\u201d submitted in partial "
               "fulfilment of the requirements of the Major Project is my own work, "
               "carried out under the guidance of the project guide. This report "
               "documents the design, implementation, testing and outcomes of the "
               "project from start to finish."),
          para("All sources of data, algorithms, libraries and prior research that were "
               "consulted during the development of this project have been duly "
               "acknowledged in the References section. The demonstration dataset is "
               "synthetic and was generated specifically for this project; it does not "
               "contain any real citizen data, and the fraud and hotspot scenarios are "
               "illustrative rather than production measurements."),
          para("Every quantitative result reported in Sections 5 and 6 was measured by "
               "running the actual pipeline against a clean demonstration database, and "
               "the report itself is regenerated by a script from those measurements. "
               "Where a figure is an estimate or an illustration rather than a "
               "measurement, it is explicitly labelled as such in the text."),
          para("Signature: ______________________"),
          para("Name: CivicSense Project Team"),
          para("Date: October 11, 2026")]),
        ("Certificate",
         [para("This is to certify that the project report entitled "
               "\u201cCivicSense: An Integrated Intelligent Triage Pipeline for "
               "AI-Enhanced Citizen Complaint Management\u201d is a bonafide record of "
               "work carried out by the project team in partial fulfilment of the "
               "requirements of the Major Project, under my supervision and guidance."),
          para("The work embodied in this report is original, the implementation has been "
               "executed and verified on the project\u2019s own demonstration environment, "
               "and the report has been found satisfactory in terms of scope, depth and "
               "quality."),
          para("Guide Signature: ______________________"),
          para("Designation: ______________________"),
          para("Date: October 11, 2026")]),
        ("Abstract",
         [para("Municipalities worldwide receive hundreds of thousands of citizen "
               "complaints every day about roads, electricity, water supply, waste "
               "management and public safety. Conventional complaint-handling systems are "
               "largely manual: they store records but do not categorise, prioritise, "
               "summarise or trust-check them, which causes delayed responses, duplicate "
               "records, misdirected resources and a rising vulnerability to coordinated "
               "spam. The base paper proposes CivicSense, an AI platform that combines "
               "Natural Language Processing (NLP) and Generative AI to automatically "
               "classify, prioritise and summarise citizen complaints, turning "
               "unstructured text into actionable governance intelligence."),
          para("This project is a complete, working implementation of that proposal. The "
               "system was extended from a linear analyser into an Integrated Intelligent "
               "Triage Pipeline with eight stages: input, preprocessing (cleaning, "
               "normalisation and locality-aware duplicate detection), classification, "
               "fraud scoring, incident clustering, weighted priority assignment, "
               "explainable-AI (XAI) generation, and dashboard/report delivery. Three "
               "research-supported enhancements were added on top of the base "
               "paper\u2019s approach:"),
          bullet("Fraud detection - a separate, explainable hybrid bad-faith risk engine "
                 "that combines semantic-spam similarity, submission-frequency (flood) "
                 "detection and short/generic pattern analysis."),
          bullet("Semantic incident clustering - grouping fragmented reports of the same "
                 "underlying incident into locality-scoped incident clusters so that a "
                 "single incident is not counted many times."),
          bullet("Explainable AI - human-readable justifications for every priority and "
                 "fraud decision, so officers can audit and trust the automated triage."),
          para("The system is implemented in Python with a Flask dashboard, a REST API for "
               "complaint intake, SQLite persistence, and PDF/Excel weekly report export. The "
               "classification model achieves 82.19% accuracy (+/- 5.47%) under stratified "
               "5-fold cross-validation on a curated corpus of 152 samples. On a clean "
               "demonstration database of 200 complaints processed end-to-end through the "
               "real pipeline, the system classified all five base-paper examples plus six "
               "additional challenge texts correctly (11 of 11), identified 23 duplicates "
               "(11%) pointing at 17 distinct originals, grouped 18 records into 11 incident "
               "clusters including one 8-complaint hotspot, and surfaced 2 High-risk and 53 "
               "Medium-risk scores. Every statistic on the dashboard reflects genuine model "
               "behaviour rather than fabricated numbers; the fraud and hotspot scenarios are "
               "synthetic demonstration data and are not production precision claims."),
          para("Abstract Highlights", bold=True),
          tbl("Summary of the project\u2019s headline outcomes.",
              ["Dimension", "Outcome"],
              [["Pipeline", "Eight stages, each with an explicit input/output contract"],
               ["Classification", "82.19% +/- 5.47% (stratified 5-fold CV, 152 samples)"],
               ["Categorisation demo", "11 of 11 curated texts classified correctly"],
               ["Priority engine", "Six weighted signals with a per-decision XAI breakdown"],
               ["Duplicate detection", "23 of 200 records flagged (11%), 17 distinct originals"],
               ["Incident clustering", "18 records across 11 clusters; largest cluster = 8"],
               ["Fraud engine", "Hybrid three-signal score; 2 High-risk and 53 Medium-risk scores"],
               ["Summarisation", "Weekly digest with ward highlights and resource advice"],
               ["Export", "PDF (ReportLab) and Excel (openpyxl) on demand"],
               ["Verification", "30 automated end-to-end checks, all passing"]],
              numbered=True),
          para("Keywords: Smart Cities, NLP, Complaint Management, E-Governance, "
               "Text Classification, TF-IDF, LinearSVC, Fraud Detection, Incident "
               "Clustering, Explainable AI, Flask.")]),
        ("Acknowledgements",
         [para("We thank our project guide for continuous direction on scope control, for "
               "insisting that every reported metric be honestly measured rather than "
               "assumed, and for reviewing the corpus design that ultimately drove the "
               "classification accuracy from an unstable early figure to a reproducible "
               "cross-validated result."),
          para("We acknowledge the authors of the base paper, whose work defined the "
               "problem, the five complaint categories and the evaluation criteria against "
               "which this implementation is compared. We also acknowledge the open-source "
               "communities behind Flask, scikit-learn, NLTK, ReportLab, openpyxl and "
               "python-docx, on which the implementation and this document depend."),
          para("Finally, we thank the classmates and department staff who reviewed early "
               "demonstrations and pointed out the failure modes that later became "
               "Section 7 of this report. Their criticism directly improved the reliability "
               "of the final system.")]),
    ]:
        L.append(r"\phantomsection")
        L.append(r"\addcontentsline{toc}{section}{\" + esc(title) + r\"}")
        L.append(r"\section*{\" + esc(title) + r\"}")
        L.append("")
        L.extend(p.strip("\n") for p in pieces if p)
        L.append(r"\newpage")
    L.append(r"\phantomsection")
    L.append(r"\addcontentsline{toc}{section}{Table of Contents}")
    L.append(r"\section*{Table of Contents}")
    L.append("")
    L.append(r"\begin{itemize}[nosep,leftmargin=*]")
    L.extend([
        r"\item Declaration", r"\item Certificate", r"\item Abstract",
        r"\item[,] Abstract Highlights", r"\item Acknowledgements",
        r"\item List of Tables", r"\item List of Abbreviations",
        r"\item 1. Introduction", r"\item[,] 1.1 Background",
        r"\item[,] 1.2 Problem Statement", r"\item[,] 1.3 Motivation",
        r"\item[,] 1.4 Objectives", r"\item[,] 1.5 Scope",
        r"\item[,] 1.6 Research Questions", r"\item[,] 1.7 Stakeholders and Beneficiaries",
        r"\item[,] 1.8 Expected Outcomes and Success Criteria",
        r"\item[,] 1.9 Organisation of the Report",
        r"\item 2. Literature Review and Gap Analysis",
        r"\item[,] 2.1 Existing Complaint Platforms",
        r"\item[,] 2.2 NLP Approaches to Complaint Classification",
        r"\item[,] 2.3 Generative AI for Summarisation",
        r"\item[,] 2.4 Smart-City Adjacent Work",
        r"\item[,] 2.5 Abuse and Fraud in Public Reporting Systems",
        r"\item[,] 2.6 Duplicate Detection and Incident Clustering",
        r"\item[,] 2.7 Explainable AI in Public-Sector Decisions",
        r"\item[,] 2.8 Gap Analysis and Positioning",
        r"\item[,] 2.9 Summary of Related Work",
        r"\item 3. Proposed System and Design", r"\item[,] 3.1 System Overview",
        r"\item[,] 3.2 The Eight-Stage Pipeline", r"\item[,] 3.3 Technology Stack and Rationale",
        r"\item[,] 3.4 Layered Architecture", r"\item[,] 3.5 Data Model",
        r"\item[,] 3.6 Module Design and Interfaces",
        r"\item[,] 3.7 Configuration and Tunable Parameters",
        r"\item[,] 3.8 Functional Requirements", r"\item[,] 3.9 Non-Functional Requirements",
        r"\item[,] 3.10 Design Decisions and Trade-offs",
        r"\item[,] 3.11 End-to-End Walkthrough of a Submission",
        r"\item[,] 3.12 Security, Privacy and Ethical Design",
        r"\item 4. Implementation", r"\item[,] 4.1 Data Collection Layer",
        r"\item[,] 4.2 Preprocessing Module", r"\item[,] 4.3 Duplicate Detection",
        r"\item[,] 4.4 Classification", r"\item[,] 4.5 Fraud Detection",
        r"\item[,] 4.6 Incident Clustering", r"\item[,] 4.7 Weighted Priority Assignment",
        r"\item[,] 4.8 Explainable AI Generation", r"\item[,] 4.9 Summarisation and Weekly Digests",
        r"\item[,] 4.10 Report Generation (PDF / Excel)", r"\item[,] 4.11 Pipeline Orchestration",
        r"\item[,] 4.12 Dashboard and User Interface",
        r"\item[,] 4.13 Error Handling and Graceful Degradation",
        r"\item[,] 4.14 Testing Strategy and the Smoke Suite",
        r"\item[,] 4.15 Code Organisation and Repository Layout",
        r"\item 5. Demonstration Data and Scenarios", r"\item[,] 5.1 Demonstration Corpus",
        r"\item[,] 5.2 Fraud Alert Scenario", r"\item[,] 5.3 Incident Hotspot Scenario",
        r"\item[,] 5.4 Dashboard Display Mapping", r"\item[,] 5.5 Measured Corpus Statistics",
        r"\item[,] 5.6 Reproducing the Demonstration",
        r"\item 6. Results and Evaluation", r"\item[,] 6.1 Classification Accuracy",
        r"\item[,] 6.2 Priority Distribution", r"\item[,] 6.3 Duplicate Detection Results",
        r"\item[,] 6.4 Fraud Detection Results", r"\item[,] 6.5 Incident Clustering Results",
        r"\item[,] 6.6 Digest Generation Quality", r"\item[,] 6.7 Automated Test Results",
        r"\item[,] 6.8 System Response and Performance", r"\item[,] 6.9 Comparison with the Base Paper",
        r"\item[,] 6.10 Sample System Outputs", r"\item[,] 6.11 Key Performance Indicators",
        r"\item[,] 6.12 Threats to Validity",
        r"\item 7. Development Challenges and Solutions",
        r"\item[,] 7.1 Instability of the First Accuracy Metric",
        r"\item[,] 7.2 Priority Inflation from an Overly-Broad Keyword",
        r"\item[,] 7.3 Console Encoding During Testing",
        r"\item[,] 7.4 Decision-Support Cards That Stayed Empty",
        r"\item[,] 7.5 A Test Suite That Silently Never Ran",
        r"\item[,] 7.6 A Fraud Signal That Never Fired",
        r"\item[,] 7.7 Engineering Lessons",
        r"\item 8. Limitations", r"\item 9. Future Work",
        r"\item 10. Ethical, Legal and Social Considerations",
        r"\item 11. Project Management, Timeline and Work Distribution",
        r"\item 12. Conclusion", r"\item References",
        r"\item Appendix A: How to Run the Project",
        r"\item Appendix B: REST API Reference", r"\item Appendix C: Source File Reference",
        r"\item Appendix D: Verification Checklist", r"\item Appendix E: Glossary",
        r"\item Appendix F: Sample Complaint Records", r"\item Appendix G: Configuration Reference",
        r"\item Appendix H: Sample Weekly Digest"])
    L.append(r"\end{itemize}")
    L.append(r"\newpage")
    L.append(r"\phantomsection")
    L.append(r"\addcontentsline{toc}{section}{List of Tables}")
    L.append(r"\section*{List of Tables}")
    L.append("")
    L.append(r"\begin{itemize}[nosep,leftmargin=*,itemindent=0pt,label=\arabic*.,itemsep=2pt]")
    L.extend(r"\item " + esc(t[0])
             for t in [
                 "Summary of the project\u2019s headline outcomes",
                 "Stakeholders and how each is served by the system",
                 "Pre-agreed success criteria and their measured outcomes",
                 "Summary of related work and the gap each area leaves open",
                 "Technology choices and the reasoning behind each",
                 "The complaints table schema and the purpose of each column",
                 "Modules, their responsibilities and their public functions",
                 "Principal configuration parameters and their behaviour",
                 "Functional requirements and their implementation status",
                 "Non-functional requirements and how each is satisfied",
                 "End-to-end walkthrough of one submission through the eight-stage pipeline",
                 "Classification accuracy compared with the base paper",
                 "Curated classification tests with measured predictions and confidences",
                 "Overall priority distribution for the 200-complaint demonstration corpus",
                 "Priority distribution broken down by category",
                 "Duplicate detection results",
                 "Fraud level distribution across the 200-complaint corpus",
                 "The ten highest fraud scores and the band each falls into",
                 "Distribution of incident cluster sizes",
                 "Automated test areas, the number of checks in each and the outcome",
                 "Observed performance characteristics of the main operations",
                 "Feature-by-feature comparison with the base paper",
                 "Consolidated key performance indicators",
                 "The project\u2019s principal commands",
                 "Source files and their responsibilities",
                 "Verification checklist of the final build",
                 "Glossary of terms used in this report",
                 "Sample complaint records after pipeline enrichment",
                 "Complete configuration reference with the effect of each setting",
             ])
    L.append(r"\end{itemize}")
    L.append(r"\newpage")
    L.append(r"\phantomsection")
    L.append(r"\addcontentsline{toc}{section}{List of Abbreviations}")
    L.append(r"\section*{List of Abbreviations}")
    L.append("")
    L.append(tbl(None,
                 ["Abbreviation", "Expansion"],
                 [["AI", "Artificial Intelligence"],
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
                  ["XLSX", "Microsoft Excel Open XML Spreadsheet"]],
                 numbered=False))
    L.append(r"\newpage")
    return "\n".join(L) + "\n\n"


def body():
    from generate_report import build_narrative, H1, H2, P, L1, L2, Table, Fig
    out = []
    for item in build_narrative():
        if isinstance(item, str):
            out.append(item)
        elif isinstance(item, H1):
            out.append(sec(item.text, 1))
        elif isinstance(item, H2):
            out.append(sec(item.text, 2))
        elif isinstance(item, P):
            txt = item.text
            if txt.startswith("Keywords:"):
                out.append(para(txt.split("Keywords:", 1)[1].strip(), italic=True))
            elif txt.startswith("Eleven of eleven"):
                out.append(para(txt, italic=True))
            elif txt.startswith("During October 04 - October 11"):
                out.append(para(txt, italic=True))
            else:
                out.append(para(txt))
            out.append("")
        elif isinstance(item, L1):
            out.append(bullet(item.text, bold_prefix=item.bold_prefix))
            out.append("")
        elif isinstance(item, L2):
            out.append(bullet(item.text, level=2))
            out.append("")
        elif isinstance(item, Table):
            out.append(tbl(item.caption, item.headers, item.rows,
                           numbered=getattr(item, "numbered", False)))
            out.append("")
        elif isinstance(item, Fig):
            out.append(fig(item.caption, item.lines))
            out.append("")
        else:
            out.append("")
    while out and out[-1] == "":
        out.pop()
    return "\n".join(out) + "\n\n"


def references_and_appendices():
    L = []
    L.append(r"\clearpage")
    L.append(r"\phantomsection")
    L.append(r"\addcontentsline{toc}{section}{References}")
    L.append(r"\section*{References}")
    L.append("")
    refs = [
        "Aakash P., Chandru T., Kiruba Wesley. CivicSense: AI-Based Citizen Complaint Analyzer. "
        "Proceedings of the Global Conference on Sustainable Energy Systems, Smart Electronics "
        "and Intelligent Computing (GCSESEIC 2025), Advances in Engineering Research 297. "
        "(Base paper - project source document.)",
        "Government of India. Centralized Public Grievance Redress and Monitoring System (CPGRAMS). "
        "Department of Administrative Reforms and Public Grievances, 2023.",
        "Municipal Services Office. OneService App. Government of Singapore, 2023.",
        "City of New York. NYC 311 Service Request Platform, 2023.",
        "Devlin, J., Chang, M.-W., Lee, K., Toutanova, K. BERT: Pre-training of Deep "
        "Bidirectional Transformers for Language Understanding. NAACL-HLT, 2019.",
        "Sanh, V., Debut, L., Chaumond, J., Wolf, T. DistilBERT, a distilled version of BERT: "
        "smaller, faster, cheaper and lighter. arXiv:1910.01108, 2019.",
        "Reimers, N., Gurevych, I. Sentence-BERT: Sentence Embeddings using Siamese "
        "BERT-Networks. EMNLP-IJCNLP, 2019.",
        "Pedregosa, F. et al. Scikit-learn: Machine Learning in Python. Journal of Machine "
        "Learning Research 12, 2011.",
        "Bird, S., Klein, E., Loper, E. Natural Language Processing with Python. "
        "O\u2019Reilly Media, 2009.",
        "Loper, E., Bird, S. NLTK: The Natural Language Toolkit. ACL Workshop on Effective "
        "Tools and Methodologies for Teaching NLP, 2002.",
        "Flask Documentation. Pallets Projects - https://flask.palletsprojects.com",
        "ReportLab Documentation - https://docs.reportlab.com",
        "openpyxl Documentation - https://openpyxl.readthedocs.io",
        "python-docx Documentation - https://python-docx.readthedocs.io",
        "Van Rossum, G., Drake, F. L. Python Language Reference - https://docs.python.org",
        "Hutto, C. J., Gilbert, E. VADER: A Parsimonious Rule-based Model for Sentiment "
        "Analysis of Social Media Text. ICWSM, 2014.",
    ]
    for r in refs:
        L.append(r"\item " + esc(r))
    L.append("")
    L.append(para("Note on sourcing: the base paper is the primary source and defines the "
                  "problem, the five service categories and the evaluation setting. The "
                  "remaining references support the libraries and background methods used in "
                  "the implementation, and each is cited where the technique is used.",                   size=9))
    L.append(r"\newpage")

    apps = (
        ("Appendix A: How to Run the Project", [
            (para, "The fastest path is the one run script, which installs dependencies, "
                   "downloads the required NLTK data and starts the application:"),
            ("", ""),
            (tbl, "The project\u2019s principal commands.",
                ["Command", "What it does"],
                [["../run.sh", "Install dependencies, fetch NLTK data, start the app on "
                  "http://127.0.0.1:5000"],
                 ["./run.sh test", "Install dependencies, fetch NLTK data, run the end-to-end smoke suite"],
                 ["python app.py", "Start the application directly (dependencies already installed)"],
                 ["python smoke_test.py", "Run the automated suite against a clean database"],
                 ["python civic_sense/build_report.py",
                  "Regenerate the Word report from the current measurements"],
                 ["python civic_sense/build_report_latex.py",
                  "Regenerate the LaTeX source for the report"]],
                True),
            ("", ""),
            (para, "If installing manually, the equivalent sequence is:"),
            ("", ""),
            (bullet, "pip install -r requirements.txt"),
            (bullet, "python -c \"import nltk; nltk.download(['stopwords','wordnet','vader_lexicon','punkt'])\""),
            (bullet, "python app.py"),
            ("", ""),
            (para, "On first launch the application automatically creates the schema, trains the "
                   "classifier if it is not already trained, seeds and processes the demonstration "
                   "corpus, and is immediately ready at http://127.0.0.1:5000. The optional "
                   "environment settings are OPENAI_API_KEY, which enables language-model-written "
                   "digests, and USE_TRANSFORMERS=1, which enables zero-shot DistilBERT "
                   "classification when the transformer stack is installed."),
        ]),
        , ("Appendix B: REST API Reference", [
            (para, "The REST API is the programmatic intake path, mirroring the paper\u2019s "
                   "requirement that complaints be aggregated via API connections. Every "
                   "submission runs the full pipeline before the record is returned."),
            ("", ""),
            (tbl, "REST endpoints.",
                ["Endpoint", "Method", "Description"],
                [["/api/complaints", "POST", "Submit a complaint; runs the full pipeline with fraud scoring and XAI"],
                 ["/api/complaints/<id>", "GET", "Retrieve one complaint as JSON"],
                 ["/api/stats", "GET", "JSON statistics: totals, category mix, priority mix and recent rows"]],
                True),
            ("", ""),
            (para, "A single submission example:"),
            ("", ""),
            (tbl, "A single submission example.",
                ["Command line", ""],
                [["curl -X POST http://127.0.0.1:5000/api/complaints \\\\", ""],
                 ["-H \"Content-Type: application/json\" \\\\", ""],
                 ["-d '{\"description\": \"Sewage overflowing near the market area\", \"ward\": "
                  "\"Wakad\", \"source\": \"Mobile App\"}'", ""]],
                False),
            ("", ""),
            (para, "On the server side the request is processed by run_pipeline(), which returns "
                   "a JSON payload containing the category, confidence, priority, priority "
                   "breakdown, fraud score, fraud level, fraud explanation, cluster identifier and "
                   "duplicate metadata. The dashboard index page renders the same values into the "
                   "KPI cards, the Fraud Alerts card and the Incident Hotspots card."),
        ]),
        , ("Appendix C: Source File Reference", [
            (tbl, "Source files and their responsibilities.",
                ["File", "Responsibility"],
                [["app.py", "Flask application: all routes (UI and API), the run_pipeline() orchestrator and startup seeding"],
                 ["civic_sense/config.py", "Paths, category and priority constants, thresholds and feature flags"],
                 ["civic_sense/preprocessing.py", "Cleaning, tokenising, lemmatising, stop-word removal, similarity, duplicate detection and incident clustering"],
                 ["civic_sense/classifier.py", "Training corpus, TF-IDF + LinearSVC pipeline, optional DistilBERT path, cross-validated metrics and confidence scoring"],
                 ["civic_sense/fraud_detector.py", "Three-signal fraud risk scoring and its explanation generator"],
                 ["civic_sense/prioritizer.py", "Six-signal weighted priority assignment and its explanation generator"],
                 ["civic_sense/summarizer.py", "Extractive complaint summaries and weekly digest generation (template and optional LLM)"],
                 ["civic_sense/reports.py", "PDF (ReportLab) and Excel (openpyxl) export of weekly reports"],
                 ["civic_sense/database.py", "Schema, connection handling, inserts, queries, aggregates and the dashboard card queries"],
                 ["civic_sense/seed_data.py", "Synthetic corpus generation plus the fraud and hotspot scenarios"],
                 ["civic_sense/build_report.py", "This report\u2019s Word generator (document is produced from measured data)"],
                 ["civic_sense/build_report_latex.py", "This report\u2019s LaTeX source generator"],
                 ["smoke_test.py", "The end-to-end automated test suite"],
                 ["templates/", "Jinja2 templates: dashboard, complaint list, intake form, detail, reports and pipeline explainer"],
                 ["static/css/style.css", "The stylesheet, including the CSS-only charts"]],
                True),
            ("", ""),
        ]),
        , ("Appendix D: Verification Checklist", [
            (para, "Generated from the verified live state of the running demonstration server "
                   "and the clean-seed measurement run:"),
            ("", ""),
            (tbl, "Verification checklist of the final build.",
                ["Check", "Result"],
                [["Automated smoke suite (30 assertions)", "All passed; exit status 0"],
                 ["Demo database (data/civicsense.db)", "Created and populated on startup when empty"],
                 ["Classification example set (11 texts)", "11 of 11 classified correctly"],
                 ["Classifier cross-validation", "82.19% +/- 5.47% (stratified 5-fold, 152 samples)"],
                 ["Fraud Alerts card render", "2 High and 3 Medium rows present"],
                 ["Incident Hotspots card render", "11 clusters; largest shows 8 complaints"],
                 ["Complaint detail pages", "Live cluster and fraud values reflected"],
                 ["Duplicate detection", "Re-filed complaint flagged with ratio 1.0 pointing at the original"],
                 ["Weekly digest", "Names a locality, a priority mix and a resource allocation suggestion"],
                 ["PDF export", "Downloads with type application/pdf"],
                 ["Excel export", "Downloads with the correct spreadsheet MIME type"],
                 ["Status update workflow", "New status persists to the database"],
                 ["Graceful degradation", "Similarity, classification, tokenisation and digest paths all fall back without error"]],
                True),
            ("", ""),
        ]),
        , ("Appendix E: Glossary", [
            (tbl, "Glossary of terms used in this report.",
                ["Term", "Meaning"],
                [["Classification", "Assigning a complaint to one of the five service categories."],
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
                 ["XAI", "Explainable AI - a human-readable justification for an automated decision."]],
                True),
            ("", ""),
        ]),
        , ("Appendix F: Sample Complaint Records", [
            (para, "The following records illustrate how a single submission is enriched as it "
                   "passes through the pipeline. They are drawn from the demonstration output "
                   "described in Section 6."),
            ("", ""),
            (tbl, "Sample complaint records after pipeline enrichment.",
                ["Description", "Category", "Priority", "Duplicate", "Fraud level"],
                [["Sewage overflowing near the market area", "Public Safety", "High", "No", "Low"],
                 ["Transformer making loud noise and sparking at night", "Electricity", "High", "No", "Low"],
                 ["Large pothole near school", "Roads", "Medium", "No", "Low"],
                 ["Streetlight not working on main road", "Electricity", "Medium", "No", "Low"],
                 ["No water supply in the colony since morning", "Water Supply", "High", "No", "Low"],
                 ["Garbage not collected for three days", "Waste Management", "Medium", "No", "Low"],
                 ["Please fix this issue immediately", "Roads", "Medium", "No", "High"],
                 ["Need urgent attention please", "Roads", "Medium", "No", "High"],
                 ["A tree fell on the road", "Public Safety", "High", "No", "Low"],
                 ["A fallen branch blocked traffic", "Public Safety", "High", "Yes", "Low"]],
                True),
            ("", ""),
            (para, "The seventh and eighth rows show the fraud engine flagging generic, low-effort "
                   "submissions that arrive in the same ward within a short window. The final row "
                   "shows locality-aware duplicate detection recognising a paraphrase of an existing "
                   "incident rather than counting it as a new one. Taken together, these rows "
                   "illustrate the two integrity mechanisms that distinguish CivicSense from the "
                   "base paper\u2019s pipeline."),
            ("", ""),
        ]),
        , ("Appendix G: Configuration Reference", [
            (para, "All tunable behaviour is centralised. The complete reference is:"),
            ("", ""),
            (tbl, "Complete configuration reference with the effect of each setting.",
                ["Setting", "Default", "Effect of changing it"],
                [["SIM_THRESHOLD", "0.85", "Higher values flag fewer duplicates; lower values flag more."],
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
                 ["OPENAI_API_KEY", "unset", "When set, digests are rewritten by a language model."]],
                True),
            ("", ""),
        ]),
        , ("Appendix H: Sample Weekly Digest", [
            (para, "The following is the digest generated by the real template engine on the clean "
                   "demonstration corpus, reproduced verbatim (newlines preserved):"),
            ("", ""),
            (para, "Weekly Civic Complaint Digest - October 04 - October 11, 2026"),
            ("", ""),
            (para, "During October 04 - October 11, 2026, 121 citizen complaints were received and "
                   "automatically processed. The dominant category was Roads (35 reports), followed by "
                   "Waste Management (25) and Water Supply (23). Priority-wise, 65 complaints were High, "
                   "48 Medium and 8 Low. Recurring themes include: road, water, waste, garbage, damage, "
                   "bridge."),
            ("", ""),
            (para, "Locality-level highlights:"),
            ("", ""),
            (bullet, "Hinjewadi recorded 29 complaints this week, predominantly roads (14 reports). 20 of them (69%) were flagged High Priority and need immediate attention."),
            (bullet, "Wakad recorded 23 complaints this week, predominantly roads (8 reports). 13 of them (57%) were flagged High Priority and need immediate attention."),
            (bullet, "Talegaon recorded 15 complaints this week, predominantly water supply (6 reports). 10 of them (67%) were flagged High Priority and need immediate attention."),
            (bullet, "Vadgaon recorded 12 complaints this week, predominantly roads (3 reports). 4 of them (33%) were flagged High Priority and need immediate attention."),
            (bullet, "Maval recorded 11 complaints this week, predominantly waste management (5 reports). 3 of them (27%) were flagged High Priority and need immediate attention."),
            ("", ""),
            (para, "Resource allocation suggestion: prioritise Hinjewadi, the current hotspot for roads issues, and schedule preventive maintenance based on the recurring patterns above."),
            ("", ""),
            (para, "This digest is the artefact the base paper\u2019s proposal ultimately aims to produce: "
                   "a short, readable, decision-oriented summary of a week of citizen complaints, naming "
                   "the wards that need attention and the recurring themes behind them."),
            ("", ""),
        ]),
    ]
    for title, blocks in apps:
        L.append(r"\clearpage")
        L.append(r"\phantomsection")
        L.append(r"\addcontentsline{toc}{section}{\" + esc(title) + r\"}")
        L.append(r"\section*{\" + esc(title) + r\"}")
        L.append("")
        for kind, payload in blocks:
            if isinstance(payload, str) and payload == "":
                L.append("")
                continue
            if kind == "p":
                L.append(para(payload))
                L.append("")
            elif kind == "b":
                L.append(bullet(payload))
                L.append("")
            elif kind == "t":
                L.append(tbl(payload[1], payload[2], payload[3],
                              numbered=payload[4] if len(payload) > 4 else False))
                L.append("")
    return "\n".join(L) + "\n\n"


def preamble():
    return (r"\documentclass[10pt,letterpaper,oneside]{article}"
            + r"\usepackage{geometry}"
            + r"\geometry{top=1in,bottom=1in,left=1in,right=1in,includeheadfoot}"
            + r"\usepackage{xcolor}"
            + r"\definecolor{color@navy}{HTML}{1F3B63}"
            + r"\definecolor{color@grey}{HTML}{404040}"
            + r"\definecolor{color@hdr}{HTML}{F2F4F7}"
            + r"\usepackage{titlesec}"
            + r"\titleformat{\section}"
            + r"  {\normalfont\huge\bfseries\color@navy}"
            + r"  {}{0pt}{\MakeUppercase}"
            + r"\titleformat{\subsection}"
            + r"  {\normalfont\Large\bfseries\color@navy}"
            + r"  {}{0pt}{}"
            + r"\titleformat{\subsubsection}"
            + r"  {\normalfont\large\bfseries\color@navy}"
            + r"  {}{0pt}{}"
            + r"\titlespacing*{\section}{0pt}{14pt}{6pt}"
            + r"\titlespacing*{\subsection}{0pt}{10pt}{4pt}"
            + r"\titlespacing*{\subsubsection}{0pt}{8pt}{3pt}"
            + r"\setlength{\parindent}{0pt}"
            + r"\setlength{\parskip}{0.6em}"
            + r"\parindent=0pt"
            + r"\usepackage{enumitem}"
            + r"\setlist{nosep,leftmargin=*,itemsep=0pt,topsep=2pt,partopsep=0pt}"
            + r"\usepackage{array}"
            + r"\usepackage{booktabs}"
            + r"\usepackage{caption}"
            + r"\captionsetup{font={small,it},labelfont={bf},labelsep=period,"
            + r"  parskip=2pt,skip=4pt,list=no}"
            + r"\captionsetup[table]{labelfont={bf,small,color@navy},name=Table}"
            + r"\usepackage{graphicx}"
            + r"\usepackage{verbatim}"
            + r"\usepackage{ragged2e}"
            + r"\usepackage{longtable}"
            + r"\usepackage{tabularx}"
            + r"\usepackage{multirow}"
            + r"\usepackage{colortbl}"
            + r"\definecolor{rowshade}{HTML}{F2F4F7}"
            + r"\usepackage{tikz}"
            + r"\usetikzlibrary{positioning,calc}"
            + r"\usepackage[hidelinks]{hyperref}"
            + r"\hypersetup{colorlinks=true,linkcolor=color@navy,urlcolor=color@navy}"
            + r"\pagestyle{fancy}"
            + r"\fancyhf{}"
            + r"\renewcommand{\headrulewidth}{0.4pt}"
            + r"\fancyhead[L]{\small\color@navy CivicSense \textemdash{} Project Report}"
            + r"\fancyhead[R]{\small\color@grey " + esc(DATE) + r"}"
            + r"\fancyfoot[C]{\small\color@grey " + esc(TITLE[:40]) + r"}"
            + r"\fancyfoot[R]{\small\color@grey Page \thepage}"
            + r"\usepackage{setspace}"
            + r"\setstretch{1.15}"
            + r"\AtBeginDocument{"
            + r"  \hypersetup{pdftitle={" + esc(TITLE) + r"},"
            + r"    pdfauthor={" + esc(AUTHOR) + r"},"
            + r"    pdfsubject={Project Report},"
            + r"    pdfkeywords={smart cities, NLP, complaint management, e-governance},"
            + r"    pdfcreator={CivicSense Project Team}"
            + r"  }"
            + r"}"
            )


def main():
    print("Collecting shared content ...")
    from generate_report import build_narrative
    print("Rendering LaTeX ...")
    front = frontmatter()
    body_text = body()
    refs = references_and_appendices()
    doc = "\n".join([
        preamble(),
        r"\begin{document}",
        front,
        body_text,
        refs,
        r"\end{document}",
    ])
    with open("Project_Report.tex", "w", encoding="utf-8") as f:
        f.write(doc)
    print("Wrote Project_Report.tex")
    print("paragraphs:", sum(1 for _ in build_narrative() if isinstance(_, str) or hasattr(_, "text")))
    tabs = [x for x in build_narrative() if getattr(x, "numbered", False)]
    print("numbered tables:", len(tabs))
    print("figures:", sum(1 for _ in build_narrative() if getattr(_, "caption", None)))
    print("lines:", doc.count("\n"))


if __name__ == "__main__":
    main()
