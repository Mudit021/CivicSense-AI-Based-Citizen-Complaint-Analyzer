"""Priority assignment engine (paper section 3.4).

Combines multiple signals into an urgency score, exactly as described in the
paper: severity of the words used, number of similar complaints in the same
location, emotive language, and the age of the complaint. Each complaint is
labelled High / Medium / Low priority.
"""
from datetime import datetime

# Words that indicate an immediate safety / health hazard.
HIGH_KEYWORDS = {
    "accident", "flood", "fire", "sewage", "overflow", "burst", "electrocution",
    "collapse", "collapsed", "emergency", "injured", "drowning", "gas", "toxic",
    "smoke", "explosion", "leaking", "leak", "sparking", "hanging", "snapped",
    "falling", "crumbling", "attacking", "unfit", "contaminated", "danger",
    "dangerous", "risk", "hazard", "exposed", "manhole",
}

# Words that signal a notable but non-emergency problem.
MEDIUM_KEYWORDS = {
    "damaged", "broken", "frequent", "irregular", "not working", "not collected",
    "overflowing", "low", "cut", "delayed", "delay", "blocked", "choked",
    "dead", "flickering", "leaning", "tilted", "no water", "no electricity",
    "waste", "garbage", "pothole", "cracked", "rotting", "smelling", "noise",
}

# Emotive language used by frustrated citizens (boosts priority).
ANGRY_WORDS = {
    "useless", "furious", "angry", "frustrated", "disgusted", "sick",
    "terrible", "horrible", "shameless", "neglected", "unacceptable",
    "outrage", "fed up", "suffering", "helpless", "shame", "pathetic",
}

# Category base urgency: safety hazards outweigh cleanliness issues.
CATEGORY_BASE = {
    "Public Safety": 1.6,
    "Electricity": 1.0,
    "Roads": 0.5,
    "Water Supply": 0.5,
    "Waste Management": 0.0,
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
    """Many similar complaints in the same ward => escalating urgency."""
    return min(similar_count * 0.6, 2.4)


def _age_score(created_at: str) -> float:
    try:
        created = datetime.fromisoformat(created_at)
        days = max(0, (datetime.now() - created).total_seconds() / 86400)
    except (ValueError, TypeError):
        days = 0
    return min(days * 0.25, 1.0)


def assign_priority(text: str, category: str, ward: str, created_at: str,
                    similar_count: int = 0):
    """Compute priority + a human-readable breakdown for transparency."""
    breakdown = {
        "keywords": round(_keyword_score(text), 2),
        "category": CATEGORY_BASE.get(category, 0.0),
        "emotion": round(_emotion_score(text), 2),
        "frequency": round(_frequency_score(similar_count), 2),
        "age": round(_age_score(created_at), 2),
    }
    total = round(sum(breakdown.values()), 2)
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
    if breakdown["keywords"] >= 2.4:
        lines.append("Contains strongly urgent wording (e.g. safety or hazard terms).")
    elif breakdown["keywords"] > 0:
        lines.append("Contains issue-specific wording that indicates a problem.")
    if breakdown["category"] >= 1.6:
        lines.append("Category carries inherent safety risk (Public Safety).")
    elif breakdown["category"] >= 1.0:
        lines.append("Category involves electrical hazard risk.")
    if breakdown["emotion"] > 0:
        lines.append("Complaint expresses strong dissatisfaction or urgency.")
    if breakdown["frequency"] >= 1.8:
        lines.append("Many similar complaints reported in this ward recently.")
    elif breakdown["frequency"] > 0:
        lines.append("Similar complaints exist in this ward.")
    if breakdown["age"] > 0.5:
        lines.append("Issue has been pending for several days.")
    if not lines:
        lines.append("No strong urgency signals detected.")
    lines.append(f"Total urgency score: {total} (High ≥ 3.2, Medium ≥ 1.6).")
    return lines
