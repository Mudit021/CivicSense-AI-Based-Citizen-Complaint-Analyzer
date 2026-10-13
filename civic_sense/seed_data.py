"""Seed the demo database with realistic PCU campus student complaints.

The generated corpus is processed through the *real* pipeline
(preprocessing -> classification -> prioritization), so every dashboard
statistic reflects actual model behaviour.
"""
import random
from datetime import datetime, timedelta

from . import database
from .classifier import classify_text
from .config import SOURCES, CAMPUS_BLOCKS, FLOORS
from .preprocessing import find_duplicate
from .prioritizer import assign_priority

# Realistic PCU campus complaint templates for all 6 categories
_TEMPLATES = {
    "Classroom & Lab Infrastructure": [
        "Projector is not turning on and screen remains completely blank in {place}",
        "HDMI display cable and audio system are physically damaged in {place}",
        "Multiple high-performance lab computers and CPUs fail to boot in {place}",
        "Air conditioning unit is blowing warm air and making a loud rattling sound in {place}",
        "Broken desk benches with sharp nails protruding causing hazard for students in {place}",
        "Podium microphone is producing severe screeching feedback during lectures in {place}",
        "Whiteboard is stained permanently and marker tray is broken in {place}",
        "Window glass pane is cracked and vibrating heavily during winds in {place}",
        "Ethernet wall ports and network switch have no connectivity in {place}",
        "Ceiling fans are wobbling dangerously and not cooling the lecture room in {place}",
    ],
    "Hostel & Residential Life": [
        "Hot water geyser is not functioning in the bathroom wing of {place}",
        "Hostel Wi-Fi access point is completely disconnected since yesterday in {place}",
        "Study table and cot frame are badly damaged and need carpenter repair in {place}",
        "Severe insect and mosquito breeding issue reported inside rooms of {place}",
        "Water seepage leaking from upper floor ceiling onto student study desk in {place}",
        "Washing machines in the laundry area are vibrating violently and failing to drain in {place}",
        "Room door lock latch is jammed and students are locked out of {place}",
        "Common room water dispenser and study room air conditioning are out of order in {place}",
        "Excessive noise disturbance after quiet hours near corridor of {place}",
        "Window wire mesh is torn allowing rain and insects into rooms in {place}",
    ],
    "Electricity & Maintenance": [
        "Exposed electrical wiring sparking near the main switchboard in {place}",
        "Frequent power tripping and voltage fluctuations disrupting practical sessions in {place}",
        "Corridor tube lights and emergency exit signs are burnt out and dark in {place}",
        "Elevator is producing loud grinding noises and jerked abruptly between floors in {place}",
        "Wall power socket has visible burn marks and gave a mild electric shock in {place}",
        "Exhaust fans have stopped spinning causing hot air and fumes to build up in {place}",
        "Generator backup failed to kick in during evening study hours in {place}",
        "Staircase illumination is completely off creating tripping risk at night in {place}",
        "Lab 3-phase power breaker tripped during machinery operation in {place}",
        "Loose electrical wire hanging dangerously low in the corridor of {place}",
    ],
    "Water Supply & Washrooms": [
        "No running water supply in the entire washroom wing since early morning in {place}",
        "Drinking water cooler filter is dispensing murky brownish water in {place}",
        "Urinals and toilet flushes are clogged and overflowing onto the floor in {place}",
        "Restroom door latch is broken and sink faucet is leaking continuously in {place}",
        "Overhead terrace water storage tank is overflowing and flooding stairs in {place}",
        "Foul sewage smell rising from floor drainage pipes in {place}",
        "Liquid soap dispensers and paper towel holders are broken and empty in {place}",
        "Extremely low water pressure in wash basins making handwashing impossible in {place}",
        "Drain pipe under washroom basin burst and flooded the hallway of {place}",
        "Hostel solar hot water line has been cold for three consecutive days in {place}",
    ],
    "Canteen & Food Quality": [
        "Lunch meal served had undercooked rice and stale vegetables at {place}",
        "Found a dead insect in the food plate served to students at {place}",
        "Drinking water glasses and steel trays have sticky oil residue and food stains at {place}",
        "Breakfast milk served tasted sour and appeared curdled at {place}",
        "Vendors are overcharging students above printed MRP for snacks at {place}",
        "Hostellers suffered severe food poisoning and vomiting after dinner at {place}",
        "Food counter has swarms of houseflies and unhygienic open food containers at {place}",
        "Patties and sandwiches served were hard, cold, and visibly expired at {place}",
        "Cooking oil used for frying smells burnt and reused excessively at {place}",
        "Disorderly rush at lunch counters due to lack of queue barriers at {place}",
    ],
    "Campus Safety & Parking": [
        "Two-wheelers and cars parked haphazardly blocking the ambulance ramp at {place}",
        "Basement underground parking lights are completely shut off leaving it pitch dark at {place}",
        "Speeding private vehicles and rash driving observed on the internal road near {place}",
        "Stray dog pack acting aggressive towards students walking in the evening near {place}",
        "CCTV security camera appears switched off or misaligned at {place}",
        "Fire extinguisher inspection tag expired two years ago and gauge is in red zone at {place}",
        "Emergency fire exit door has been locked with a heavy iron chain at {place}",
        "Waterlogging and oil slick puddles on the concrete floor in basement parking of {place}",
        "Unknown visitors roaming campus without security badges near {place}",
        "Student helmet and riding gear stolen from designated parking space at {place}",
    ],
}

