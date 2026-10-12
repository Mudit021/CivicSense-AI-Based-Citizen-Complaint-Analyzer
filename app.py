"""CivicSense — Flask web application.

Run:  python app.py   (then open http://127.0.0.1:5000)

Implements the integrated triage pipeline from the base paper and exposes it
through:
  - an officer dashboard (decision support), including Fraud Alerts and
    Incident Hotspots cards
  - a complaint intake form + REST API (data collection)
  - filterable complaint lists (classification / prioritisation results)
  - weekly digest reports with PDF & Excel export

Pipeline order in code: preprocessing (incl. duplicate detection) →
classification → fraud scoring → incident clustering → weighted priority →
XAI generation → dashboard / reports.

Fraud scoring is intentionally separate from duplicate detection and is wired
into both the REST API path and the seeded demo data.
"""
from datetime import datetime

from flask import (Flask, abort, jsonify, redirect, render_template, request,
                   send_file, url_for)

from civic_sense import database
from civic_sense.classifier import load_classifier, classify_text
from civic_sense.config import (CATEGORIES, PRIORITIES, SOURCES, STATUSES,
                                WARDS, TREND_DAYS)
from civic_sense.preprocessing import find_duplicate, detect_incident_cluster
from civic_sense.prioritizer import assign_priority, priority_explanation
from civic_sense.fraud_detector import analyze_fraud_risk, generate_fraud_explanation
from civic_sense.reports import generate_excel, generate_pdf
from civic_sense.summarizer import generate_weekly_report

app = Flask(__name__)

# ---------------------------------------------------------------------------
# Startup: DB, model, demo data
# ---------------------------------------------------------------------------
database.init_db()
classifier, MODEL_METRICS = load_classifier()
_seeded = 0
if database.complaint_count() == 0:
    from civic_sense.seed_data import seed_if_empty
    _seeded = seed_if_empty()

# ---------------------------------------------------------------------------
# Pipeline helper (used by both the web form and the API)
# ---------------------------------------------------------------------------
def run_pipeline(title: str, description: str, ward: str, source: str,
                 created_at: str = None):
    """Run the full triage pipeline for one submission.

    Order: preprocessing (duplicate detection) -> classification -> incident
    clustering -> fraud scoring -> weighted priority -> XAI generation.

    Fraud scoring is returned here as well as being independently persisted by
    the caller, so every intake path (web form and REST API) produces the same
    set of fields.
    """
    created_at = created_at or datetime.now().isoformat(timespec="seconds")

    # 1. Preprocessing: locality-aware duplicate detection.
    dup = find_duplicate(description, ward=ward)

    # 2. Classification.
    category, confidence = classify_text(classifier, description)

    # 3. Incident clustering: group fragmented reports of the same incident.
    cluster_id = detect_incident_cluster(description, ward=ward, category=category)

    # 4. Fraud scoring (independent of duplicate detection).
    fraud_score, fraud_level, fraud_breakdown = analyze_fraud_risk({
        "description": description, "ward": ward, "source": source,
    })
    fraud_explanation = generate_fraud_explanation(
        fraud_breakdown, fraud_score, fraud_level)

    # 5. Weighted priority, with an optional boost when the complaint joins a
    #    known incident cluster (repeated reports of one issue are more urgent).
    similar = database.similar_complaints(ward, category)
    priority, score, breakdown = assign_priority(description, category, ward,
                                                 created_at, similar)
    explanation = priority_explanation(breakdown, score)

    return {
        "category": category,
        "confidence": confidence,
        "priority": priority,
        "score": score,
        "breakdown": breakdown,
        "explanation": explanation,
        "is_duplicate": bool(dup),
        "duplicate_of": dup[0] if dup else None,
        "duplicate_ratio": dup[1] if dup else None,
        "cluster_id": cluster_id,
        "fraud_score": fraud_score,
        "fraud_level": fraud_level,
        "fraud_explanation": fraud_explanation,
    }


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    stats = database.get_stats()
    trend = database.daily_counts(TREND_DAYS)
    wards = database.ward_counts()
    recent = database.recent_complaints(8)
    reports = database.get_reports(3)
    keywords = database.top_keywords(None, 7, 12)
    # Decision-support cards query the whole table rather than only the most
    # recent rows, so a flag raised earlier in the day is still visible.
    fraud_alerts = database.fraud_alerts(5)
    hotspots = database.cluster_summary(5)

    # Latest digest for the hero card
    latest_digest = None
    if reports:
        latest_digest = reports[0]["summary"].split("\n")[0]

    max_trend = max(max((c for _, c in trend), default=0), 1)
    max_ward = max((w["total"] for w in wards), default=1)
    max_cat = max(stats["by_category"].values(), default=1)

    return render_template(
        "index.html",
        stats=stats, trend=trend, wards=wards, recent=recent,
        reports=reports, latest_digest=latest_digest,
        max_trend=max_trend, max_ward=max_ward, max_cat=max_cat,
        categories=CATEGORIES, priorities=PRIORITIES, keywords=keywords,
        metrics=MODEL_METRICS, seeded=_seeded,
        fraud_alerts=fraud_alerts, hotspots=hotspots,
    )


