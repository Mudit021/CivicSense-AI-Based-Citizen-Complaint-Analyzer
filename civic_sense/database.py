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
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    source           TEXT    NOT NULL DEFAULT 'Student Portal',
    ward             TEXT    NOT NULL,
    floor            TEXT    DEFAULT '',
    room_number      TEXT    DEFAULT '',
    sub_location     TEXT    DEFAULT '',
    category         TEXT    NOT NULL,
    title            TEXT    NOT NULL,
    description      TEXT    NOT NULL,
    priority         TEXT    NOT NULL DEFAULT 'Medium',
    status           TEXT    NOT NULL DEFAULT 'Open',
    confidence       REAL,
    is_duplicate     INTEGER NOT NULL DEFAULT 0,
    duplicate_of     INTEGER,
    is_suspicious    INTEGER NOT NULL DEFAULT 0,
    suspicion_score  REAL    DEFAULT 0.0,
    suspicion_reason TEXT    DEFAULT '',
    lat              REAL,
    lon              REAL,
    image_url        TEXT    DEFAULT '',
    image_analysis   TEXT    DEFAULT '',
    geo_source       TEXT    DEFAULT 'manual',
    created_at       TEXT    NOT NULL,
    processed_at     TEXT
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

CREATE INDEX IF NOT EXISTS idx_complaints_ward        ON complaints(ward);
CREATE INDEX IF NOT EXISTS idx_complaints_category    ON complaints(category);
CREATE INDEX IF NOT EXISTS idx_complaints_created     ON complaints(created_at);
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

        # Seamless schema migration for existing databases
        existing_cols = {row["name"] for row in conn.execute("PRAGMA table_info(complaints)").fetchall()}
        new_cols = [
            ("is_suspicious", "INTEGER NOT NULL DEFAULT 0"),
            ("suspicion_score", "REAL DEFAULT 0.0"),
            ("suspicion_reason", "TEXT DEFAULT ''"),
            ("lat", "REAL"),
            ("lon", "REAL"),
            ("floor", "TEXT DEFAULT ''"),
            ("room_number", "TEXT DEFAULT ''"),
            ("sub_location", "TEXT DEFAULT ''"),
            ("image_url", "TEXT DEFAULT ''"),
            ("image_analysis", "TEXT DEFAULT ''"),
            ("geo_source", "TEXT DEFAULT 'manual'"),
        ]
        for col, col_type in new_cols:
            if col not in existing_cols:
                conn.execute(f"ALTER TABLE complaints ADD COLUMN {col} {col_type}")

        conn.execute("CREATE INDEX IF NOT EXISTS idx_complaints_suspicious ON complaints(is_suspicious);")

        # Backfill coordinates and fraud evaluation for existing complaints if missing
        missing_geo = conn.execute("SELECT id, ward, description FROM complaints WHERE lat IS NULL").fetchall()
        if missing_geo:
            from .hotspot_analyzer import assign_coordinates
            from .fraud_detector import check_complaint
            for row in missing_geo:
                lat, lon = assign_coordinates(row["ward"], row["description"])
                is_susp, susp_score, susp_reason = check_complaint(row["description"])
                conn.execute(
                    "UPDATE complaints SET lat = ?, lon = ?, is_suspicious = ?, suspicion_score = ?, suspicion_reason = ? WHERE id = ?",
                    (lat, lon, int(is_susp), susp_score, susp_reason, row["id"])
                )


# ---------------------------------------------------------------------------
# Complaints
# ---------------------------------------------------------------------------
def insert_complaint(c: dict) -> int:
    from .config import LEGACY_BLOCK_ALIASES
    canonical_ward = LEGACY_BLOCK_ALIASES.get(c.get("ward", ""), c.get("ward", ""))
    with get_conn() as conn:
        cur = conn.execute(
            """INSERT INTO complaints
                 (source, ward, floor, room_number, sub_location, category, title, description, priority, status,
                  confidence, is_duplicate, duplicate_of, is_suspicious,
                  suspicion_score, suspicion_reason, lat, lon, image_url, image_analysis, geo_source,
                  created_at, processed_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (c["source"], canonical_ward, c.get("floor", ""), c.get("room_number", ""), c.get("sub_location", ""),
             c["category"], c["title"], c["description"],
             c["priority"], c.get("status", "Open"), c.get("confidence"),
             int(c.get("is_duplicate", 0)), c.get("duplicate_of"),
             int(c.get("is_suspicious", 0)), float(c.get("suspicion_score", 0.0)),
             c.get("suspicion_reason", ""), c.get("lat"), c.get("lon"),
             c.get("image_url", ""), c.get("image_analysis", ""), c.get("geo_source", "manual"),
             c["created_at"], datetime.now().isoformat(timespec="seconds")),
        )
        return cur.lastrowid


def get_complaint(cid: int):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM complaints WHERE id = ?", (cid,)).fetchone()
        return dict(row) if row else None


def get_complaints(category=None, priority=None, ward=None, status=None, q=None,
                   is_suspicious=None, floor=None, limit=300, offset=0):
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
    if floor:
        sql += " AND floor = ?"
        args.append(floor)
    if status:
        sql += " AND status = ?"
        args.append(status)
    if is_suspicious is not None and is_suspicious != "":
        sql += " AND is_suspicious = ?"
        args.append(int(is_suspicious))
    if q:
        sql += " AND (title LIKE ? OR description LIKE ? OR room_number LIKE ? OR sub_location LIKE ?)"
        args += [f"%{q}%", f"%{q}%", f"%{q}%", f"%{q}%"]
    sql += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
    args += [limit, offset]
    with get_conn() as conn:
        return [dict(r) for r in conn.execute(sql, args).fetchall()]


def complaint_count(category=None, priority=None, ward=None, status=None, is_suspicious=None, floor=None) -> int:
    return len(get_complaints(category=category, priority=priority, ward=ward,
                              status=status, is_suspicious=is_suspicious, floor=floor, limit=10_000_000))


def recent_complaints(limit=10):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM complaints ORDER BY created_at DESC, id DESC LIMIT ?",
            (limit,)).fetchall()
        return [dict(r) for r in rows]


def get_map_incidents(limit=250):
    """Retrieve recent complaints with valid coordinates for Leaflet map display."""
    with get_conn() as conn:
        rows = conn.execute(
            """SELECT id, title, description, ward, floor, room_number, sub_location, category, priority, status,
                      confidence, is_duplicate, duplicate_of, is_suspicious,
                      suspicion_score, lat, lon, image_url, image_analysis, geo_source, created_at
               FROM complaints WHERE lat IS NOT NULL
               ORDER BY created_at DESC LIMIT ?""",
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
        "suspicious": sum(1 for r in rows if r["is_suspicious"]),
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
    from .config import LEGACY_BLOCK_ALIASES
    cutoff = (datetime.now() - timedelta(days=days)).isoformat(timespec="seconds")
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT ward, category FROM complaints WHERE created_at >= ?", (cutoff,)).fetchall()
    ward_total = Counter(LEGACY_BLOCK_ALIASES.get(r["ward"], r["ward"]) for r in rows)
    ward_cat = Counter((LEGACY_BLOCK_ALIASES.get(r["ward"], r["ward"]), r["category"]) for r in rows)
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
