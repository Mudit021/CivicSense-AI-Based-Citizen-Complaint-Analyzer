"""SQLite persistence layer for CivicSense complaints and reports.

Complaints table mirrors the paper's "central database (PostgreSQL or MongoDB)"
concept; SQLite keeps the demo self-contained and portable.
"""
import sqlite3
from collections import Counter
from contextlib import contextmanager
from datetime import datetime, timedelta

from .config import DB_PATH, CATEGORIES, PRIORITIES

SCHEMA = """
CREATE TABLE IF NOT EXISTS complaints (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    source        TEXT    NOT NULL DEFAULT 'Web Portal',
    ward          TEXT    NOT NULL,
    category      TEXT    NOT NULL,
    title         TEXT    NOT NULL,
    description   TEXT    NOT NULL,
    priority      TEXT    NOT NULL DEFAULT 'Medium',
    status        TEXT    NOT NULL DEFAULT 'Open',
    confidence    REAL,
    is_duplicate  INTEGER NOT NULL DEFAULT 0,
    duplicate_of  INTEGER,
    created_at    TEXT    NOT NULL,
    processed_at  TEXT
);

CREATE TABLE IF NOT EXISTS reports (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    period_start TEXT NOT NULL,
    period_end   TEXT NOT NULL,
    title        TEXT NOT NULL,
    summary      TEXT NOT NULL,
    format       TEXT NOT NULL DEFAULT 'weekly',
    created_at   TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_complaints_ward     ON complaints(ward);
CREATE INDEX IF NOT EXISTS idx_complaints_category ON complaints(category);
CREATE INDEX IF NOT EXISTS idx_complaints_created  ON complaints(created_at);
"""


@contextmanager
def get_conn():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_conn() as conn:
        conn.executescript(SCHEMA)


