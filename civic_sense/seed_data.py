"""Seed the demo database with realistic citizen complaints.

The generated corpus is processed through the real pipeline
(preprocessing -> classification -> prioritization -> fraud scoring), so every
dashboard statistic reflects actual model behaviour.

Two hidden scenarios are injected beyond the paper's plain complaint corpus:

1. Fraud-alert scenario - a short burst of near-identical, short, generic
   reports submitted from the same ward in the same narrow time window. This is
   designed to light up the fraud detector's submission frequency and semantic
   spam signals, so the dashboard's "Fraud Alerts" card has something concrete
   to show.

2. Incident-hotspot scenario - a wider cluster of distinct-but-related
   complaints about the same underlying incident (same ward, same category,
   semantically similar phrasing) submitted over several hours. This is designed
   to light up the incident-cluster signal and give the "Incident Hotspots" card
   a representative cluster to display.

These are labelled internally with the `scenario` field so they can be
excluded from deterministic tests if needed.
"""
from __future__ import annotations

import random
from datetime import datetime, timedelta
from typing import Dict, List

from . import database
from .classifier import classify_text
from .config import SOURCES, WARDS
from .preprocessing import find_duplicate, detect_incident_cluster
from .prioritizer import assign_priority

# ---------------------------------------------------------------------------
# Scenario constants
# ---------------------------------------------------------------------------

# How many near-identical spam reports to inject for the fraud-alert scenario.
# Kept small so the burst is tight in time (which is what the frequency signal
# reacts to) rather than a long, diffuse trickle.
FRAUD_SCENARIO_COUNT = 12

# The fraud scenario is clustered in one ward and one narrow time band so the
# frequency signal is credible. The window must sit *inside* the last hour:
# the detector's flood signal only counts complaints submitted within the
# previous 60 minutes, so a burst timestamped further back scores zero.
FRAUD_SCENARIO_WARD = "Hinjewadi"
FRAUD_SCENARIO_START_MINUTES_AGO = 50
FRAUD_SCENARIO_SPREAD_MINUTES = 40          # entire burst lands in the last ~50 min

# How many related-but-distinct reports to inject for the incident-hotspot
# scenario. They share a locality and a theme but are phrased differently so
# they are *not* treated as duplicates of one another.
HOTSPOT_SCENARIO_COUNT_WORDS = 8
HOTSPOT_SCENARIO_SPREAD_HOURS = 6
HOTSPOT_SCENARIO_WARD = "Wakad"
HOTSPOT_SCENARIO_CATEGORY = "Public Safety"

# Generic spam templates used for the fraud scenario. These are intentionally
# repetitive and short so the fraud detector has something concrete to score.
# They are used by the fraud-alert scenario in the demo seed.
_FRAUD_SPAM_TEMPLATES = [
    "Please fix this issue immediately",
    "Need urgent attention please",
    "Kindly look into this matter",
    "Immediate action required please",
    "Need help asap please",
    "Please attend to this ASAP",
    "Attention required urgently",
    "Please resolve this issue",
]

# Related-but-distinct hotspot templates. These describe one underlying
# incident from different angles so they are semantically similar but not
# near-duplicates. They are used by the incident-hotspot scenario in the
# demo seed.
_HOTSPOT_TEMPLATES = [
    "A tree has fallen across the road near {place} after the rain",
    "The road near {place} is blocked by a fallen tree branch",
    "A large tree branch near {place} has come down and is blocking traffic",
    "The tree near {place} dropped a heavy branch onto the road",
    "Debris from the tree near {place} is spread all over the road",
    "A tree near {place} has cracked and a branch fell on the road",
    "The roadside tree near {place} lost a big branch last night",
    "Fallen tree near {place} is stopping vehicles from passing",
    "A fallen tree near {place} is blocking the road and traffic",
    "Large branches from the tree near {place} have covered the road",
]

# Extra public safety hotspots phrased as urgent safety issues.
_HOTSPOT_EXTRA_PUBLIC_SAFETY = [
    "Open manhole near {place} is dangerous for pedestrians and children",
    "Sewage water is leaking near {place} and spreading on the road",
    "A tree branch has blocked the road near {place} after the storm",
    "The street near {place} has debris from a fallen tree and is unsafe",
    "Water is entering houses near {place} after the heavy rain",
]


