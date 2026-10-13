"""Priority assignment engine (paper section 3.4).

Combines multiple signals into an urgency score, exactly as described in the
paper: severity of the words used, number of similar complaints in the same
location, emotive language, and the age of the complaint. Each complaint is
labelled High / Medium / Low priority.
"""
from datetime import datetime

# Words that indicate an immediate safety / health hazard on campus.
HIGH_KEYWORDS = {
    "accident", "flood", "fire", "electrocution", "shock", "short circuit",
    "collapse", "collapsed", "emergency", "injured", "gas leak", "chemical spill",
    "smoke", "explosion", "sparking", "snapped wire", "falling ceiling", "ragging",
    "trapped", "stuck in lift", "elevator stuck", "food poisoning", "vomiting",
    "contaminated water", "danger", "dangerous", "hazard", "exposed wire",
    "medical emergency", "assault", "harassment",
    "spark", "sparks", "switchboard", "live wire", "open wire", "burning smell",
    "burnt smell", "burnt wire", "grinding noise", "loud grinding", "grinding noises",
    "elevator malfunction", "lift malfunctioning", "cable snapped", "falling debris",
    "high voltage", "circuit breaker tripped", "structural crack",
}

# Words that signal a notable but non-emergency campus problem.
MEDIUM_KEYWORDS = {
    "damaged", "broken", "frequent", "irregular", "not working", "choked",
    "overflowing", "cut", "delayed", "blocked", "no water", "no electricity",
    "no power", "wifi down", "internet down", "projector broken", "ac not cooling",
    "fan not working", "geyser broken", "cold water", "flush broken", "leaking tap",
    "unhygienic", "cockroach", "insects", "stale food", "hair in food", "mess food",
    "parking blocked", "wrong parking", "dark corridor", "lights out", "sound system",
    "podium mic", "socket not working", "water cooler", "elevator", "lift", "grinding",
}

# Emotive language used by frustrated students / residents (boosts priority).
ANGRY_WORDS = {
    "useless", "furious", "angry", "frustrated", "disgusted", "sick",
    "terrible", "horrible", "unacceptable", "outrage", "fed up", "suffering",
    "helpless", "pathetic", "exam tomorrow", "cannot study", "ruined",
}

# Category base urgency for campus categories
CATEGORY_BASE = {
    "Campus Safety & Parking": 1.6,
    "Electricity & Maintenance": 1.2,
    "Canteen & Food Quality": 1.0,
    "Water Supply & Washrooms": 0.8,
    "Classroom & Lab Infrastructure": 0.6,
    "Hostel & Residential Life": 0.6,
}

THRESHOLD_HIGH = 3.2
THRESHOLD_MEDIUM = 1.6


def _keyword_score(text: str) -> float:
    low = text.lower()
    high_hits = sum(1 for w in HIGH_KEYWORDS if w in low)
    medium_hits = sum(1 for w in MEDIUM_KEYWORDS if w in low)
    return min(high_hits * 1.2, 3.6) + min(medium_hits * 0.35, 1.4)


def _emotion_score(text: str) -> float:
    low = text.lower()
    score = 0.0
    if any(w in low for w in ANGRY_WORDS):
        score += 1.0
    if low.count("!") >= 2:
        score += 0.5
    words = [w for w in low.split() if w]
    if words:
        caps = sum(1 for w in words if w.isupper() and len(w) > 2)
        if caps / len(words) > 0.3:
            score += 0.5
    return score


def _frequency_score(similar_count: int) -> float:
    """Many similar complaints in the same block/location => escalating urgency."""
    return min(similar_count * 0.6, 2.4)


def _age_score(created_at: str) -> float:
    try:
        created = datetime.fromisoformat(created_at)
        days = max(0, (datetime.now() - created).total_seconds() / 86400)
    except (ValueError, TypeError):
        days = 0
    return min(days * 0.25, 1.0)


def _visual_evidence_score(image_result: dict = None) -> tuple:
    """Compute priority boost and evidence explanations from uploaded photo analysis."""
    if not image_result or not image_result.get("has_image") or not image_result.get("is_valid"):
        return 0.0, []

    score = 0.0
    notes = []

    # 1. Clarity and authenticity: real verifiable photo evidence gets base credibility boost
    sharpness_label = image_result.get("sharpness_label", "")
    if "Sharp" in sharpness_label or "Moderate" in sharpness_label:
        score += 0.4
        notes.append("Verified clear photo evidence confirms physical complaint authenticity (+0.4).")

    # 2. Defect signatures & hazardous environments
    defect_tags = image_result.get("defect_tags", [])
    lighting_label = image_result.get("lighting_label", "")

    if "Basement / Blackout Lighting" in defect_tags or "Pitch Dark" in lighting_label or "Low Light" in lighting_label:
        score += 0.6
        notes.append("Visual evidence confirms pitch-dark / unlit conditions posing safety hazard (+0.6).")

    if "Water / Reflective Surface" in defect_tags:
        score += 0.5
        notes.append("Visual evidence confirms active water leakage / moisture pooling (+0.5).")

    if "High Texture / Physical Structural Edge" in defect_tags and image_result.get("sharpness_score", 0) > 250:
        score += 0.4
        notes.append("Visual evidence detects high-fracture structural or physical equipment damage (+0.4).")

    if "Warm Food / Heating Equipment" in defect_tags:
        score += 0.3
        notes.append("Visual evidence confirms cafeteria food or heating equipment issue (+0.3).")

    return min(round(score, 2), 1.5), notes


