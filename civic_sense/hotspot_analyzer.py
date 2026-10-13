"""Geospatial hotspot analyzer for Pimpri Chinchwad University (PCU), Sate, Maval.

Implements campus building coordinate mapping, floor/parking micro-location offsets,
and building density intensity visualization for interactive Leaflet maps.
"""
import hashlib
import random
from .config import CAMPUS_BLOCKS, CATEGORIES, PCU_COORDINATES

# Accurate geographic coordinates for PCU Campus buildings (Sate, Maval, Pune)
# Centered at 18.749034, 73.606889
# Satellite-calibrated geographic coordinates for PCU Campus buildings (Sate, Maval, Pune)
# Perfectly aligned with Google Maps satellite aerial layout
CAMPUS_GEO_DATA = {
    # 1. Admin Block (Central PCU administrative building)
    "Admin Block": {
        "lat": 18.748911, "lon": 73.607058,
        "name": "Administrative Headquarters & Exam Cell",
        "radius": 36,
        "type": "Administrative"
    },
    # 2. Central Canteen (Between Lawn 2 and Admin Block)
    "Central Canteen": {
        "lat": 18.748958, "lon": 73.606766,
        "name": "Central Campus Canteen & Dining Hall",
        "radius": 28,
        "type": "Dining"
    },
    # 3. A Block (Northwest academic building, west of Lawn 2)
    "A Block": {
        "lat": 18.749007, "lon": 73.605764,
        "name": "Academic Block A (Engineering & Tech Labs)",
        "radius": 40,
        "type": "Academic"
    },
    # 4. B Block (Academic building directly south of A Block)
    "B Block": {
        "lat": 18.748326, "lon": 73.605783,
        "name": "Academic Block B (Management & Media)",
        "radius": 40,
        "type": "Academic"
    },
    # 5. Cafeteria (Dining facility immediately south of B Block)
    "Cafeteria": {
        "lat": 18.747957, "lon": 73.605701,
        "name": "Cafeteria & Student Food Court",
        "radius": 24,
        "type": "Dining"
    },
    # 6. C Block (Southwest building, below Cafeteria & Sports Lawn)
    "C Block": {
        "lat": 18.747520, "lon": 73.605866,
        "name": "Academic Block C (Sciences & Central Library)",
        "radius": 44,
        "type": "Academic"
    },
    # 7. Girls Hostel (Residential complex north of Central Canteen / Lawn 2)
    "Girls Hostel": {
        "lat": 18.749625, "lon": 73.606743,
        "name": "Girls Hostel Residence",
        "radius": 42,
        "type": "Residential"
    },
    # 8. Boys Hostel (Residential building in northeast along Mohitewadi Rd)
    "Boys Hostel": {
        "lat": 18.750219, "lon": 73.608119,
        "name": "Boys Hostel Residence",
        "radius": 40,
        "type": "Residential"
    },
    # 9. Lawn 1 (East courtyard between Admin Block and Mohitewadi Rd)
    "Lawn 1": {
        "lat": 18.748930, "lon": 73.607544,
        "name": "Campus Lawn 1 (East Quad)",
        "radius": 34,
        "type": "Recreation"
    },
    # 10. Lawn 2 (West quad between Central Canteen and A Block)
    "Lawn 2": {
        "lat": 18.749012, "lon": 73.606363,
        "name": "Campus Lawn 2 (West Quad)",
        "radius": 36,
        "type": "Recreation"
    },
    # 11. Sports Lawn (Central green field south of road, east of B Block)
    "Sports Lawn": {
        "lat": 18.748218, "lon": 73.606277,
        "name": "University Sports Lawn & Ground",
        "radius": 44,
        "type": "Recreation"
    },
    # 12. Main Gate 1 (Entry) (White gate structure on Mohitewadi Rd on the side of C Block)
    "Main Gate 1 (Entry)": {
        "lat": 18.748580, "lon": 73.607551,
        "name": "Main Gate 1 (Entry - C Block Side)",
        "radius": 24,
        "type": "Security"
    },
    # 13. Main Gate 2 (Exit) (White gate structure on Mohitewadi Rd on the side of Girls Hostel)
    "Main Gate 2 (Exit)": {
        "lat": 18.749231, "lon": 73.607650,
        "name": "Main Gate 2 (Exit - Girls Hostel Side)",
        "radius": 24,
        "type": "Security"
    },
}

# Aliases for backward compatibility with existing records
CAMPUS_GEO_DATA["Block A"] = CAMPUS_GEO_DATA["A Block"]
CAMPUS_GEO_DATA["Block B"] = CAMPUS_GEO_DATA["B Block"]
CAMPUS_GEO_DATA["Block C"] = CAMPUS_GEO_DATA["C Block"]
CAMPUS_GEO_DATA["Boys Hostel 1"] = CAMPUS_GEO_DATA["Boys Hostel"]
CAMPUS_GEO_DATA["Cafeteria 2"] = CAMPUS_GEO_DATA["Cafeteria"]
CAMPUS_GEO_DATA["Sports Ground & Lawns"] = CAMPUS_GEO_DATA["Sports Lawn"]
CAMPUS_GEO_DATA["Main Gate & Security"] = CAMPUS_GEO_DATA["Main Gate 1 (Entry)"]
CAMPUS_GEO_DATA["Main Gate"] = CAMPUS_GEO_DATA["Main Gate 1 (Entry)"]
CAMPUS_GEO_DATA["Gate 1"] = CAMPUS_GEO_DATA["Main Gate 1 (Entry)"]
CAMPUS_GEO_DATA["Gate 2"] = CAMPUS_GEO_DATA["Main Gate 2 (Exit)"]
CAMPUS_GEO_DATA["main gate 1(entry)"] = CAMPUS_GEO_DATA["Main Gate 1 (Entry)"]
CAMPUS_GEO_DATA["main gate 2(exit)"] = CAMPUS_GEO_DATA["Main Gate 2 (Exit)"]
CAMPUS_GEO_DATA["main gate 1 (entry)"] = CAMPUS_GEO_DATA["Main Gate 1 (Entry)"]
CAMPUS_GEO_DATA["main gate 2 (exit)"] = CAMPUS_GEO_DATA["Main Gate 2 (Exit)"]


