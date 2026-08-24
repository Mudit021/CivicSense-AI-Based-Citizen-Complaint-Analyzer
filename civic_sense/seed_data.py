"""Seed the demo database with realistic citizen complaints.

The generated corpus is processed through the *real* pipeline
(preprocessing -> classification -> prioritization), so every dashboard
statistic reflects actual model behaviour.
"""
import random
from datetime import datetime, timedelta

from . import database
from .classifier import classify_text
from .config import SOURCES
from .preprocessing import find_duplicate
from .prioritizer import assign_priority

# Category template pools — realistic complaints. Every template contains
# exactly one {place} slot so the dedup uniqueness key is effective.
_TEMPLATES = {
    "Roads": [
        "There is a huge pothole near {place} causing traffic jams every morning",
        "The main road near {place} is full of potholes and needs urgent repair",
        "Footpath tiles are broken near {place} and pedestrians are falling",
        "Road surface is cracked near {place}",
        "An open trench has been left on the road near {place} for a week",
        "Potholes on the ring road near {place} damaged my car tyre yesterday",
        "The speed breaker near {place} is completely damaged and vehicles speed through",
        "Street barricades have fallen over near {place} and block half the road",
        "Road markings near {place} have faded away completely",
        "The pavement outside {place} is broken and slippery when wet",
    ],
    "Electricity": [
        "Streetlight not working for the past three days near {place}",
        "Frequent power cuts in our area near {place} since last week",
        "Voltage near {place} fluctuates and is damaging our home appliances",
        "Transformer near {place} is making loud noise and sparking at night",
        "An electric pole near {place} is leaning dangerously over the footpath",
        "Hanging wires are touching the ground near {place} after the storm",
        "Streetlights are flickering near {place} and some are completely dead",
        "High tension wires are sagging very low over the road near {place}",
        "Power supply near {place} is disrupted every evening between 7 and 9 pm",
        "The street lamp near {place} has not worked for a whole week",
    ],
    "Water Supply": [
        "No water supply in our area near {place} since yesterday, tanks are empty",
        "Water pressure is very low near {place} in the mornings",
        "A water pipe near {place} is leaking and wasting water all day",
        "Pipeline burst and water is flooding the street near {place}",
        "Tap water near {place} is muddy and unfit to drink since two days",
        "Water supply near {place} is irregular, we get water only twice a week",
        "Water tanker did not come for three days near {place}",
        "Water from the tap near {place} smells bad and has a strange colour",
        "The overhead tank near {place} is not filling up at all",
        "Leakage from the main water line near {place} is damaging the road",
    ],
    "Waste Management": [
        "Garbage not collected for two days near {place}",
        "Dustbin is overflowing near {place} and rubbish is scattered",
        "Garbage is dumped in the open ground near {place}",
        "Sanitation workers have not visited the area near {place} this week",
        "A dead animal is lying near {place} and the whole area smells",
        "Construction debris is dumped on the footpath near {place}",
        "The drain near {place} is choked with garbage and plastic waste",
        "Garbage trucks come very late near {place} and scatter waste everywhere",
        "People are burning waste in the open field near {place} causing thick smoke",
        "Plastic waste is piled up near {place} for days",
    ],
    "Public Safety": [
        "Sewage overflowing near {place} and spreading on the road",
        "Open manhole near {place} is a danger to children walking to school",
        "Stray dogs are attacking people near {place} in the evening",
        "A tree branch fell near {place} and blocked the way for everyone",
        "The old building near {place} is crumbling and bricks are falling",
        "The bridge railing near {place} is broken and completely unsafe",
        "Flood water is entering houses near {place} after the heavy rain",
        "A gas leak is reported near {place}",
        "Smoke is coming from the electric box near {place}",
        "The abandoned house near {place} is a hiding place for anti-socials",
    ],
}

