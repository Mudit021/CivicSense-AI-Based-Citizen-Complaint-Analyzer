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
DB_PATH = DATA_DIR / "civicsense.db"
CLASSIFIER_PATH = MODELS_DIR / "classifier.joblib"
METRICS_PATH = MODELS_DIR / "metrics.json"

for _p in (DATA_DIR, MODELS_DIR, REPORTS_DIR):
    _p.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Domain constants (from the base paper, Table 1)
# ---------------------------------------------------------------------------
CATEGORIES = ["Roads", "Electricity", "Water Supply", "Waste Management", "Public Safety"]
PRIORITIES = ["High", "Medium", "Low"]
WARDS = [f"Ward {i}" for i in range(1, 11)]
SOURCES = ["Mobile App", "Web Portal", "Email", "Call Center", "Social Media"]
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