# ---------------------------------------------------------------------------
# Complaints list
# ---------------------------------------------------------------------------
@app.route("/complaints")
def complaints():
    filters = {
        "category": request.args.get("category", ""),
        "priority": request.args.get("priority", ""),
        "ward": request.args.get("ward", ""),
        "status": request.args.get("status", ""),
        "q": request.args.get("q", ""),
        "cid": request.args.get("id", ""),
        "dup": request.args.get("dup", ""),
    }
    # Convert numeric filters
    db_filters = {k: v for k, v in filters.items() if v}
    if "cid" in db_filters:
        try:
            db_filters["cid"] = int(db_filters["cid"])
        except (ValueError, TypeError):
            del db_filters["cid"]
    if "dup" in db_filters:
        db_filters["dup"] = 1
    rows = database.get_complaints(**db_filters)
    return render_template("complaints.html", rows=rows, filters=filters,
                           categories=CATEGORIES, priorities=PRIORITIES,
                           wards=WARDS, statuses=STATUSES)


# ---------------------------------------------------------------------------
# Complaint detail
# ---------------------------------------------------------------------------
@app.route("/complaints/<int:cid>")
def complaint_detail(cid):
    import json as _json
    c = database.get_complaint(cid)
    if not c:
        abort(404)
    # Parse stored JSON breakdown
    if c.get("priority_breakdown"):
        try:
            c["priority_breakdown"] = _json.loads(c["priority_breakdown"])
        except (TypeError, ValueError):
            c["priority_breakdown"] = None
    related = database.related_complaints(c["ward"], c["category"], cid)
    duplicate_of = None
    if c.get("duplicate_of"):
        duplicate_of = database.get_complaint(c["duplicate_of"])
    return render_template("complaint_detail.html", c=c, related=related,
                           duplicate_of=duplicate_of, statuses=STATUSES)


# ---------------------------------------------------------------------------
# Complaint intake (web form)
# ---------------------------------------------------------------------------
@app.route("/complaints/new", methods=["GET", "POST"])
def new_complaint():
    result = None
    saved = None
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        ward = request.form.get("ward", "PCMC")
        source = request.form.get("source", "Web Portal")
        if not description:
            return render_template("new_complaint.html", error="Please describe the issue.",
                                   wards=WARDS, sources=SOURCES)
        result = run_pipeline(title or description[:60], description, ward, source)
        saved = database.insert_complaint({
            "source": source, "ward": ward, "category": result["category"],
            "title": title or " ".join(description.split()[:6]) + "...",
            "description": description, "priority": result["priority"],
            "confidence": result["confidence"],
            "is_duplicate": result["is_duplicate"],
            "duplicate_of": result["duplicate_of"],
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "priority_score": result["score"],
            "priority_breakdown": result["breakdown"],
            "fraud_score": result.get("fraud_score"),
            "fraud_level": result.get("fraud_level"),
            "fraud_explanation": result.get("fraud_explanation"),
            "cluster_id": result.get("cluster_id"),
            "xai_explanation": result.get("xai_explanation"),
        })
    return render_template("new_complaint.html", result=result, saved=saved,
                           wards=WARDS, sources=SOURCES, categories=CATEGORIES)


