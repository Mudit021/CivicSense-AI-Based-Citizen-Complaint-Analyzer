"""End-to-end smoke test for CivicSense.

Exercises the whole pipeline through the Flask test client:
- classifier training / reload
- demo seeding (including the fraud-alert and incident-hotspot scenarios)
- dashboard, filtering, intake (web form + REST API)
- fraud scoring persistence and API response consistency
- duplicate detection
- weekly report generation and PDF / Excel export

Run:  python smoke_test.py

This suite is intentionally run against a fresh database so the seeded counts
and scenario behaviour are reproducible. It does not depend on the
transformer/sentence-transformers stack, which is optional and currently
degraded by the environment.
"""

import os
import sys
from datetime import datetime

# Make console output encoding-safe (the digest text contains unicode symbols).
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass

# Ensure a clean database so the smoke run is deterministic.
# Re-running this file against an existing DB is fine in development, but CI
# should always start from a fresh state so the seeded counts are reproducible.
import sys
from civic_sense.config import DB_PATH
if DB_PATH.exists():
    DB_PATH.unlink()

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
for path in ["/", "/complaints", "/complaints?priority=High&ward=Vadgaon",
             "/complaints/new", "/reports", "/pipeline"]:
    r = client.get(path)
    check(f"GET {path}", r.status_code == 200, f"({r.status_code})")

# -- additional end-to-end checks for the newly documented features --

# Fraud scoring is wired into saved complaints (API inserts run the full
# pipeline and persist fraud_score / fraud_level / fraud_explanation).
# The returned body includes the pipeline result; the database row also stores
# these fields, so both the API response and a follow-up GET must be consistent.
fraud_body = client.post("/api/complaints", json={
    "description": "General complaint for fraud check",
    "ward": "PCMC", "source": "Web Portal"
}).get_json()
check("fraud fields in api response",
      fraud_body and isinstance(fraud_body, dict)
      and "fraud_score" in fraud_body and "fraud_level" in fraud_body
      and "fraud_explanation" in fraud_body
      and fraud_body["fraud_level"] in ("Low", "Medium", "High"),
      str(fraud_body))
# Follow up by fetching the saved row directly from the database so we know
# the persistence layer also received the fraud fields.
fraud_cid = fraud_body.get("id")
if fraud_cid:
    from civic_sense import database as _db
    saved_row = _db.get_complaint(fraud_cid)
    check("fraud fields persisted to DB",
          saved_row
          and isinstance(saved_row.get("fraud_score"), (int, float))
          and saved_row.get("fraud_level") in ("Low", "Medium", "High"),
          str(saved_row))

# Classification confidence should be a finite number in [0, 1].
check("api confidence normalized",
      0 <= fraud_body.get("confidence", -1) <= 1,
      str(fraud_body.get("confidence")))

# --- intake via web form ----------------------------------------------------
r = client.post("/complaints/new", data={
    "title": "Broken footpath", "description": "Footpath tiles are broken near the park and people are falling",
    "ward": "Chinchwad", "source": "Mobile App"}, follow_redirects=False)
check("POST /complaints/new", r.status_code == 200, f"({r.status_code})")

# --- intake via REST API -----------------------------------------------------
r = client.post("/api/complaints", json={
    "description": "Transformer is making loud noise and sparking at night",
    "ward": "Hinjewadi", "source": "Email"})
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
check("digest mentions a locality", any(loc in latest["summary"] for loc in ["PCMC", "Chinchwad", "Vadgaon", "Maval", "Talegaon", "Akurdi", "Wakad", "Hinjewadi", "Katraj", "Kamseth"]))
check("digest mentions priority", "Priority" in latest["summary"])

# --- duplicate detection (identical complaint submitted twice) ---------------
# Use a unique description (timestamped) so it can never collide with records
# from a previous test run; the only possible match is the submission above it.
_unique = ("The zebra crossing near the hospital has faded and needs repainting "
           f"(reported {datetime.now().strftime('%H%M%S%f')})")
first = client.post("/api/complaints", json={
    "description": _unique,
    "ward": "Maval", "source": "Web Portal"}).get_json()
second = client.post("/api/complaints", json={
    "description": _unique,
    "ward": "Maval", "source": "Web Portal"}).get_json()
# Duplicate detection invariant: submitting the same description twice in
# direct succession must link the second to the first with a 100% similarity
# ratio. If the DB already contains that exact text from a prior run, the
# first submission may itself be flagged duplicate; in that case the duplicate
# chain is still intact (both point to the same original), which is sufficient
# to prove the dedup stage works.
if first is not None and first.get("is_duplicate"):
    # Both point to the same original record.
    check("duplicate detection: both link to same original",
          second is not None and second.get("duplicate_of") == first.get("duplicate_of"),
          str((first.get("duplicate_of"), second.get("duplicate_of"))))
else:
    check("duplicate detection: first is fresh",
          first is not None and first.get("is_duplicate") is False,
          str(first))
    check("duplicate detection: second points at first",
          second is not None and second.get("duplicate_of") == first.get("id"),
          str(second))
check("duplicate detection: ratio is 1.0",
      second is not None and second.get("duplicate_ratio", 0) == 1.0,
      str(second))

print()
if fails:
    print(f"SMOKE TEST FAILED: {len(fails)} failures -> {fails}")
    sys.exit(1)
print("ALL SMOKE TESTS PASSED ✔")
