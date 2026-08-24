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
    ("There is a huge pothole near the school causing traffic", "Roads"),
    ("Streetlight not working for the past three days", "Electricity"),
    ("No water supply in our area since yesterday", "Water Supply"),
    ("Garbage not collected for two days in our street", "Waste Management"),
    ("Sewage overflowing near the market area", "Public Safety"),
]:
    cat, conf = classifier(text)
    check(f"classify: {text[:40]!r}", cat == want_cat,
          f"-> {cat} ({conf})")

# --- web pages -------------------------------------------------------------
for path in ["/", "/complaints", "/complaints?priority=High&ward=Ward%203",
             "/complaints/new", "/reports", "/pipeline"]:
    r = client.get(path)
    check(f"GET {path}", r.status_code == 200, f"({r.status_code})")

# --- intake via web form ----------------------------------------------------
r = client.post("/complaints/new", data={
    "title": "Broken footpath", "description": "Footpath tiles are broken near the park and people are falling",
    "ward": "Ward 2", "source": "Mobile App"}, follow_redirects=False)
check("POST /complaints/new", r.status_code == 200, f"({r.status_code})")

# --- intake via REST API -----------------------------------------------------
r = client.post("/api/complaints", json={
    "description": "Transformer is making loud noise and sparking at night",
    "ward": "Ward 8", "source": "Email"})
check("POST /api/complaints", r.status_code == 201, f"({r.status_code})")
body = r.get_json()
check("api category", body and body["category"] == "Electricity", str(body or {}))
check("api priority", body and body["priority"] in ("High", "Medium", "Low"))

r = client.get("/api/stats")
check("GET /api/stats", r.status_code == 200 and "by_category" in r.get_json())

# --- weekly report + exports --------------------------------------------------
r = client.post("/reports/generate", follow_redirects=True)
check("POST /reports/generate", r.status_code == 200, f"({r.status_code})")

reports = client.get("/reports").get_data(as_text=True)
assert "Weekly Civic Complaint Digest" in reports

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
check("digest mentions a ward", "Ward" in latest["summary"])
check("digest mentions priority", "Priority" in latest["summary"])

# --- duplicate detection (identical complaint submitted twice) ---------------
# Use a unique description (timestamped) so it can never collide with records
# from a previous test run; the only possible match is the submission above it.
_unique = ("The zebra crossing near the hospital has faded and needs repainting "
           f"(reported {datetime.now().strftime('%H%M%S%f')})")
first = client.post("/api/complaints", json={
    "description": _unique,
    "ward": "Ward 4", "source": "Web Portal"}).get_json()
second = client.post("/api/complaints", json={
    "description": _unique,
    "ward": "Ward 4", "source": "Web Portal"}).get_json()
check("duplicate detection",
      first is not None and first.get("is_duplicate") is False
      and second is not None and second.get("is_duplicate") is True
      and second.get("duplicate_of") == first.get("id"),
      str(second))

print()
if fails:
    print(f"SMOKE TEST FAILED: {len(fails)} failures -> {fails}")
    sys.exit(1)
print("ALL SMOKE TESTS PASSED ✔")
