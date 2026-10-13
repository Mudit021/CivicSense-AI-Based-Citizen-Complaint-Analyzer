"""PDF & Excel export of weekly civic reports (paper: "automatic generation
in such formats as PDF or Excel")."""
from datetime import datetime
from pathlib import Path

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (Paragraph, SimpleDocTemplate, Spacer, Table,
                                TableStyle)

from .config import REPORTS_DIR, CATEGORIES, PRIORITIES


def _stats_table(stats: dict) -> list:
    rows = [["Metric", "Value"]]
    rows.append(["Total complaints", stats["total"]])
    for p in PRIORITIES:
        rows.append([f"{p} priority", stats["by_priority"].get(p, 0)])
    for c in CATEGORIES:
        rows.append([f"{c} category", stats["by_category"].get(c, 0)])
    return rows


def generate_pdf(report: dict) -> Path:
    """Render a styled PDF report and return its path."""
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = REPORTS_DIR / f"civic_report_{stamp}.pdf"

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("TitleX", parent=styles["Title"], fontSize=16,
                                 textColor=colors.HexColor("#1e2a4a"),
                                 spaceAfter=6 * mm)
    sub_style = ParagraphStyle("SubX", parent=styles["Normal"], fontSize=9,
                               textColor=colors.HexColor("#5b6478"))
    body = ParagraphStyle("BodyX", parent=styles["BodyText"], fontSize=10.5,
                          leading=15, spaceAfter=4 * mm)

    doc = SimpleDocTemplate(str(out), pagesize=A4,
                            leftMargin=18 * mm, rightMargin=18 * mm,
                            topMargin=18 * mm, bottomMargin=18 * mm)
    story = [
        Paragraph("PCU CivicSense — Campus Grievance Intelligence", title_style),
        Paragraph(report["title"], sub_style),
        Paragraph(f"Generated {datetime.now().strftime('%d %B %Y, %H:%M')}",
                  sub_style),
        Spacer(1, 6 * mm),
    ]

    for para in report["summary"].split("\n\n"):
        story.append(Paragraph(para.replace("\n", "<br/>"), body))
    story.append(Spacer(1, 6 * mm))

    table_data = _stats_table(report["stats"])
    table = Table(table_data, colWidths=[70 * mm, 90 * mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e2a4a")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9.5),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.white, colors.HexColor("#f2f4fa")]),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#ccd2e3")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(table)
    doc.build(story)
    return out


def generate_excel(report: dict) -> Path:
    """Render an Excel workbook (Overview / Complaints / Breakdown) and return its path."""
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = REPORTS_DIR / f"civic_report_{stamp}.xlsx"

    rows = report.get("rows", [])
    overview = [
        ["Metric", "Value"],
        ["Report", report["title"]],
        ["Period", f"{report['period_start'][:10]} to {report['period_end'][:10]}"],
        ["Generated", datetime.now().strftime("%d %B %Y %H:%M")],
        ["Total complaints", report["stats"]["total"]],
    ]
    for p in PRIORITIES:
        overview.append([f"{p} priority", report["stats"]["by_priority"].get(p, 0)])
    for c in CATEGORIES:
        overview.append([f"{c} category", report["stats"]["by_category"].get(c, 0)])

    complaints = [
        {
            "ID": r.get("id"),
            "Campus Block": r.get("ward"),
            "Floor": r.get("floor", ""),
            "Room/Facility": r.get("room_number", ""),
            "Sub Location": r.get("sub_location", ""),
            "Source": r.get("source"),
            "Category": r.get("category"),
            "Priority": r.get("priority"),
            "Status": r.get("status"),
            "Title": r.get("title"),
            "Created At": r.get("created_at"),
            "Confidence": r.get("confidence"),
        }
        for r in rows
    ]
    breakdown = [
        {"Category": c, "Count": report["stats"]["by_category"].get(c, 0)}
        for c in CATEGORIES
    ]

    with pd.ExcelWriter(out, engine="openpyxl") as writer:
        pd.DataFrame(overview).to_excel(writer, sheet_name="Overview",
                                        index=False, header=False)
        pd.DataFrame(complaints).to_excel(writer, sheet_name="Complaints",
                                          index=False)
        pd.DataFrame(breakdown).to_excel(writer, sheet_name="Category Breakdown",
                                         index=False)

        ws = writer.sheets["Overview"]
        for col, width in zip("ABCDEFGH", [28, 60, 18, 24, 12, 14, 40, 22, 12]):
            ws.column_dimensions[col].width = width
    return out