_BLOCK_WEIGHTS = {
    "Block A": 0.18,
    "Block B": 0.16,
    "Block C": 0.16,
    "Admin Block": 0.10,
    "Girls Hostel": 0.14,
    "Boys Hostel 1": 0.14,
    "Central Canteen": 0.05,
    "Cafeteria 2": 0.03,
    "Sports Ground & Lawns": 0.02,
    "Main Gate & Security": 0.02,
}

_CATEGORY_WEIGHTS = {
    "Classroom & Lab Infrastructure": 0.22,
    "Hostel & Residential Life": 0.20,
    "Electricity & Maintenance": 0.18,
    "Water Supply & Washrooms": 0.18,
    "Canteen & Food Quality": 0.12,
    "Campus Safety & Parking": 0.10,
}

REPORTED_DUPLICATE_FRACTION = 0.10

_AMBIGUOUS = [
    ("No water in washroom", "Water Supply & Washrooms"),
    ("Projector not working", "Classroom & Lab Infrastructure"),
    ("Corridor lights out", "Electricity & Maintenance"),
    ("Food has bad smell", "Canteen & Food Quality"),
    ("Basement parking completely dark", "Campus Safety & Parking"),
    ("Geyser cold in hostel", "Hostel & Residential Life"),
]

# Realistic spam and anomaly submissions to demonstrate fraud detection capabilities
_SPAM_ANOMALIES = [
    ("Click here to earn quick student income and win crypto lottery prize http://scam-campus.biz/deal", "Campus Safety & Parking"),
    ("asdfghjkl zxcvbnmqwerty test spam nothing broken here at all", "Classroom & Lab Infrastructure"),
    ("Buy discounted casino tokens and instant cash loans on telegram @pcu_student_deals", "Campus Safety & Parking"),
    ("test test test test test test test test test test test", "Electricity & Maintenance"),
    ("Pay for assignment thesis writing and hire proxy hacker for exams http://essayleak.com", "Classroom & Lab Infrastructure"),
    ("zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz", "Hostel & Residential Life"),
]


def _pick_location_details(category: str, block: str):
    """Determine realistic floor, room/lab number, and sub-location for PCU."""
    if block in ("Block A", "Block B", "Block C"):
        floor = random.choice(["Ground Floor", "1st Floor", "2nd Floor", "3rd Floor", "4th Floor", "5th Floor", "Basement / Parking"])
        if "Parking" in floor:
            room = f"{block} Underground Parking"
            sub_loc = "Basement Parking Bay"
        elif "Lab" in category or random.random() < 0.4:
            lab_num = random.randint(1, 6)
            room = f"Lab {lab_num} ({floor})"
            sub_loc = f"{floor} Computing & Tech Wing"
        else:
            floor_num = "G" if "Ground" in floor else floor[0]
            room_num = f"{floor_num}0{random.randint(1, 9)}"
            room = f"Room {room_num}"
            sub_loc = f"{floor} Lecture Hall Wing"

    elif block == "Admin Block":
        floor = random.choice(["Ground Floor", "1st Floor", "2nd Floor", "3rd Floor", "Basement / Parking"])
        if "Parking" in floor:
            room = "Admin Basement Parking"
            sub_loc = "Faculty & Visitor Parking"
        else:
            room = random.choice(["Exam Control Room", "Accounts Section", "Registrar Desk", "Dean Cabin", "Admissions Hall", "Conference Room"])
            sub_loc = f"{floor} Administrative Wing"

    elif block in ("Girls Hostel", "Boys Hostel 1"):
        floor = random.choice(["Ground Floor", "1st Floor", "2nd Floor", "3rd Floor", "4th Floor"])
        floor_num = "G" if "Ground" in floor else floor[0]
        room = f"Hostel Room {floor_num}{random.randint(10, 45)}"
        sub_loc = random.choice([f"{floor} Residential Wing", f"{floor} Washroom Block", "Common Study Hall", "Mess & Dining Hall", "Warden Section"])

    elif block in ("Central Canteen", "Cafeteria 2"):
        floor = "Ground Floor"
        room = random.choice(["Serving Counter 1", "Serving Counter 2", "Main Dining Hall", "Kitchen Section", "Beverage Counter"])
        sub_loc = "Dining Area"

    elif block == "Sports Ground & Lawns":
        floor = "Ground Floor"
        room = random.choice(["Cricket Pitch & Nets", "Basketball Court", "Football Ground", "Athletics Lawn"])
        sub_loc = "Outdoor Sports Complex"

    else:  # Main Gate & Security
        floor = "Ground Floor"
        room = random.choice(["Main Gate Security Cabin", "Boom Barrier Post", "Visitor Registration Desk", "Bus Bay Checkpoint"])
        sub_loc = "Campus Main Entry"

    return floor, room, sub_loc