_WARD_WEIGHTS = {
    "Ward 1": 0.06, "Ward 2": 0.13, "Ward 3": 0.16, "Ward 4": 0.06,
    "Ward 5": 0.15, "Ward 6": 0.11, "Ward 7": 0.09, "Ward 8": 0.12,
    "Ward 9": 0.06, "Ward 10": 0.06,
}
_CATEGORY_WEIGHTS = {
    "Roads": 0.24, "Electricity": 0.18, "Water Supply": 0.20,
    "Waste Management": 0.20, "Public Safety": 0.18,
}
_PLACES = ["the school", "the market", "the park", "the bus stop", "the temple",
           "the hospital", "the petrol pump", "the community hall", "the stadium",
           "the railway station", "the church", "the playground", "the river bridge",
           "the fish market", "the old fort road", "the lake view colony"]

# Fraction of complaints that are deliberate re-files of an earlier one
# (realistic duplicate behaviour that exercises the dedup stage).
REPORTED_DUPLICATE_FRACTION = 0.10

# Occasionally inject the paper's "challenges": very short / ambiguous text.
_AMBIGUOUS = [
    ("No water", "Water Supply"),
    ("Road bad", "Roads"),
    ("Light not working", "Electricity"),
    ("Garbage everywhere", "Waste Management"),
    ("Very dangerous near school", "Public Safety"),
]


def _random_time(now: datetime) -> str:
    """Weight recent days more heavily (complaint influx is not uniform)."""
    days_back = int(random.random() ** 1.4 * 14)  # skewed towards 0
    dt = now - timedelta(days=days_back,
                         hours=random.randint(0, 23),
                         minutes=random.randint(0, 59))
    return dt.isoformat(timespec="seconds")


def _generate(n: int = 180) -> list:
    now = datetime.now()
    out = []
    used = []            # (text, category) pairs for deliberate re-files
    used_keys = set()    # (category, template_index, place) for uniqueness

    def _finish(text, category):
        used.append((text, category))
        title = " ".join(text.split()[:6]).rstrip(",").capitalize() + "..."
        ward = random.choices(list(_WARD_WEIGHTS),
                              weights=list(_WARD_WEIGHTS.values()))[0]
        out.append({"ward": ward, "category": category, "title": title,
                    "description": text, "source": random.choice(SOURCES),
                    "created_at": _random_time(now)})

    while len(out) < n:
        if random.random() < 0.06:
            # The paper's challenge: very short / ambiguous complaints.
            text, category = random.choice(_AMBIGUOUS)
            _finish(text.capitalize(), category)
        elif used and random.random() < REPORTED_DUPLICATE_FRACTION:
            # Deliberate re-file: copy an earlier complaint verbatim so the
            # dedup stage has real duplicates to catch.
            text, category = random.choice(used)
            _finish(text, category)
        else:
            category = random.choices(list(_CATEGORY_WEIGHTS),
                                      weights=list(_CATEGORY_WEIGHTS.values()))[0]
            idx = random.randrange(len(_TEMPLATES[category]))
            place = random.choice(_PLACES)
            key = (category, idx, place)
            if key in used_keys:
                continue  # avoid near-identical template repeats
            used_keys.add(key)
            text = _TEMPLATES[category][idx].format(place=place)
            _finish(text, category)
    return out


def seed_if_empty(n: int = 180) -> int:
    """Populate the database with processed sample complaints if it is empty."""
    if database.complaint_count() > 0:
        return 0

    from .classifier import load_classifier
    classifier, _metrics = load_classifier()

    inserted = 0
    for c in _generate(n):
        cat, conf = classify_text(classifier, c["description"])

        dup = find_duplicate(c["description"])
        if dup:
            c["is_duplicate"], c["duplicate_of"] = 1, dup[0]

        similar = database.similar_complaints(c["ward"], cat)
        priority, _score, _bd = assign_priority(
            c["description"], cat, c["ward"], c["created_at"], similar)

        database.insert_complaint({
            "source": c["source"], "ward": c["ward"], "category": cat,
            "title": c["title"], "description": c["description"],
            "priority": priority, "confidence": conf,
            "is_duplicate": c.get("is_duplicate", 0),
            "duplicate_of": c.get("duplicate_of"),
            "created_at": c["created_at"],
        })
        inserted += 1
    return inserted
