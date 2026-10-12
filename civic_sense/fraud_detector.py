"""Fraud / bad-faith detection module for CivicSense.

This is intentionally separate from the deduplication stage:

- **Duplicate detection** (preprocessing.py) links repeated reports of the same
  legitimate complaint so an incident is not over-counted.
- **Fraud detection** (here) looks for *bad-faith or manipulated* filings:
  floods of reports from one locality in a short window, near-identical spam
  appearing under many different identities, and trivially short or generic text.

Returns a 0–100 risk score, a qualitative level (Low / Medium / High), and an
XAI breakdown so officers can decide whether to mark a filing for review.

Signals:
  - semantic_similarity: how many other complaints share near-identical text
  - submission_frequency: how many complaints arrived from the same locality in
    the last hour
  - pattern_analysis: how generic / short the submitted text is

Configurable thresholds: FREQ_THRESHOLD, SIM_THRESHOLD.

This module is intentionally separate from duplicate detection in preprocessing.
Duplicate detection links repeated legitimate reports of the same incident so an
incident is not over-counted; fraud detection looks for bad-faith or manipulated
filings (floods, near-identical spam across different reporters, generic/short
text).

The demo seed (civic_sense/seed_data.py) includes an explicit fraud-alert
scenario so the Fraud Alerts dashboard card has something concrete to show.
"""
import json
from datetime import datetime, timedelta
from typing import Tuple, Dict, List, Optional

from . import database
from .preprocessing import similarity

# Tunable fraud thresholds.
FREQ_THRESHOLD = 5   # complaints from the same ward in the last hour before frequency risk ramps up
SIM_THRESHOLD = 0.85 # near-identical body text across many complaints before semantic spam risk ramps up
HIGH_FRAUD_SCORE = 70   # score at/above this is shown as High risk on the Fraud Alerts card
MEDIUM_FRAUD_SCORE = 30 # score at/above this is Medium; below this is Low

def analyze_fraud_risk(complaint: dict) -> Tuple[float, str, Dict[str, float]]:
    """
    Analyze a complaint for potential fraud/spam.

    Returns: (fraud_risk_score, fraud_level, explanation_breakdown)

    The three signals are independent so a single legitimate duplicate will
    not be punished twice (duplicate detection is elsewhere).
    """
    score = 0.0
    breakdown = {}

    desc = complaint.get("description", "")
    ward = complaint.get("ward", "")

    # 1. Semantic spam detection — near-identical body text across many
    #    different complaints suggests copy-paste automation rather than a
    #    single repeated legitimate report.
    sim_hits = 0
    for c in database.recent_complaints(limit=100):
        if complaint.get("id") and c["id"] == complaint.get("id"):
            continue
        if similarity(desc, c["description"]) > SIM_THRESHOLD:
            sim_hits += 1

    sim_score = min(sim_hits * 20.0, 40.0)
    breakdown["semantic_similarity"] = sim_score
    score += sim_score

    # 2. Submission frequency / flood detection — many complaints from the
    #    same locality within a short window is the strongest indicator of
    #    coordinated manipulation.
    one_hour_ago = (datetime.now() - timedelta(hours=1)).isoformat(timespec="seconds")
    with database.get_conn() as conn:
        row = conn.execute(
            "SELECT COUNT(*) as n FROM complaints WHERE ward = ? AND created_at >= ?",
            (ward, one_hour_ago)
        ).fetchone()
        freq = row["n"] if row else 0

    freq_score = 0.0
    if freq > FREQ_THRESHOLD:
        freq_score = min((freq - FREQ_THRESHOLD) * 5.0, 30.0)

    breakdown["submission_frequency"] = freq_score
    score += freq_score

    # 3. Pattern analysis — trivially short or formulaic text is harder to
    #    verify and is a weak but common spam signal.
    if len(desc) < 20:
        pattern_score = 10.0
    elif "please" in desc.lower() and len(desc) < 50:
        pattern_score = 5.0
    else:
        pattern_score = 0.0

    breakdown["pattern_analysis"] = pattern_score
    score += pattern_score

    # Final score capping
    final_score = min(score, 100.0)

    # Classification
    if final_score >= HIGH_FRAUD_SCORE:
        level = "High"
    elif final_score >= MEDIUM_FRAUD_SCORE:
        level = "Medium"
    else:
        level = "Low"

    return round(final_score, 2), level, breakdown

def generate_fraud_explanation(breakdown: Dict[str, float], score: float, level: str) -> List[str]:
    """XAI: Explains the fraud risk score in human-readable terms."""
    lines = []
    if breakdown.get("semantic_similarity", 0) >= 20:
        lines.append("Text is highly similar to other reports, suggesting possible automated spam.")
    if breakdown.get("submission_frequency", 0) >= 15:
        lines.append("Unusual volume of reports from this location in a short time window.")
    if breakdown.get("pattern_analysis", 0) > 0:
        lines.append("Complaint content is too generic or short to be verified.")

    if not lines:
        lines.append("No suspicious patterns detected.")

    lines.append(f"Fraud Risk Score: {score} ({level} Risk).")
    return lines