# ---------------------------------------------------------------------------
# Complaints
# ---------------------------------------------------------------------------
def insert_complaint(c: dict) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            """INSERT INTO complaints
                 (source, ward, category, title, description, priority, status,
                  confidence, is_duplicate, duplicate_of, created_at, processed_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (c["source"], c["ward"], c["category"], c["title"], c["description"],
             c["priority"], c.get("status", "Open"), c.get("confidence"),
             int(c.get("is_duplicate", 0)), c.get("duplicate_of"),
             c["created_at"], datetime.now().isoformat(timespec="seconds")),
        )
        return cur.lastrowid


def get_complaint(cid: int):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM complaints WHERE id = ?", (cid,)).fetchone()
        return dict(row) if row else None


def get_complaints(category=None, priority=None, ward=None, status=None, q=None,
                   limit=300, offset=0):
    sql = "SELECT * FROM complaints WHERE 1=1"
    args = []
    if category:
        sql += " AND category = ?"
        args.append(category)
    if priority:
        sql += " AND priority = ?"
        args.append(priority)
    if ward:
        sql += " AND ward = ?"
        args.append(ward)
    if status:
        sql += " AND status = ?"
        args.append(status)
    if q:
        sql += " AND (title LIKE ? OR description LIKE ?)"
        args += [f"%{q}%", f"%{q}%"]
    sql += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
    args += [limit, offset]
    with get_conn() as conn:
        return [dict(r) for r in conn.execute(sql, args).fetchall()]


def complaint_count(category=None, priority=None, ward=None, status=None) -> int:
    return len(get_complaints(category=category, priority=priority, ward=ward,
                              status=status, limit=10_000_000))


def recent_complaints(limit=10):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM complaints ORDER BY created_at DESC, id DESC LIMIT ?",
            (limit,)).fetchall()
        return [dict(r) for r in rows]


def similar_complaints(ward: str, category: str, days: int = 7) -> int:
    """Count of recent complaints in the same ward + category (used for
    frequency-based priority boosting and duplicate trend detection)."""
    cutoff = (datetime.now() - timedelta(days=days)).isoformat(timespec="seconds")
    with get_conn() as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS n FROM complaints WHERE ward = ? AND category = ? AND created_at >= ?",
            (ward, category, cutoff)).fetchone()
        return int(row["n"])


def get_stats(days: int = 3650) -> dict:
    """Aggregated statistics: totals by priority / category / status and overall."""
    cutoff = (datetime.now() - timedelta(days=days)).isoformat(timespec="seconds")
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM complaints WHERE created_at >= ?", (cutoff,)).fetchall()

    total = len(rows)
    by_priority = Counter(r["priority"] for r in rows)
    by_category = Counter(r["category"] for r in rows)
    by_status = Counter(r["status"] for r in rows)
    return {
        "total": total,
        "by_priority": {p: by_priority.get(p, 0) for p in PRIORITIES},
        "by_category": {c: by_category.get(c, 0) for c in CATEGORIES},
        "by_status": dict(by_status),
        "duplicates": sum(1 for r in rows if r["is_duplicate"]),
    }


def daily_counts(days: int = 14) -> list:
    """[(date_str, count)] for the last `days` days, oldest first."""
    today = datetime.now().date()
    cutoff = (datetime.now() - timedelta(days=days)).isoformat(timespec="seconds")
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT created_at FROM complaints WHERE created_at >= ?", (cutoff,)).fetchall()
    counts = Counter(r["created_at"][:10] for r in rows)
    out = []
    for i in range(days - 1, -1, -1):
        d = today - timedelta(days=i)
        out.append((d.strftime("%b %d"), counts.get(d.isoformat(), 0)))
    return out


def ward_counts(days: int = 30) -> list:
    """[(ward, total, top_category)] for the dashboard hotspot view."""
    cutoff = (datetime.now() - timedelta(days=days)).isoformat(timespec="seconds")
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT ward, category FROM complaints WHERE created_at >= ?", (cutoff,)).fetchall()
    ward_total = Counter(r["ward"] for r in rows)
    ward_cat = Counter((r["ward"], r["category"]) for r in rows)
    out = []
    for ward, total in ward_total.most_common():
        top = max(CATEGORIES, key=lambda c: ward_cat.get((ward, c), 0))
        out.append({"ward": ward, "total": total, "top_category": top,
                    "share": total / max(1, len(rows)) * 100})
    return sorted(out, key=lambda w: w["total"], reverse=True)


def top_keywords(category=None, days: int = 7, n: int = 8) -> list:
    """Most frequent content words across complaints (optionally one category)."""
    from .preprocessing import normalize, tokenize, remove_stopwords
    cutoff = (datetime.now() - timedelta(days=days)).isoformat(timespec="seconds")
    if category:
        sql = "SELECT description FROM complaints WHERE category = ? AND created_at >= ?"
        args = (category, cutoff)
    else:
        sql = "SELECT description FROM complaints WHERE created_at >= ?"
        args = (cutoff,)
    with get_conn() as conn:
        rows = conn.execute(sql, args).fetchall()
    counter = Counter()
    for r in rows:
        counter.update(remove_stopwords(tokenize(normalize(r["description"]))))
    return [w for w, _ in counter.most_common(n)]


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------
def insert_report(period_start, period_end, title, summary, fmt="weekly") -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO reports (period_start, period_end, title, summary, format, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (period_start, period_end, title, summary, fmt,
             datetime.now().isoformat(timespec="seconds")))
        return cur.lastrowid


def get_reports(limit=50):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM reports ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        return [dict(r) for r in rows]


def get_report(rid: int):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM reports WHERE id = ?", (rid,)).fetchone()
        return dict(row) if row else None


def update_status(cid: int, status: str) -> None:
    with get_conn() as conn:
        conn.execute("UPDATE complaints SET status = ? WHERE id = ?", (status, cid))


def complaints_in_period(start: str, end: str) -> list:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM complaints WHERE created_at >= ? AND created_at <= ? "
            "ORDER BY created_at",
            (start, end)).fetchall()
        return [dict(r) for r in rows]