# Micro-offsets for specific facilities within buildings
_FACILITY_OFFSETS = {
    "parking": (-0.00015, -0.00012),
    "basement": (-0.00014, -0.00010),
    "lab": (0.00008, -0.00008),
    "washroom": (-0.00006, 0.00009),
    "toilet": (-0.00006, 0.00009),
    "restroom": (-0.00006, 0.00009),
    "canteen": (0.00010, 0.00010),
    "mess": (0.00012, 0.00008),
    "library": (0.00005, -0.00005),
    "classroom": (0.00006, 0.00006),
    "seminar": (0.00009, 0.00004),
    "terrace": (0.00002, 0.00002),
}


def assign_coordinates(block_name: str, description: str = "", floor: str = "", room: str = "") -> tuple:
    """Generate precise latitude and longitude coordinates for a campus complaint."""
    base = CAMPUS_GEO_DATA.get(block_name, CAMPUS_GEO_DATA["Admin Block"])
    lat, lon = base["lat"], base["lon"]

    # Match facility keywords
    full_context = f"{description} {floor} {room}".lower()
    matched_offset = None
    for fac, offset in _FACILITY_OFFSETS.items():
        if fac in full_context:
            matched_offset = offset
            break

    # Floor altitude / micro-drift
    floor_drift = 0.0
    if "1st" in full_context or "first" in full_context:
        floor_drift = 0.00002
    elif "2nd" in full_context or "second" in full_context:
        floor_drift = 0.00004
    elif "3rd" in full_context or "third" in full_context:
        floor_drift = 0.00006
    elif "4th" in full_context or "fourth" in full_context:
        floor_drift = 0.00008
    elif "5th" in full_context or "fifth" in full_context:
        floor_drift = 0.00010
    elif "basement" in full_context or "parking" in full_context:
        floor_drift = -0.00005

    # Hash-based micro-jitter ensures consistency for identical rooms/text
    h = int(hashlib.md5(f"{block_name}:{room}:{floor}:{description}".encode()).hexdigest()[:6], 16)
    jitter_lat = ((h % 1000) / 1000.0 - 0.5) * 0.00012
    jitter_lon = (((h // 1000) % 1000) / 1000.0 - 0.5) * 0.00012

    if matched_offset:
        lat += matched_offset[0] + jitter_lat + floor_drift
        lon += matched_offset[1] + jitter_lon
    else:
        lat += jitter_lat + floor_drift
        lon += jitter_lon

    return round(lat, 6), round(lon, 6)


def get_hotspot_summary(ward_counts_data: list) -> list:
    """Calculate campus hotspot intensity, colors, and map circle radii for each building.

    Args:
        ward_counts_data: list of dicts with block counts from database.ward_counts()
    """
    from .config import LEGACY_BLOCK_ALIASES

    # Normalize counts from legacy aliases into canonical block names
    normalized_counts = {}
    total_complaints = sum(w.get("total", 0) for w in ward_counts_data)

    for w in ward_counts_data:
        canonical = LEGACY_BLOCK_ALIASES.get(w["ward"], w["ward"])
        if canonical not in normalized_counts:
            normalized_counts[canonical] = {
                "total": 0,
                "top_category": w.get("top_category", "Classroom & Lab Infrastructure"),
                "share": 0.0,
            }
        normalized_counts[canonical]["total"] += w["total"]
        if w.get("total", 0) > 0:
            normalized_counts[canonical]["top_category"] = w.get("top_category", normalized_counts[canonical]["top_category"])

    # Recompute share based on normalized totals
    for block_data in normalized_counts.values():
        block_data["share"] = round((block_data["total"] / max(1, total_complaints)) * 100, 1)

    out = []
    for block in CAMPUS_BLOCKS:
        geo = CAMPUS_GEO_DATA.get(block, CAMPUS_GEO_DATA["Admin Block"])
        w_info = normalized_counts.get(block, {
            "total": 0,
            "top_category": "Classroom & Lab Infrastructure",
            "share": 0.0
        })
        total = w_info["total"]

        # Scaled thresholds for university campus building density
        if total >= 25:
            intensity = "Critical"
            color = "#e5484d"  # Red
            fill_opacity = 0.45
            radius = geo["radius"] * 1.3
        elif total >= 15:
            intensity = "High"
            color = "#f5a524"  # Amber
            fill_opacity = 0.38
            radius = geo["radius"] * 1.15
        elif total >= 8:
            intensity = "Moderate"
            color = "#3b5bdb"  # Blue
            fill_opacity = 0.28
            radius = geo["radius"]
        else:
            intensity = "Low"
            color = "#30a46c"  # Green
            fill_opacity = 0.20
            radius = geo["radius"] * 0.85

        out.append({
            "ward": block,
            "name": geo["name"],
            "type": geo["type"],
            "lat": geo["lat"],
            "lon": geo["lon"],
            "total": total,
            "top_category": w_info["top_category"],
            "share": w_info.get("share", 0.0),
            "intensity": intensity,
            "color": color,
            "fill_opacity": fill_opacity,
            "radius": round(radius, 1),
        })

    return sorted(out, key=lambda x: x["total"], reverse=True)