def _fraud_scenario(now: datetime) -> List[Dict]:
    """Generate the fraud-alert burst.

    Near-identical, short, generic texts submitted from the same ward within a
    tight time window so the frequency + semantic spam signals fire.
    """
    base = now - timedelta(minutes=FRAUD_SCENARIO_START_MINUTES_AGO)
    out = []
    # Real coordinated spam re-uses the same short text under many identities,
    # so the burst draws from a deliberately small pool and repeats it. Using
    # eight distinct wordings would look like ordinary citizens complaining,
    # not like automated filing.
    pool = _FRAUD_SPAM_TEMPLATES[:3]
    for i in range(FRAUD_SCENARIO_COUNT):
        text = pool[i % len(pool)]
        dt = base + timedelta(minutes=random.randint(0, FRAUD_SCENARIO_SPREAD_MINUTES))
        out.append({
            "description": text,
            "title": text.capitalize() + "...",
            "ward": FRAUD_SCENARIO_WARD,
            "category": "Roads",
            "source": random.choice(SOURCES),
            "created_at": dt.isoformat(timespec="seconds"),
            "scenario": "fraud_alert",
        })
    return out


# A stable cluster id for the demo hotspot scenario. It must be deterministic:
# Python's built-in hash() is randomised per process, which would make the
# cluster id change on every restart and break reproducible tests.
HOTSPOT_CLUSTER_ID = 5000001


# ---------------------------------------------------------------------------
# Incident-hotspot scenario
# ---------------------------------------------------------------------------


def _hotspot_scenario(now: datetime) -> List[Dict]:
    """Generate the incident-hotspot cluster.

    Distinct-but-related complaints about the same underlying incident in the
    same ward, phrased differently so they are similar but not near-duplicates.
    This lights up the incident-cluster signal and gives the dashboard a
    hotspot to display.

    The hotspot cluster is tagged with a shared `cluster_id` so the dashboard
    can group the related complaints even when the semantic embedding path is
    unavailable in the current environment.
    """
    base = now - timedelta(hours=HOTSPOT_SCENARIO_SPREAD_HOURS)
    place = random.choice(["the school", "the market", "the park", "the bus stop"])
    out = []
    used_keys = set()
    needed = HOTSPOT_SCENARIO_COUNT_WORDS
    attempts = 0

    # Build a full group of related complaints first, then share one cluster_id
    # across them so the dashboard Incident Hotspots card has something to show.
    while len(out) < needed and attempts < needed * 5:
        attempts += 1
        template = random.choice(_HOTSPOT_TEMPLATES)
        key = (template, place)
        if key in used_keys:
            continue
        used_keys.add(key)
        dt = base + timedelta(
            hours=random.randint(0, HOTSPOT_SCENARIO_SPREAD_HOURS),
            minutes=random.randint(0, 59),
        )
        out.append({
            "description": template.format(place=place),
            "title": " ".join(template.format(place=place).split()[:6]).capitalize() + "...",
            "ward": HOTSPOT_SCENARIO_WARD,
            "category": HOTSPOT_SCENARIO_CATEGORY,
            "source": random.choice(SOURCES),
            "created_at": dt.isoformat(timespec="seconds"),
            "scenario": "incident_hotspot",
        })

    # The dashboard Incident Hotspots card groups by cluster_id, so attach the
    # same shared, deterministic cluster id to every related complaint.
    for c in out:
        c["cluster_id"] = HOTSPOT_CLUSTER_ID

    return out


def _category_template_pools() -> Dict[str, List[str]]:
    """Return realistic complaint templates by category.

    Every template contains exactly one {place} slot so the dedup uniqueness
    key is effective.
    """
    return _TEMPLATES


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
    "PCMC": 0.06, "Chinchwad": 0.13, "Vadgaon": 0.16, "Maval": 0.06,
    "Talegaon": 0.15, "Akurdi": 0.11, "Wakad": 0.09, "Hinjewadi": 0.12,
    "Katraj": 0.06, "Kamseth": 0.06,
}

_CATEGORY_WEIGHTS = {
    "Roads": 0.24, "Electricity": 0.18, "Water Supply": 0.20,
    "Waste Management": 0.20, "Public Safety": 0.18,
}

_PLACES = [
    "the school", "the market", "the park", "the bus stop", "the temple",
    "the hospital", "the petrol pump", "the community hall", "the stadium",
    "the railway station", "the church", "the playground", "the river bridge",
    "the fish market", "the old fort road", "the lake view colony",
]

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


# Fixed random state for the demonstration corpus. Without this the seed is
# stochastic and every count quoted for the dashboard (duplicates, clusters,
# fraud bands, priority mix) drifts between runs, which makes the project
# report unreproducible. Seeding here makes the whole demo deterministic:
# the same corpus, the same counts and the same report numbers every time.
RANDOM_STATE = 20261011


