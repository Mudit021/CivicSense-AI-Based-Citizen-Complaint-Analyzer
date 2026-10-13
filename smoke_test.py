"""End-to-end smoke test for CivicSense.

Exercises the whole pipeline through the Flask test client:
model training, demo seeding, dashboard, filtering, intake (web + API),
weekly report generation, and PDF/Excel export.
Run:  python smoke_test.py
"""
import sys
from datetime import datetime

# Make console output encoding-safe (the digest text contains unicode symbols).
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass

from app import app, classifier, _seeded

client = app.test_client()
fails = []


def check(label, ok, extra=""):
    status = "PASS" if ok else "FAIL"
    print(f"  [{status}] {label} {extra}")
    if not ok:
        fails.append(label)


print(f"Seeded complaints: {_seeded}")

# --- core pipeline sanity -------------------------------------------------
for text, want_cat in [
    ("Projector screen is flickering and HDMI cable damaged in classroom", "Classroom & Lab Infrastructure"),
    ("Hot water geyser not working in hostel bathroom wing", "Hostel & Residential Life"),
    ("Short circuit and sparking electrical wire near switchboard", "Electricity & Maintenance"),
    ("No running water supply in washroom and choked flush", "Water Supply & Washrooms"),
    ("Undercooked rice and stale food served at the canteen counter", "Canteen & Food Quality"),
    ("Basement underground parking lights are completely off and dark", "Campus Safety & Parking"),
]:
    cat, conf = classifier(text)
    check(f"classify: {text[:40]!r}", cat == want_cat,
          f"-> {cat} ({conf})")

# --- web pages -------------------------------------------------------------
for path in ["/", "/complaints", "/complaints?priority=High&ward=Block%20A",
             "/complaints/new", "/reports", "/pipeline"]:
    r = client.get(path)
    check(f"GET {path}", r.status_code == 200, f"({r.status_code})")

# --- intake via web form ----------------------------------------------------
r = client.post("/complaints/new", data={
    "title": "Broken projector in CS Lab",
    "description": "Projector is not turning on and screen is blank in Block A Lab 3",
    "ward": "Block A", "floor": "1st Floor", "room_number": "Lab 3",
    "sub_location": "Computing Wing", "source": "Student Portal"}, follow_redirects=False)
check("POST /complaints/new", r.status_code == 200, f"({r.status_code})")

# --- intake via REST API -----------------------------------------------------
r = client.post("/api/complaints", json={
    "description": "Elevator is making loud grinding noises and sparking near switchboard",
    "ward": "Block B", "floor": "2nd Floor", "room_number": "Lift Lobby",
    "source": "PCU Mobile App"})
check("POST /api/complaints", r.status_code == 201, f"({r.status_code})")
body = r.get_json()
check("api category", body and body["category"] == "Electricity & Maintenance", str(body or {}))
check("api priority", body and body["priority"] in ("High", "Medium", "Low"))

r = client.get("/api/stats")
check("GET /api/stats", r.status_code == 200 and "by_category" in r.get_json())
check("api stats suspicious count", "suspicious" in r.get_json())

# --- geospatial map APIs ----------------------------------------------------
r_hotspots = client.get("/api/hotspots")
check("GET /api/hotspots", r_hotspots.status_code == 200 and len(r_hotspots.get_json()) >= 10)

r_incidents = client.get("/api/map-incidents")
check("GET /api/map-incidents", r_incidents.status_code == 200 and len(r_incidents.get_json()) > 0)

# --- fraud / anomaly detection ----------------------------------------------
spam_res = client.post("/api/complaints", json={
    "description": "Click here to buy discount crypto lottery prize and free casino cash tokens http://spam.example.com",
    "ward": "Block A", "source": "Student Portal"}).get_json()
check("fraud detection flagged", spam_res and spam_res.get("is_suspicious") is True, str(spam_res))

# --- weekly report + exports --------------------------------------------------
r = client.post("/reports/generate", follow_redirects=True)
check("POST /reports/generate", r.status_code == 200, f"({r.status_code})")

reports = client.get("/reports").get_data(as_text=True)
assert "PCU Campus Grievance Digest" in reports or "Digest" in reports

# fetch the latest report id from the db
from civic_sense import database as db
latest = db.get_reports(1)[0]
rid = latest["id"]

r = client.get(f"/reports/{rid}")
check("GET /reports/<id>", r.status_code == 200)

r = client.get(f"/reports/{rid}/pdf")
check("GET /reports/<id>/pdf", r.status_code == 200 and
      r.headers.get("Content-Type", "").startswith("application/pdf"),
      f"(type={r.headers.get('Content-Type')})")

r = client.get(f"/reports/{rid}/xlsx")
check("GET /reports/<id>/xlsx", r.status_code == 200 and
      "spreadsheet" in r.headers.get("Content-Type", "").lower(),
      f"(type={r.headers.get('Content-Type')})")

# --- status update workflow (complaint id 1 always exists after seeding) --------
from civic_sense import database as db2
cid = db2.get_complaints(limit=1)[0]["id"]
r = client.post(f"/complaints/{cid}/status", data={"status": "Resolved"},
                follow_redirects=True)
check("POST /complaints/<id>/status", r.status_code == 200)
check("status persisted", db2.get_complaint(cid)["status"] == "Resolved")
# revert for a neutral demo state
client.post(f"/complaints/{cid}/status", data={"status": "Open"})

# --- digest content check -----------------------------------------------------
check("digest mentions priority", "Priority" in latest["summary"])

