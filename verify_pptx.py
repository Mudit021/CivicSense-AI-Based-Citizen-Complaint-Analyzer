#!/usr/bin/env python3
"""Verify the extended CivicSense presentation.

Checks slide count, all 8 new slide titles, original slides preserved,
and footer numbering.
"""
from pptx import Presentation
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

prs = Presentation("Project_Presentation.pptx")

assert len(prs.slides) == 21, f"Expected 21 slides, got {len(prs.slides)}"

# Collect ALL text per slide (not just first shape's first paragraph)
def slide_text(slide):
    parts = []
    for shape in slide.shapes:
        if shape.has_text_frame:
            for para in shape.text_frame.paragraphs:
                t = para.text.strip()
                if t:
                    parts.append(t)
    return " | ".join(parts)

texts = [slide_text(s) for s in prs.slides]

checks = [
    ("Slide count = 21", len(prs.slides) == 21),
    ("Slide 1: Title", "Artificial Intelligence and Data Science" in texts[0]),
    ("Slide 2: Content/TOC", "Content:" in texts[1]),
    ("Slide 3: Introduction", "Introduction" in texts[2] and "Municipalities" in texts[2]),
    ("Slide 4: Problem Statement", "Problem Statement" in texts[3]),
    ("Slide 5: Objectives", "Objectives" in texts[4]),
    ("Slide 6: Base Paper Details", "Base Paper Details" in texts[5]),
    ("Slide 7: Literature Survey", "Literature Survey" in texts[6]),
    ("Slide 8: Research Gap", "Research Gap" in texts[7]),
    ("Slide 9: Existing System", "Existing System" in texts[8]),
    ("Slide 10: Proposed System", "Six-Stage AI Pipeline" in texts[9]),
    ("Slide 11: Implementation Highlights", "Implementation Highlights" in texts[10]),
    # NEW slides
    ("Slide 12: Tech Stack & Environment", "Tech Stack & Environment" in texts[11]),
    ("Slide 13: PyTorch Environment Fix", "PyTorch Environment Fix" in texts[12]),
    ("Slide 14: Full Pipeline Walkthrough", "Full Pipeline Walkthrough" in texts[13]),
    ("Slide 15: Classifier TF-IDF + LinearSVC", "Classifier: TF-IDF + LinearSVC" in texts[14]),
    ("Slide 16: Optional DistilBERT Path", "Optional DistilBERT Transformer Path" in texts[15]),
    ("Slide 17: Fraud Detection Module", "Fraud Detection Module" in texts[16]),
    ("Slide 18: System Architecture & Deployment", "System Architecture & Deployment" in texts[17]),
    ("Slide 19: Updated Results & Validation", "Updated Results & Validation" in texts[18]),
    ("Slide 20: Results & Outcomes", "Results & Outcomes" in texts[19]),
    ("Slide 21: Conclusion", "Conclusion" in texts[20]),
    # Content checks on specific new slides
    ("Slide 13 has Problem box", "THE PROBLEM" in texts[12]),
    ("Slide 13 has Fix box", "THE FIX" in texts[12]),
    ("Slide 13 has Verification box", "Verification" in texts[12]),
    ("Slide 13 mentions torch 2.14.1", "2.14.1" in texts[12]),
    ("Slide 19 mentions 29/29 passed", "29/29" in texts[18] or "29 / 29" in texts[18]),
    ("Slide 19 mentions exit code 0", "exit code 0" in texts[18]),
    ("Slide 18 has architecture flow", "Citizen" in texts[17] and "SQLite" in texts[17]),
    # Footer numbering on new slide
    ("Slide 12 footer says 14 / 21", "14 / 21" in texts[11]),
    ("Slide 13 footer says 15 / 21", "15 / 21" in texts[12]),
    ("Slide 19 footer says 21 / 21", "21 / 21" in texts[18]),
]

all_pass = True
for name, ok in checks:
    status = "PASS" if ok else "FAIL"
    if not ok:
        all_pass = False
    print(f"  [{status}] {name}")

print()
if all_pass:
    print("ALL VERIFICATION CHECKS PASSED")
else:
    print("SOME CHECKS FAILED — see above")
    sys.exit(1)