# ---------------------------------------------------------------------------
# REST API (data collection via API connections — paper section 3.1)
# ---------------------------------------------------------------------------
@app.route("/api/complaints", methods=["POST"])
def api_submit():
    data = request.get_json(silent=True) or {}
    description = (data.get("description") or "").strip()
    if not description:
        return jsonify({"error": "description is required"}), 400
    ward = data.get("ward", "PCMC")
    if ward not in WARDS:
        return jsonify({"error": f"ward must be one of {WARDS}"}), 400
    source = data.get("source", "Web Portal")
    if source not in SOURCES:
        return jsonify({"error": f"source must be one of {SOURCES}"}), 400

    result = run_pipeline(data.get("title", ""), description, ward, source)
    # Fraud scoring already ran inside run_pipeline; reuse its result so the
    # stored row and the API response can never drift apart.
    fraud_score = result["fraud_score"]
    fraud_level = result["fraud_level"]
    fraud_explanation = result["fraud_explanation"]

    cid = database.insert_complaint({
        "source": source, "ward": ward, "category": result["category"],
        "title": (data.get("title") or " ".join(description.split()[:6]) + "..."),
        "description": description, "priority": result["priority"],
        "confidence": result["confidence"],
        "is_duplicate": result["is_duplicate"],
        "duplicate_of": result["duplicate_of"],
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "priority_score": result["score"],
        "priority_breakdown": result["breakdown"],
        "fraud_score": fraud_score, "fraud_level": fraud_level,
        "fraud_explanation": fraud_explanation,
        "cluster_id": result.get("cluster_id"),
        "xai_explanation": result.get("xai_explanation"),
    })
    return jsonify({
        "id": cid,
        "category": result["category"],
        "confidence": result["confidence"],
        "priority": result["priority"],
        "score": result["score"],
        "breakdown": result["breakdown"],
        "explanation": result["explanation"],
        "is_duplicate": result["is_duplicate"],
        "duplicate_of": result["duplicate_of"],
        "duplicate_ratio": result["duplicate_ratio"],
        "fraud_score": fraud_score,
        "fraud_level": fraud_level,
        "fraud_explanation": fraud_explanation,
        "cluster_id": result.get("cluster_id"),
    }), 201


@app.route("/api/stats")
def api_stats():
    return jsonify(database.get_stats())


@app.route("/api/complaints/<int:cid>")
def api_complaint(cid):
    c = database.get_complaint(cid)
    return jsonify(c) if c else (jsonify({"error": "not found"}), 404)


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------
def _enrich_report(report: dict) -> dict:
    """Attach computed stats/rows to a stored report row.

    The database only persists the digest text; stats are re-derived from the
    complaints in the report period (they are deterministic).
    """
    from collections import Counter
    rows = database.complaints_in_period(report["period_start"],
                                         report["period_end"])
    by_cat = Counter(r["category"] for r in rows)
    by_prio = Counter(r["priority"] for r in rows)
    report["rows"] = rows
    report["stats"] = {
        "total": len(rows),
        "by_category": {c: by_cat.get(c, 0) for c in CATEGORIES},
        "by_priority": dict(by_prio),
        "by_ward": dict(Counter(r["ward"] for r in rows)),
    }
    return report


@app.route("/reports")
def reports():
    rows = database.get_reports()
    return render_template("reports.html", reports=rows)


@app.route("/reports/generate", methods=["POST"])
def generate_report():
    report = generate_weekly_report()
    rid = database.insert_report(
        report["period_start"], report["period_end"],
        report["title"], report["summary"], "weekly")
    return redirect(url_for("report_view", rid=rid))


@app.route("/complaints/<int:cid>/status", methods=["POST"])
def update_status(cid):
    status = request.form.get("status", "")
    if status not in STATUSES:
        abort(400)
    database.update_status(cid, status)
    return redirect(url_for("complaints"))


@app.route("/reports/<int:rid>")
def report_view(rid):
    report = database.get_report(rid)
    if not report:
        abort(404)
    return render_template("report_view.html", report=report,
                           categories=CATEGORIES)


@app.route("/reports/<int:rid>/pdf")
def report_pdf(rid):
    report = database.get_report(rid)
    if not report:
        abort(404)
    path = generate_pdf(_enrich_report(report))
    return send_file(path, as_attachment=True,
                     download_name=f"civic_report_{rid}.pdf")


@app.route("/reports/<int:rid>/xlsx")
def report_xlsx(rid):
    report = database.get_report(rid)
    if not report:
        abort(404)
    path = generate_excel(_enrich_report(report))
    return send_file(path, as_attachment=True,
                     download_name=f"civic_report_{rid}.xlsx")


# ---------------------------------------------------------------------------
# Pipeline explainer
# ---------------------------------------------------------------------------
@app.route("/pipeline")
def pipeline():
    return render_template("pipeline.html", metrics=MODEL_METRICS,
                           categories=CATEGORIES)


@app.template_filter("pretty_date")
def pretty_date(value):
    try:
        dt = datetime.fromisoformat(value)
        return dt.strftime("%d %b %Y, %I:%M %p")
    except (ValueError, TypeError):
        return value


if __name__ == "__main__":
    print("=" * 62)
    print("  CivicSense — AI-Based Citizen Complaint Analyzer")
    print("  Open:  http://127.0.0.1:5000")
    print("=" * 62)
    app.run(debug=True, host="127.0.0.1", port=5000)