# --- duplicate detection (identical complaint submitted twice) ---------------
# Use a unique description (timestamped) so it can never collide with records
# from a previous test run; the only possible match is the submission above it.
import uuid, random
_items = ["projector mount", "desk bench", "fan switch", "lan port", "water tap"]
_verbs = ["broken and hanging", "completely damaged", "dislodged", "shattered"]
_token = "".join(c for c in uuid.uuid4().hex if c.isalpha())[:10]
_unique = f"Classroom equipment {_token} {random.choice(_items)} was {random.choice(_verbs)}"
first = client.post("/api/complaints", json={
    "description": _unique,
    "ward": "Block C", "source": "Student Portal"}).get_json()
second = client.post("/api/complaints", json={
    "description": _unique,
    "ward": "Block C", "source": "Student Portal"}).get_json()
check("duplicate detection",
      first is not None and first.get("is_duplicate") is False
      and second is not None and second.get("is_duplicate") is True
      and second.get("duplicate_of") == first.get("id"),
      str(second))

# --- auto location detection (/api/detect-location) -------------------------
# Test with PCU campus center coordinates (18.749034, 73.606889)
loc_res = client.post("/api/detect-location", json={"lat": 18.749034, "lon": 73.606889})
check("POST /api/detect-location", loc_res.status_code == 200, f"({loc_res.status_code})")
loc_body = loc_res.get_json()
check("nearest block resolved", loc_body and "nearest_block" in loc_body and loc_body.get("on_campus") is True, str(loc_body))

# Test with invalid coordinates
bad_loc = client.post("/api/detect-location", json={"lat": "invalid", "lon": "xyz"})
check("detect-location validation", bad_loc.status_code == 400)

# --- image upload, verification & analysis ----------------------------------
import io
from PIL import Image

# Create an in-memory sample JPEG image
sample_img = Image.new("RGB", (320, 240), color=(180, 70, 90))
img_bytes = io.BytesIO()
sample_img.save(img_bytes, format="JPEG")
img_bytes.seek(0)

# 1. Test image upload via web form intake (multipart/form-data)
r_img_web = client.post("/complaints/new", data={
    "title": "Chipped tiles and cracked wall in Block B",
    "description": "Noticeable crack along corridor wall and chipped floor tiles near Room 201",
    "ward": "Block B", "floor": "2nd Floor", "room_number": "201",
    "source": "Student Portal",
    "user_lat": "18.7491", "user_lon": "73.6062",
    "image": (io.BytesIO(img_bytes.getvalue()), "corridor_crack.jpg")
}, content_type="multipart/form-data")
check("POST /complaints/new with image", r_img_web.status_code == 200, f"({r_img_web.status_code})")

# 2. Test image upload via API with multipart/form-data
img_bytes.seek(0)
r_img_api = client.post("/api/complaints", data={
    "title": "Water seepage in canteen ceiling",
    "description": "Continuous water droplet leaking from ceiling above dining table counter",
    "ward": "Central Canteen", "floor": "Ground Floor",
    "source": "PCU Mobile App",
    "user_lat": "18.7488", "user_lon": "73.6069",
    "image": (io.BytesIO(img_bytes.getvalue()), "canteen_leak.jpg")
}, content_type="multipart/form-data")
check("POST /api/complaints with image", r_img_api.status_code == 201, f"({r_img_api.status_code})")
img_api_body = r_img_api.get_json()

check("image_url returned", img_api_body and bool(img_api_body.get("image_url")), str(img_api_body.get("image_url")))
check("geo_source is gps_auto", img_api_body and img_api_body.get("geo_source") == "gps_auto", str(img_api_body.get("geo_source")))
check("image_result has sharpness & lighting",
      img_api_body and "image_result" in img_api_body and
      "sharpness_score" in img_api_body["image_result"] and
      "lighting_label" in img_api_body["image_result"] and
      "authenticity" in img_api_body["image_result"],
      str(img_api_body.get("image_result", {})))

# --- NCM-Net research innovation validations --------------------------------
# 1. Conformal prediction verification
check("conformal prediction set present",
      body and "conformal_prediction" in body and
      "prediction_set" in body["conformal_prediction"] and
      len(body["conformal_prediction"]["prediction_set"]) >= 1,
      str(body.get("conformal_prediction", {})))

# 2. Neuro-symbolic safety constraint verification
check("neuro-symbolic hazard axiom satisfied",
      body and "symbolic_axioms" in body and
      body["symbolic_axioms"].get("is_safety_critical") is True and
      len(body["symbolic_axioms"].get("axioms", [])) > 0,
      str(body.get("symbolic_axioms", {})))

# 3. Spatio-temporal cascade clusters endpoint
r_cascades = client.get("/api/cascades")
check("GET /api/cascades", r_cascades.status_code == 200 and "cascades" in r_cascades.get_json())

# 4. Conformal model stats endpoint
r_cstats = client.get("/api/conformal-stats")
check("GET /api/conformal-stats", r_cstats.status_code == 200 and r_cstats.get_json().get("safety_hazard_recall") == "100.0% Zero-Miss Bound")

# 5. Asymmetric gated cross-modal alignment (AG-CMA) gate check
check("AG-CMA modality gate present",
      img_api_body and "image_result" in img_api_body and
      "cross_modal_alignment" in img_api_body["image_result"] and
      "modality_gate_g" in img_api_body["image_result"]["cross_modal_alignment"],
      str(img_api_body.get("image_result", {}).get("cross_modal_alignment", {})))

print()
if fails:
    print(f"SMOKE TEST FAILED: {len(fails)} failures -> {fails}")
    sys.exit(1)
print("ALL SMOKE TESTS PASSED ✔")