def _random_time(now: datetime) -> str:
    """Weight recent days more heavily."""
    days_back = int(random.random() ** 1.4 * 14)
    dt = now - timedelta(days=days_back,
                         hours=random.randint(0, 23),
                         minutes=random.randint(0, 59))
    return dt.isoformat(timespec="seconds")


def _generate(n: int = 180) -> list:
    now = datetime.now()
    out = []
    used = []
    used_keys = set()

    def _finish(text, category, block, floor, room, sub_loc):
        used.append((text, category, block, floor, room, sub_loc))
        title = " ".join(text.split()[:6]).rstrip(",").capitalize() + "..."
        out.append({
            "ward": block,
            "floor": floor,
            "room_number": room,
            "sub_location": sub_loc,
            "category": category,
            "title": title,
            "description": text,
            "source": random.choice(SOURCES),
            "created_at": _random_time(now),
        })

    while len(out) < n:
        if random.random() < 0.035:
            # Realistic spam / anomaly test cases
            text, category = random.choice(_SPAM_ANOMALIES)
            block = random.choice(CAMPUS_BLOCKS[:6])
            floor, room, sub_loc = _pick_location_details(category, block)
            _finish(f"{text} ({block})", category, block, floor, room, sub_loc)
        elif random.random() < 0.05:
            # Short / ambiguous test cases
            text, category = random.choice(_AMBIGUOUS)
            block = random.choice(CAMPUS_BLOCKS[:4])
            floor, room, sub_loc = _pick_location_details(category, block)
            _finish(f"{text} in {block} {room}", category, block, floor, room, sub_loc)
        elif used and random.random() < REPORTED_DUPLICATE_FRACTION:
            # Verbatim duplicate re-file
            text, category, block, floor, room, sub_loc = random.choice(used)
            _finish(text, category, block, floor, room, sub_loc)
        else:
            category = random.choices(list(_CATEGORY_WEIGHTS),
                                      weights=list(_CATEGORY_WEIGHTS.values()))[0]
            # Tailor block by category
            if category == "Hostel & Residential Life":
                block = random.choice(["Girls Hostel", "Boys Hostel 1"])
            elif category == "Canteen & Food Quality":
                block = random.choice(["Central Canteen", "Cafeteria 2"])
            elif category == "Classroom & Lab Infrastructure":
                block = random.choice(["Block A", "Block B", "Block C", "Admin Block"])
            else:
                block = random.choices(list(_BLOCK_WEIGHTS),
                                       weights=list(_BLOCK_WEIGHTS.values()))[0]

            floor, room, sub_loc = _pick_location_details(category, block)
            place = f"{block} ({room}, {floor})"

            idx = random.randrange(len(_TEMPLATES[category]))
            key = (category, idx, block, room)
            if key in used_keys:
                continue
            used_keys.add(key)
            text = _TEMPLATES[category][idx].format(place=place)
            _finish(text, category, block, floor, room, sub_loc)
    return out


def seed_if_empty(n: int = 180, force: bool = False) -> int:
    """Populate the database with processed sample complaints if empty or forced."""
    if not force and database.complaint_count() > 0:
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

        from .hotspot_analyzer import assign_coordinates
        from .fraud_detector import check_complaint
        lat, lon = assign_coordinates(c["ward"], c["description"])
        is_susp, susp_score, susp_reason = check_complaint(c["description"], similar)

        database.insert_complaint({
            "source": c["source"],
            "ward": c["ward"],
            "floor": c.get("floor", ""),
            "room_number": c.get("room_number", ""),
            "sub_location": c.get("sub_location", ""),
            "category": cat,
            "title": c["title"],
            "description": c["description"],
            "priority": priority,
            "confidence": conf,
            "is_duplicate": c.get("is_duplicate", 0),
            "duplicate_of": c.get("duplicate_of"),
            "is_suspicious": int(is_susp),
            "suspicion_score": susp_score,
            "suspicion_reason": susp_reason,
            "lat": lat,
            "lon": lon,
            "created_at": c["created_at"],
        })
        inserted += 1
    return inserted


def reseed_database(n: int = 180) -> int:
    """Wipe current complaints and seed fresh PCU data."""
    with database.get_conn() as conn:
        conn.execute("DELETE FROM complaints")
        conn.execute("DELETE FROM reports")
    return seed_if_empty(n=n, force=True)