def assign_priority(text: str, category: str, ward: str, created_at: str,
                    similar_count: int = 0, image_result: dict = None):
    """Compute priority + a human-readable breakdown for transparency."""
    low = text.lower()
    visual_boost, visual_notes = _visual_evidence_score(image_result)

    # Acute Compound Hazard check (e.g. electrical/fire danger on passenger lift or main switchboard)
    has_active_danger = any(k in low for k in [
        "spark", "sparking", "sparks", "smoke", "burning", "burnt", "fire", "shock",
        "electrocution", "explosion", "short circuit", "gas leak"
    ])
    has_critical_machinery = any(k in low for k in [
        "elevator", "lift", "switchboard", "transformer", "circuit breaker",
        "panel", "substation", "high voltage", "boiler"
    ])
    has_severe_mechanical = any(k in low for k in [
        "grinding", "screeching", "loud grinding", "snapped", "trapped",
        "stuck", "cable", "vibrating", "falling"
    ])

    compound_hazard = 0.0
    compound_notes = []
    if has_active_danger and has_critical_machinery:
        compound_hazard = 1.6
        compound_notes.append("Critical Hazard Alert: Active electrical spark/fire threat detected on passenger lift or switchboard (+1.6).")
    elif has_critical_machinery and has_severe_mechanical:
        compound_hazard = 1.2
        compound_notes.append("Severe Mechanical Threat: Mechanical breakdown detected in critical passenger transport system (+1.2).")
    elif has_active_danger and has_severe_mechanical:
        compound_hazard = 1.0
        compound_notes.append("Compound Hazard: Dangerous mechanical stress accompanied by active electrical or heat hazard (+1.0).")

    breakdown = {
        "keywords": round(_keyword_score(text), 2),
        "category": CATEGORY_BASE.get(category, 0.0),
        "compound_hazard": round(compound_hazard, 2),
        "emotion": round(_emotion_score(text), 2),
        "frequency": round(_frequency_score(similar_count), 2),
        "age": round(_age_score(created_at), 2),
        "visual_evidence": visual_boost,
        "_compound_notes": compound_notes,
        "_visual_notes": visual_notes,
    }
    # Calculate total without private metadata
    total_val = sum(v for k, v in breakdown.items() if not k.startswith("_"))
    total = round(total_val, 2)
    if total >= THRESHOLD_HIGH:
        priority = "High"
    elif total >= THRESHOLD_MEDIUM:
        priority = "Medium"
    else:
        priority = "Low"
    return priority, total, breakdown


def priority_explanation(breakdown: dict, total: float) -> list:
    """Turn the score breakdown into sentences shown on the UI."""
    lines = []
    for note in breakdown.get("_compound_notes", []):
        lines.append(note)
    if breakdown["keywords"] >= 2.4:
        lines.append("Contains strongly urgent wording (e.g. severe hazard or emergency terms).")
    elif breakdown["keywords"] > 0:
        lines.append("Contains campus issue-specific keywords indicating equipment or facility failure.")
    if breakdown["category"] >= 1.6:
        lines.append("Category carries inherent campus safety or security risk.")
    elif breakdown["category"] >= 1.0:
        lines.append("Category involves electrical hazards or food hygiene health concerns.")
    if breakdown["emotion"] > 0:
        lines.append("Complaint expresses strong student distress or urgency (e.g. upcoming exams).")
    if breakdown["frequency"] >= 1.8:
        lines.append("Multiple similar complaints reported in this campus location recently.")
    elif breakdown["frequency"] > 0:
        lines.append("Similar complaints exist in this campus location.")
    if breakdown["age"] > 0.5:
        lines.append("Issue has been pending unresolved for several days.")
    # Append visual evidence findings if present
    for note in breakdown.get("_visual_notes", []):
        lines.append(note)
    if not lines:
        lines.append("No strong urgency signals detected.")
    lines.append(f"Total urgency score: {total} (High >= 3.2, Medium >= 1.6).")
    return lines

