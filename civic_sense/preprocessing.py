"""Text preprocessing pipeline (paper section 3.2).

Stages implemented: text cleaning, tokenization, lemmatization,
stop-word removal, locality-aware duplicate detection, and incident clustering.
Every stage degrades gracefully (no hard dependency on NLTK data being present).

Duplicate detection and incident clustering both use the same ``similarity``
function. When the sentence-transformers stack is available, similarity uses
all-MiniLM-L6-v2 cosine distance; otherwise it falls back to difflib
SequenceMatcher on normalized text. Duplicate detection is locality-aware
(same ward, optional category); incident clustering additionally requires the
embedding path because the difflib fallback is too coarse for grouping.
"""
import re
import numpy as np
from difflib import SequenceMatcher
from typing import Optional, Tuple, List

from .config import DUPLICATE_SIMILARITY
from . import database

# Attempt to import advanced ML libraries; fallback to basic similarity if unavailable
try:
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity
    _HAS_ML = True
    # all-MiniLM-L6-v2 is lightweight and efficient for short civic complaints.
    # If the installed transformers/torch stack is too old to import
    # sentence_transformers at all, this import fails and we fall back below.
    _MODEL = SentenceTransformer('all-MiniLM-L6-v2')
except Exception:
    _HAS_ML = False
    _MODEL = None

# --- stop words (NLTK with a small built-in fallback) -----------------------
# Domain-level noise words (locations/time/connectors) that add no signal
# to trending-keyword analysis or digests.
_DOMAIN_NOISE = {
    # time / connectors / generic modifiers
    "near", "area", "street", "day", "days", "week", "since", "yesterday",
    "today", "tomorrow", "morning", "evening", "night", "please", "also",
    "every", "many", "much", "one", "two", "first", "last", "get", "got",
    "need", "needs", "want", "come", "going", "keep", "left", "back",
    "around", "inside", "outside", "really", "very", "quite", "still",
    "well", "time", "times", "whole", "long", "make", "made", "old",
    "new", "completely", "half", "ha", "recent", "recently",
    # generic location words (they are ward metadata, not complaint themes)
    "school", "park", "market", "hospital", "temple", "bus", "stop",
    "playground", "hall", "railway", "station", "lake", "view", "colony",
    "fort", "church", "stadium", "pump", "petrol", "corner", "lane",
    "block", "junction", "side", "behind", "front", "opposite", "overhead",
    "open", "ground", "closed", "main",
}

try:
    from nltk.corpus import stopwords as _nltk_stopwords
    _STOPWORDS = set(_nltk_stopwords.words("english")) | _DOMAIN_NOISE
except Exception:  # pragma: no cover - offline fallback
    _STOPWORDS = {
        "a", "an", "the", "and", "or", "but", "is", "are", "was", "were", "be",
        "been", "being", "to", "of", "in", "on", "at", "for", "with", "from",
        "by", "as", "it", "its", "this", "that", "these", "those", "i", "we",
        "you", "he", "she", "they", "my", "our", "your", "his", "her", "their",
        "has", "have", "had", "do", "does", "did", "not", "no", "so", "if",
        "then", "than", "too", "very", "can", "will", "just", "about", "into",
        "over", "after", "before", "between", "out", "up", "down", "off", "again",
        "there", "here", "when", "where", "why", "how", "all", "any", "both",
        "each", "few", "more", "most", "other", "some", "such", "only", "own",
        "same", "what", "which", "who", "whom", "during", "because", "until",
        "while", "also", "still", "since", "s", "t", "don", "now", "get", "got",
        "one", "two", "last", "first", "every", "lot", "much", "many",
        } | _DOMAIN_NOISE

# --- lemmatizer (NLTK WordNet, with a regex POS guess to avoid the
#     perceptron tagger download) -------------------------------------------
try:
    from nltk.stem import WordNetLemmatizer
    _LEMMATIZER = WordNetLemmatizer()
    _HAS_LEMMATIZER = True
except Exception:  # pragma: no cover
    _LEMMATIZER = None
    _HAS_LEMMATIZER = False

_TOKEN_RE = re.compile(r"[a-z][a-z']*")
_URL_RE = re.compile(r"https?://\S+|www\.\S+")
_EMAIL_RE = re.compile(r"\S+@\S+")
_NOISE_RE = re.compile(r"[^a-z0-9\s]")
_MULTI_SPACE_RE = re.compile(r"\s+")


