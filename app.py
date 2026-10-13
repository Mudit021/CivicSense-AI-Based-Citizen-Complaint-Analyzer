"""CivicSense — Flask web application.

Run:  python app.py   (then open http://127.0.0.1:5000)

Implements the six-stage pipeline from the base paper and exposes it through:
  - an officer dashboard (decision support)
  - a complaint intake form + REST API (data collection)
  - filterable complaint lists (classification / prioritisation results)
  - weekly digest reports with PDF & Excel export
"""
import json
from datetime import datetime

from flask import (Flask, abort, jsonify, redirect, render_template, request,
                   send_file, url_for)

from civic_sense import database
from civic_sense.classifier import load_classifier, classify_text, refine_category_with_vision
from civic_sense.config import (CATEGORIES, PRIORITIES, SOURCES, STATUSES,
                                WARDS, CAMPUS_BLOCKS, FLOORS, PCU_COORDINATES,
                                UNIVERSITY_NAME, CAMPUS_LOCATION, TREND_DAYS)
from civic_sense.preprocessing import find_duplicate
from civic_sense.prioritizer import assign_priority, priority_explanation
from civic_sense.fraud_detector import check_complaint
from civic_sense.hotspot_analyzer import assign_coordinates, get_hotspot_summary
from civic_sense.image_analyzer import analyze_image, find_nearest_building, find_image_duplicate
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
def run_pipeline(title: str, description: str, ward: str, source: str,
                 created_at: str = None, floor: str = "", room_number: str = "", sub_location: str = "",
                 user_lat: float = None, user_lon: float = None, image_file = None):
    """preprocessing -> text + vision classification -> visual dedup -> multi-factor prioritization -> fraud detection -> geo mapping."""
    created_at = created_at or datetime.now().isoformat(timespec="seconds")

    # 1. Textual deduplication
    dup = find_duplicate(description)
    is_dup = bool(dup)
    dup_of = dup[0] if dup else None
    dup_ratio = dup[1] if dup else None

    # 2. Base NLP classification
    raw_category, raw_conf = classify_text(classifier, description)

    # 3. Computer vision & image analysis (runs before final prioritization)
    img_res = analyze_image(image_file, category=raw_category, description=description) if image_file else {"has_image": False}
    image_url = img_res.get("image_url", "") if (img_res.get("has_image") and img_res.get("is_valid")) else ""
    image_analysis = json.dumps(img_res) if img_res.get("has_image") else ""

    # 4. Multimodal Category Refinement & Confidence Calibration (Photo improves accuracy!)
    category, confidence = refine_category_with_vision(raw_category, raw_conf, img_res)

    # 5. Visual duplicate detection (dHash perceptual similarity)
    if not is_dup and img_res.get("has_image") and img_res.get("perceptual_hash"):
        img_dup, img_dup_id, dist = find_image_duplicate(img_res["perceptual_hash"], ward)
        if img_dup:
            is_dup = True
            dup_of = img_dup_id
            dup_ratio = round(max(0.88, 1.0 - (dist / 16.0)), 2)

    # 6. Frequency & similar complaints in location
    similar = database.similar_complaints(ward, category)

    # 7. Priority assignment (Photo evidence directly boosts urgency & severity scoring!)
    priority, score, breakdown = assign_priority(description, category, ward,
                                                 created_at, similar, image_result=img_res)
    explanation = priority_explanation(breakdown, score)

    # 8. Geolocation resolution: GPS auto-detect > Image EXIF GPS > Campus GIS assignment
    geo_source = "campus_gis"
    if user_lat is not None and user_lon is not None:
        lat, lon = round(float(user_lat), 6), round(float(user_lon), 6)
        geo_source = "gps_auto"
    elif img_res.get("has_image") and img_res.get("is_valid") and img_res.get("exif", {}).get("has_gps"):
        lat, lon = img_res["exif"]["lat"], img_res["exif"]["lon"]
        geo_source = "exif_gps"
    else:
        lat, lon = assign_coordinates(ward, description, floor=floor, room=room_number)

    # 9. Fraud & anomaly detection (calibrated with verified photo authenticity)
    is_susp, susp_score, susp_reason = check_complaint(description, similar)
    if is_susp and img_res.get("has_image") and img_res.get("is_valid") and ("Sharp" in img_res.get("sharpness_label", "")):
        # Verified clear photo evidence mitigates false-positive anomaly score
        if "Isolation Forest" in susp_reason and not ("commercial" in susp_reason.lower() or "spam" in susp_reason.lower()):
            susp_score = max(0.0, round(susp_score - 0.4, 2))
            if susp_score < 0.5:
                is_susp = False
                susp_reason = "Statistical variance cleared by verified authentic photo evidence."

    return {
        "category": category,
        "confidence": confidence,
        "priority": priority,
        "score": score,
        "breakdown": breakdown,
        "explanation": explanation,
        "is_duplicate": is_dup,
        "duplicate_of": dup_of,
        "duplicate_ratio": dup_ratio,
        "is_suspicious": is_susp,
        "suspicion_score": susp_score,
        "suspicion_reason": susp_reason,
        "lat": lat,
        "lon": lon,
        "floor": floor,
        "room_number": room_number,
        "sub_location": sub_location,
        "image_url": image_url,
        "image_analysis": image_analysis,
        "image_result": img_res,
        "geo_source": geo_source,
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
    hotspots = get_hotspot_summary(wards)
    map_incidents = database.get_map_incidents(150)

    # Latest digest for the hero card
    latest_digest = None
    if reports:
        latest_digest = reports[0]["summary"].split("\n")[0]

    max_trend = max([c for _, c in trend] + [1])
    max_ward = max([w["total"] for w in wards] + [1])
    max_cat = max(list(stats["by_category"].values()) + [1])

    return render_template(
        "index.html",
        stats=stats, trend=trend, wards=wards, recent=recent,
        reports=reports, latest_digest=latest_digest,
        max_trend=max_trend, max_ward=max_ward, max_cat=max_cat,
        categories=CATEGORIES, priorities=PRIORITIES, keywords=keywords,
        metrics=MODEL_METRICS, seeded=_seeded,
        hotspots=hotspots, map_incidents=map_incidents,
        campus_blocks=CAMPUS_BLOCKS, pcu_coords=PCU_COORDINATES,
        university_name=UNIVERSITY_NAME, campus_location=CAMPUS_LOCATION,
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
        "floor": request.args.get("floor", ""),
        "status": request.args.get("status", ""),
        "is_suspicious": request.args.get("is_suspicious", ""),
        "q": request.args.get("q", ""),
    }
    rows = database.get_complaints(**{k: v for k, v in filters.items() if v != ""})
    return render_template("complaints.html", rows=rows, filters=filters,
                           categories=CATEGORIES, priorities=PRIORITIES,
                           wards=CAMPUS_BLOCKS, campus_blocks=CAMPUS_BLOCKS,
                           floors=FLOORS, statuses=STATUSES)


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
        ward = request.form.get("ward", CAMPUS_BLOCKS[0])
        floor = request.form.get("floor", "").strip()
        room_number = request.form.get("room_number", "").strip()
        sub_location = request.form.get("sub_location", "").strip()
        source = request.form.get("source", "Student Portal")

        # Location auto-detect coordinates
        raw_lat = request.form.get("user_lat", "").strip()
        raw_lon = request.form.get("user_lon", "").strip()
        user_lat, user_lon = None, None
        try:
            if raw_lat and raw_lon:
                user_lat, user_lon = float(raw_lat), float(raw_lon)
        except (ValueError, TypeError):
            user_lat, user_lon = None, None

        # Image file upload
        image_file = request.files.get("image")

        if not description:
            return render_template("new_complaint.html", error="Please describe the issue.",
                                    wards=CAMPUS_BLOCKS, campus_blocks=CAMPUS_BLOCKS,
                                    sources=SOURCES, floors=FLOORS)
        result = run_pipeline(title or description[:60], description, ward, source,
                              floor=floor, room_number=room_number, sub_location=sub_location,
                              user_lat=user_lat, user_lon=user_lon, image_file=image_file)
        saved = database.insert_complaint({
            "source": source, "ward": ward,
            "floor": floor, "room_number": room_number, "sub_location": sub_location,
            "category": result["category"],
            "title": title or " ".join(description.split()[:6]) + "...",
            "description": description, "priority": result["priority"],
            "confidence": result["confidence"],
            "is_duplicate": result["is_duplicate"],
            "duplicate_of": result["duplicate_of"],
            "is_suspicious": result["is_suspicious"],
            "suspicion_score": result["suspicion_score"],
            "suspicion_reason": result["suspicion_reason"],
            "lat": result["lat"],
            "lon": result["lon"],
            "image_url": result["image_url"],
            "image_analysis": result["image_analysis"],
            "geo_source": result["geo_source"],
            "created_at": datetime.now().isoformat(timespec="seconds"),
        })
    return render_template("new_complaint.html", result=result, saved=saved,
                           wards=CAMPUS_BLOCKS, campus_blocks=CAMPUS_BLOCKS,
                           sources=SOURCES, categories=CATEGORIES, floors=FLOORS)


# ---------------------------------------------------------------------------
# Location auto-detection API
# ---------------------------------------------------------------------------
@app.route("/api/detect-location", methods=["POST"])
def api_detect_location():
    """Auto-detect nearest campus building/block for user browser GPS coordinates."""
    data = request.get_json(silent=True) or {}
    try:
        lat = float(data.get("lat"))
        lon = float(data.get("lon"))
    except (TypeError, ValueError):
        return jsonify({"error": "Valid numeric lat and lon coordinates are required"}), 400

    info = find_nearest_building(lat, lon)
    return jsonify(info), 200


# ---------------------------------------------------------------------------
# REST API (data collection via API connections — paper section 3.1)
# ---------------------------------------------------------------------------
@app.route("/api/complaints", methods=["POST"])
def api_submit():
    if request.is_json:
        data = request.get_json(silent=True) or {}
        image_file = data.get("image")
    else:
        data = request.form.to_dict()
        image_file = request.files.get("image") or data.get("image")

    description = (data.get("description") or "").strip()
    if not description:
        return jsonify({"error": "description is required"}), 400
    ward = data.get("ward", CAMPUS_BLOCKS[0])
    if ward not in CAMPUS_BLOCKS and ward not in WARDS:
        return jsonify({"error": f"ward must be one of {CAMPUS_BLOCKS}"}), 400
    source = data.get("source", "Student Portal")
    if source not in SOURCES:
        return jsonify({"error": f"source must be one of {SOURCES}"}), 400
    floor = data.get("floor", "")
    room_number = data.get("room_number", "")
    sub_location = data.get("sub_location", "")

    # Auto GPS detection inputs
    raw_lat = data.get("lat") or data.get("user_lat")
    raw_lon = data.get("lon") or data.get("user_lon")
    user_lat, user_lon = None, None
    try:
        if raw_lat is not None and raw_lon is not None and str(raw_lat).strip() and str(raw_lon).strip():
            user_lat, user_lon = float(raw_lat), float(raw_lon)
    except (ValueError, TypeError):
        user_lat, user_lon = None, None

    result = run_pipeline(data.get("title", ""), description, ward, source,
                          floor=floor, room_number=room_number, sub_location=sub_location,
                          user_lat=user_lat, user_lon=user_lon, image_file=image_file)
    cid = database.insert_complaint({
        "source": source, "ward": ward,
        "floor": floor, "room_number": room_number, "sub_location": sub_location,
        "category": result["category"],
        "title": (data.get("title") or " ".join(description.split()[:6]) + "..."),
        "description": description, "priority": result["priority"],
        "confidence": result["confidence"],
        "is_duplicate": result["is_duplicate"],
        "duplicate_of": result["duplicate_of"],
        "is_suspicious": result["is_suspicious"],
        "suspicion_score": result["suspicion_score"],
        "suspicion_reason": result["suspicion_reason"],
        "lat": result["lat"],
        "lon": result["lon"],
        "image_url": result["image_url"],
        "image_analysis": result["image_analysis"],
        "geo_source": result["geo_source"],
        "created_at": datetime.now().isoformat(timespec="seconds"),
    })
    return jsonify({"id": cid, **result}), 201


@app.route("/api/hotspots")
def api_hotspots():
    wards = database.ward_counts()
    return jsonify(get_hotspot_summary(wards))


@app.route("/api/map-incidents")
def api_map_incidents():
    return jsonify(database.get_map_incidents(250))


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


@app.template_filter("from_json")
def from_json(value):
    """Safely deserialize JSON string to dictionary in Jinja templates."""
    if not value:
        return {}
    if isinstance(value, dict):
        return value
    try:
        return json.loads(value)
    except Exception:
        return {}



if __name__ == "__main__":
    print("=" * 62)
    print("  CivicSense — AI-Based Citizen Complaint Analyzer")
    print("  Open:  http://127.0.0.1:5000")
    print("=" * 62)
    app.run(debug=True, host="127.0.0.1", port=5000)
