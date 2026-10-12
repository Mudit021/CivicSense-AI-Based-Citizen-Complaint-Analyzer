"""Summarization & report generation (paper section 3.5).

1. Extractive summarization of individual complaint clusters.
2. Weekly digests in the style of the paper's example:
   "There are 42 road complaints in ward 5 this week primarily touching on
    potholes and damaged footpaths. Priority: High."

When OPENAI_API_KEY is configured, the digest is written by a generative LLM
with the statistics as context; otherwise the built-in template engine
produces deterministic, offline digests (still "generative" in the sense of
producing natural-language narrative from structured statistics).

The generated digest is stored in the reports table through the Flask route in
app.py; PDF and Excel rendering happen in civic_sense/reports.py.
"""
import re
import urllib.request
import json
from collections import Counter
from datetime import datetime, timedelta

from . import database
from .config import OPENAI_API_KEY, OPENAI_MODEL, CATEGORIES, REPORT_WINDOW_DAYS
from .preprocessing import normalize, tokenize, remove_stopwords

_SENT_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")


def sentence_tokenize(text: str) -> list:
    return [s.strip() for s in _SENT_SPLIT_RE.split(text or "") if len(s.strip()) > 10]


def extractive_summary(text: str, n: int = 2) -> str:
    """Frequency-based extractive summary (lightweight TextRank substitute)."""
    sentences = sentence_tokenize(text)
    if len(sentences) <= n:
        return " ".join(sentences) or text
    freq = Counter(remove_stopwords(tokenize(normalize(text))))
    if not freq:
        return " ".join(sentences[:n])
    max_f = max(freq.values())
    scored = []
    for i, s in enumerate(sentences):
        words = remove_stopwords(tokenize(normalize(s)))
        score = sum(freq.get(w, 0) for w in words) / max(1, len(words)) / max_f
        scored.append((i, score))
    scored.sort(key=lambda x: x[1], reverse=True)
    top_idx = sorted(i for i, _ in scored[:n])
    return " ".join(sentences[i] for i in top_idx)


# ---------------------------------------------------------------------------
# Weekly digest
# ---------------------------------------------------------------------------
def _ward_statements(rows) -> list:
    """Per-ward narrative lines in the paper's digest style."""
    ward_cat = Counter((r["ward"], r["category"]) for r in rows)
    ward_total = Counter(r["ward"] for r in rows)
    ward_prio = Counter((r["ward"], r["priority"]) for r in rows)
    out = []
    for ward, total in ward_total.most_common(5):
        top_cat = max(CATEGORIES, key=lambda c: ward_cat.get((ward, c), 0))
        top_n = ward_cat.get((ward, top_cat), 0)
        high = ward_prio.get((ward, "High"), 0)
        pct = round(high / max(1, total) * 100)
        out.append(
            f"{ward} recorded {total} complaints this week, predominantly "
            f"{top_cat.lower()} ({top_n} reports). {high} of them ({pct}%) were "
            f"flagged High Priority and need immediate attention."
        )
    return out


def _overview(rows, period_label: str) -> str:
    total = len(rows)
    by_cat = Counter(r["category"] for r in rows)
    by_prio = Counter(r["priority"] for r in rows)
    top_cat = max(CATEGORIES, key=lambda c: by_cat.get(c, 0))
    top_words = _top_terms(rows, 6)
    return (
        f"During {period_label}, {total} citizen complaints were received and "
        f"automatically processed. The dominant category was {top_cat} "
        f"({by_cat.get(top_cat, 0)} reports), followed by {_fmt_cats(by_cat, top_cat)}. "
        f"Priority-wise, {by_prio.get('High', 0)} complaints were High, "
        f"{by_prio.get('Medium', 0)} Medium and {by_prio.get('Low', 0)} Low. "
        f"Recurring themes include: {', '.join(top_words)}."
    )


def _recommendations(rows) -> str:
    ward_cat = Counter((r["ward"], r["category"]) for r in rows)
    ward_total = Counter(r["ward"] for r in rows)
    if not ward_total:
        return "No complaints in this window."
    hotspot = ward_total.most_common(1)[0][0]
    cat = max(CATEGORIES, key=lambda c: ward_cat.get((hotspot, c), 0))
    return (
        f"Resource allocation suggestion: prioritise {hotspot}, the current "
        f"hotspot for {cat.lower()} issues, and schedule preventive maintenance "
        f"based on the recurring patterns above."
    )


def _top_terms(rows, n=6):
    counter = Counter()
    for r in rows:
        counter.update(remove_stopwords(tokenize(normalize(r["description"]))))
    return [w for w, _ in counter.most_common(n)]


def _fmt_cats(by_cat, skip, limit=2):
    cats = [(c, n) for c, n in by_cat.items() if c != skip]
    cats.sort(key=lambda x: x[1], reverse=True)
    names = [f"{c} ({n})" for c, n in cats[:limit]]
    return ", ".join(names) if names else "others"


def _template_digest(rows, period_label: str) -> str:
    if not rows:
        return f"No complaints were recorded during {period_label}."
    parts = [
        _overview(rows, period_label),
        "",
        "Locality-level highlights:",
        *[f"  - {s}" for s in _ward_statements(rows)],
        "",
        _recommendations(rows),
    ]
    return "\n".join(parts)


def _llm_digest(rows, period_label: str, stats_summary: str) -> str:
    """Optional generative-AI digest via the OpenAI-compatible API."""
    prompt = (
        "You are an urban governance analyst. Write a concise weekly civic "
        "complaint digest for municipal officers based only on the statistics "
        "provided. Use clear ward-level highlights and end with a resource "
        "allocation recommendation. Keep it under 180 words.\n\n"
        f"Period: {period_label}\n{stats_summary}"
    )
    body = json.dumps({
        "model": OPENAI_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.4,
        "max_tokens": 350,
    }).encode()
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=body,
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {OPENAI_API_KEY}"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode())
        return data["choices"][0]["message"]["content"].strip()


def generate_weekly_report(days: int = REPORT_WINDOW_DAYS) -> dict:
    """Build the weekly digest: stats + natural-language summary."""
    end = datetime.now()
    start = end - timedelta(days=days)
    start_s, end_s = start.isoformat(timespec="seconds"), end.isoformat(timespec="seconds")
    rows = database.complaints_in_period(start_s, end_s)
    period_label = f"{start.strftime('%B %d')} – {end.strftime('%B %d, %Y')}"

    by_cat = Counter(r["category"] for r in rows)
    by_prio = Counter(r["priority"] for r in rows)
    by_ward = Counter(r["ward"] for r in rows)
    stats_summary = (
        f"Total: {len(rows)} | Categories: {dict(by_cat)} | "
        f"Priorities: {dict(by_prio)} | Top wards: "
        f"{dict(by_ward.most_common(5))}"
    )

    if OPENAI_API_KEY:
        try:
            summary = _llm_digest(rows, period_label, stats_summary)
        except Exception as exc:
            print(f"[CivicSense] LLM digest failed ({exc}); using template engine.")
            summary = _template_digest(rows, period_label)
    else:
        summary = _template_digest(rows, period_label)

    return {
        "period_start": start_s,
        "period_end": end_s,
        "title": f"Weekly Civic Complaint Digest — {period_label}",
        "summary": summary,
        "stats": {
            "total": len(rows),
            "by_category": {c: by_cat.get(c, 0) for c in CATEGORIES},
            "by_priority": dict(by_prio),
            "by_ward": dict(by_ward),
        },
        "rows": rows,
    }