def clean_text(text: str) -> str:
    """Lowercase and strip URLs, emails, symbols and repeated whitespace."""
    t = (text or "").lower()
    t = _URL_RE.sub(" ", t)
    t = _EMAIL_RE.sub(" ", t)
    t = _NOISE_RE.sub(" ", t)
    t = _MULTI_SPACE_RE.sub(" ", t)
    return t.strip()


def tokenize(text: str) -> list:
    """Simple, dependency-free word tokenizer."""
    return _TOKEN_RE.findall(clean_text(text))


def _guess_pos(word: str) -> str:
    """Rough part-of-speech guess for lemmatization (n = noun, v = verb)."""
    if word.endswith(("ing", "ed")):
        return "v"
    return "n"


def lemmatize(tokens: list) -> list:
    """Reduce words to base forms using WordNet lemmatization."""
    if not _HAS_LEMMATIZER:
        return tokens
    return [_LEMMATIZER.lemmatize(t, _guess_pos(t)) for t in tokens]


def remove_stopwords(tokens: list) -> list:
    return [t for t in tokens if t not in _STOPWORDS and len(t) > 1]


def normalize(text: str) -> str:
    """Full preprocessing pipeline -> canonical space-joined string."""
    return " ".join(remove_stopwords(lemmatize(tokenize(text))))


def similarity(a: str, b: str) -> float:
    """Compute similarity between two texts.

    Uses Semantic Embeddings (Sentence-Transformers) if available,
    otherwise falls back to SequenceMatcher.
    """
    if _HAS_ML and _MODEL:
        embeddings = _MODEL.encode([a, b])
        return float(cosine_similarity([embeddings[0]], [embeddings[1]])[0][0])

    return SequenceMatcher(None, normalize(a), normalize(b)).ratio()


def find_duplicate(description: str, category: Optional[str] = None, ward: Optional[str] = None) -> Optional[Tuple[int, float]]:
    """Return (id, ratio) of the most similar recent complaint, or None.

    Mirrors the paper's 'duplicate removal' preprocessing stage, now enhanced
    with semantic similarity to detect paraphrased repeats.

    The search is scoped by ward (and optionally category) so a complaint is
    only marked duplicate against prior reports of the same type of issue in
    the same locality. Cross-ward re-use is treated as noise, not spam.

    When sentence-transformers is available, similarity uses its embeddings;
    otherwise the function falls back to SequenceMatcher on normalized text.
    """
    best = None
    rows = database.recent_complaints(limit=300)
    for c in rows:
        if ward and c["ward"] != ward:
            continue
        if category and c["category"] != category:
            continue
        if c["is_duplicate"]:
            continue
        r = similarity(description, c["description"])
        if r >= DUPLICATE_SIMILARITY and (best is None or r > best[1]):
            best = (c["id"], round(r, 3))
    return best


def detect_incident_cluster(description: str, ward: Optional[str] = None,
                            category: Optional[str] = None,
                            threshold: float = 0.55) -> Optional[int]:
    """Group complaints describing the same incident based on text similarity.

    Returns the ``cluster_id`` of the cluster this complaint belongs to, or
    ``None`` when it does not match any existing incident.

    Clusters are scoped to the same locality (and optionally the same
    category), so the same phrasing in two different wards is treated as a
    coincidence rather than one incident. This also means the function is
    safe to call for every submission.

    Similarity uses sentence-transformers embeddings when that stack is
    available, and otherwise falls back to the difflib-based ``similarity()``
    implementation, so incident grouping still works in environments where the
    transformer stack cannot be imported.
    """
    best_cluster_id = None
    max_sim = 0.0

    for c in database.recent_complaints(limit=300):
        if c.get("is_duplicate"):
            continue
        if ward and c.get("ward") != ward:
            continue
        if category and c.get("category") != category:
            continue

        sim = similarity(description, c["description"])
        # Below the duplicate threshold (those are handled by find_duplicate)
        # but similar enough to describe the same underlying incident.
        if DUPLICATE_SIMILARITY > sim >= threshold:
            if sim > max_sim:
                max_sim = sim
                # Join an existing cluster when one exists, otherwise start a
                # new cluster anchored on this record's id.
                best_cluster_id = c.get("cluster_id") or c["id"]

    return best_cluster_id
