"""Central configuration for CivicSense.

All tunable knobs live here — paths, domain constants, optional GenAI hooks and
pipeline thresholds — so the rest of the codebase stays clean and the demo is
easy to configure.

Domain constants
----------------
CATEGORIES, WARDS, SOURCES, STATUSES come from the base paper. PRIORITIES are
the three tiers used by the prioritizer (High / Medium / Low).

Optional AI hooks
-----------------
- OPENAI_API_KEY / OPENAI_MODEL: switch the weekly digest from the offline
  template engine to a generative LLM.
- USE_TRANSFORMERS / TRANSFORMER_MODEL: switch classification from TF-IDF +
  LinearSVC to zero-shot DistilBERT (requires a compatible torch + transformers
  stack).

Pipeline tuning
---------------
- DUPLICATE_SIMILARITY: normalized-text similarity ratio at which a new complaint
  is considered a duplicate of a recent one (scope: same ward + same category).
- REPORT_WINDOW_DAYS: weekly digest window.
- TREND_DAYS: dashboard trend window.

Fraud / scenario knobs
---------------------
- Fraud scoring lives in `civic_sense/fraud_detector.py` (`FREQ_THRESHOLD`,
  `SIM_THRESHOLD`) and is intentionally separate from duplicate detection.
- The demo seed scenarios live in `civic_sense/seed_data.py` (fraud-alert burst,
  incident-hotspot cluster) and are labelled internally with a `scenario` field.
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
WARDS = ["PCMC", "Chinchwad", "Vadgaon", "Maval", "Talegaon",
         "Akurdi", "Wakad", "Hinjewadi", "Katraj", "Kamseth"]
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
# Duplicate threshold. When sentence-transformers is available, similarity is
# cosine distance over all-MiniLM-L6-v2 embeddings; otherwise the difflib
# SequenceMatcher fallback is used. The default 0.92 keeps near-paraphrase
# duplicates under the same umbrella while still allowing genuinely distinct
# reports through.
DUPLICATE_SIMILARITY = 0.92

# Weekly digest window (the paper's "weekly" cadence).
REPORT_WINDOW_DAYS = 7

# Dashboard trend window.
TREND_DAYS = 14
