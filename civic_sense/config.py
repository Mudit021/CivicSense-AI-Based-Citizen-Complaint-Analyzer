"""Central configuration for CivicSense.

All tunable knobs (paths, categories, thresholds, optional GenAI hooks) live here
so the rest of the codebase stays clean and the demo is easy to configure.
"""
import os
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"
REPORTS_DIR = DATA_DIR / "reports"
UPLOADS_DIR = BASE_DIR / "static" / "uploads"
DB_PATH = DATA_DIR / "civicsense.db"
CLASSIFIER_PATH = MODELS_DIR / "classifier.joblib"
METRICS_PATH = MODELS_DIR / "metrics.json"

for _p in (DATA_DIR, MODELS_DIR, REPORTS_DIR, UPLOADS_DIR):
    _p.mkdir(parents=True, exist_ok=True)

ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "webp", "gif"}

# ---------------------------------------------------------------------------
# PCU Campus Domain Constants (Pimpri Chinchwad University, Sate, Maval)
# ---------------------------------------------------------------------------
UNIVERSITY_NAME = "Pimpri Chinchwad University (PCU)"
CAMPUS_LOCATION = "Sate, Maval, Pune - 412106"
PCU_COORDINATES = {"lat": 18.749034, "lon": 73.606889}

CATEGORIES = [
    "Classroom & Lab Infrastructure",
    "Hostel & Residential Life",
    "Electricity & Maintenance",
    "Water Supply & Washrooms",
    "Canteen & Food Quality",
    "Campus Safety & Parking",
]
PRIORITIES = ["High", "Medium", "Low"]

CAMPUS_BLOCKS = [
    "A Block",
    "B Block",
    "C Block",
    "Admin Block",
    "Girls Hostel",
    "Boys Hostel",
    "Central Canteen",
    "Cafeteria",
    "Lawn 1",
    "Lawn 2",
    "Sports Lawn",
    "Main Gate 1 (Entry)",
    "Main Gate 2 (Exit)",
]

# Aliases for backward compatibility with existing records
LEGACY_BLOCK_ALIASES = {
    "Block A": "A Block",
    "Block B": "B Block",
    "Block C": "C Block",
    "Boys Hostel 1": "Boys Hostel",
    "Cafeteria 2": "Cafeteria",
    "Sports Ground & Lawns": "Sports Lawn",
    "Main Gate & Security": "Main Gate 1 (Entry)",
    "Main Gate": "Main Gate 1 (Entry)",
    "Gate 1": "Main Gate 1 (Entry)",
    "Gate 2": "Main Gate 2 (Exit)",
    "main gate 1(entry)": "Main Gate 1 (Entry)",
    "main gate 2(exit)": "Main Gate 2 (Exit)",
    "main gate 1 (entry)": "Main Gate 1 (Entry)",
    "main gate 2 (exit)": "Main Gate 2 (Exit)",
}

# Retain WARDS as superset for backward compatibility across database and queries
WARDS = list(dict.fromkeys(CAMPUS_BLOCKS + list(LEGACY_BLOCK_ALIASES.keys())))


FLOORS = [
    "Basement / Parking",
    "Ground Floor",
    "1st Floor",
    "2nd Floor",
    "3rd Floor",
    "4th Floor",
    "5th Floor",
    "Terrace",
]

SOURCES = ["Student Portal", "PCU Mobile App", "Hostel Desk", "Campus Helpdesk", "QR Code Scanner"]
STATUSES = ["Open", "In Progress", "Resolved"]

# ---------------------------------------------------------------------------
# Optional Generative AI hook
# Leave OPENAI_API_KEY empty to use the built-in template digest engine
# (fully offline). When set, the weekly digest is generated with an LLM.
# ---------------------------------------------------------------------------
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

# Optional heavy transformer classifier (requires torch + transformers).
# The default sklearn TF-IDF + SVM classifier is lightweight and always works.
USE_TRANSFORMERS = os.environ.get("USE_TRANSFORMERS", "0") == "1"
TRANSFORMER_MODEL = os.environ.get("TRANSFORMER_MODEL", "distilbert-base-uncased")

# ---------------------------------------------------------------------------
# Pipeline tuning
# ---------------------------------------------------------------------------
DUPLICATE_SIMILARITY = 0.92      # normalized-text similarity ratio for dedup
REPORT_WINDOW_DAYS = 7           # weekly digest window
TREND_DAYS = 14                  # dashboard trend window