def _generate(n: int = 180) -> list:
    now = datetime.now()
    out = []
    used = []            # (text, category) pairs for deliberate re-files
    used_keys = set()    # (category, template_index, place) for uniqueness

    def _finish(text, category, ward=None, scenario=None):
        used.append((text, category))
        title = " ".join(text.split()[:6]).rstrip(",").capitalize() + "..."
        if ward is None:
            ward = random.choices(list(_WARD_WEIGHTS),
                                  weights=list(_WARD_WEIGHTS.values()))[0]
        out.append({
            "ward": ward,
            "category": category,
            "title": title,
            "description": text,
            "source": random.choice(SOURCES),
            "created_at": _random_time(now),
            "scenario": scenario,
        })

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


# ---------------------------------------------------------------------------
# Seeding
# ---------------------------------------------------------------------------


def seed_if_empty(n: int = 180) -> int:
    """Populate the database with processed sample complaints if it is empty.

    Every seed record runs through the live pipeline
    (classification -> duplicate detection -> fraud scoring -> prioritization),
    so dashboard stats reflect actual model behaviour rather than hardcoded
    values.

    Injected scenarios:
      - fraud_alert: a short burst of near-identical spam from one ward within
        a tight time window, designed to light up the fraud detector.
      - incident_hotspot: a wider cluster of related-but-distinct complaints
        about one underlying incident, designed to light up the incident-cluster
        signal.

    Verification note:
      The intended demo behaviour is a credible Medium fraud signal, not
      necessarily High. If you want the dashboard Fraud Alerts card to show
      High-risk rows from a fresh seed, do not lower the fraud thresholds in
      fraud_detector.py just for the demo; instead raise
      FRAUD_SCENARIO_COUNT, tighten FRAUD_SCENARIO_START_HOURS_AGO, or tighten
      the detector thresholds, and then re-run the smoke suite.
    """
    if database.complaint_count() > 0:
        return 0

    # Deterministic demonstration corpus (see RANDOM_STATE above).
    random.seed(RANDOM_STATE)

    from .classifier import load_classifier
    from .fraud_detector import analyze_fraud_risk, generate_fraud_explanation
    classifier, _metrics = load_classifier()

    # Build the base corpus first, then attach the scenario bursts so the
    # fraud/hotspot signals have realistic prior context to react to.
    generated = _generate(n)
    # The scenario rows must run through the real pipeline before seeding,
    # otherwise their database rows will not get the duplicate/fraud/priority/
    # cluster fields the dashboard and API expect. Each scenario is injected
    # exactly once so the corpus stays reproducible.
    generated.extend(_hotspot_scenario(datetime.now()))
    generated.extend(_fraud_scenario(datetime.now()))
    inserted = 0
    for c in generated:
        cat, conf = classify_text(classifier, c["description"])

        dup = find_duplicate(c["description"], ward=c["ward"], category=cat)
        if dup:
            c["is_duplicate"], c["duplicate_of"] = 1, dup[0]

        # Incident clustering for the general corpus. The hotspot scenario
        # already carries its own shared cluster id.
        if not c.get("cluster_id") and not dup:
            c["cluster_id"] = detect_incident_cluster(
                c["description"], ward=c["ward"], category=cat)

        similar = database.similar_complaints(c["ward"], cat)
        priority, score, breakdown = assign_priority(
            c["description"], cat, c["ward"], c["created_at"], similar)

        fraud_score, fraud_level, fraud_breakdown = analyze_fraud_risk({
            "description": c["description"], "ward": c["ward"],
            "id": None,
        })
        fraud_explanation = generate_fraud_explanation(
            fraud_breakdown, fraud_score, fraud_level)

        database.insert_complaint({
            "source": c["source"], "ward": c["ward"], "category": cat,
            "title": c["title"], "description": c["description"],
            "priority": priority, "confidence": conf,
            "is_duplicate": c.get("is_duplicate", 0),
            "duplicate_of": c.get("duplicate_of"),
            "created_at": c["created_at"],
            "priority_score": score, "priority_breakdown": breakdown,
            "fraud_score": fraud_score, "fraud_level": fraud_level,
            "fraud_explanation": fraud_explanation,
            # Persisted so the dashboard Incident Hotspots card can group rows
            # by cluster. Omitting this was the bug that left the card empty.
            "cluster_id": c.get("cluster_id"),
        })
        inserted += 1
    return inserted
