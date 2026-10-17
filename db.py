"""SQLite helpers: users, articles, events, editions."""
import json
import threading
import sqlite3
_write_lock = threading.Lock()
from contextlib import contextmanager
from datetime import timedelta

from core.config import DB_PATH, utcnow

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    reading_time INTEGER DEFAULT 10,
    style TEXT DEFAULT 'balanced',
    profile_json TEXT DEFAULT '{}',
    dark_mode INTEGER DEFAULT 0,
    last_preview_date TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    source TEXT,
    published TEXT,
    snippet TEXT,
    image TEXT,
    hint_topic TEXT,
    topics_json TEXT DEFAULT '[]',
    summary TEXT,
    importance REAL DEFAULT 0.25,
    reading_min INTEGER DEFAULT 2,
    enriched INTEGER DEFAULT 0,
    fetched_at TEXT
);
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    article_id INTEGER,
    action TEXT NOT NULL,
    ts TEXT
);
CREATE TABLE IF NOT EXISTS editions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    date TEXT NOT NULL,
    edition_no INTEGER,
    json_path TEXT,
    pdf_path TEXT,
    UNIQUE(user_id, date)
);
CREATE TABLE IF NOT EXISTS shown (
    user_id INTEGER NOT NULL,
    article_id INTEGER NOT NULL,
    date TEXT NOT NULL,
    PRIMARY KEY (user_id, article_id, date)
);
"""


def get_conn():
    # Increase timeout and allow usage across threads.
    # `check_same_thread=False` permits sharing connection objects between threads if needed,
    # but each call still creates its own connection, reducing contention.
    conn = sqlite3.connect(DB_PATH, timeout=30, check_same_thread=False)
    # Enable Write-Ahead Logging for better concurrent access.
    conn.execute("PRAGMA journal_mode=WAL")
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def _conn():
    conn = get_conn()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()



def init_db():
    with _conn() as c:
        c.executescript(SCHEMA)

        # Check which columns already exist in the users table.
        columns = {
            row["name"]
            for row in c.execute("PRAGMA table_info(users)").fetchall()
        }

        # Add missing columns to existing databases.
        if "dark_mode" not in columns:
            c.execute(
                "ALTER TABLE users ADD COLUMN dark_mode INTEGER DEFAULT 0"
            )

        if "last_preview_date" not in columns:
            c.execute(
                "ALTER TABLE users ADD COLUMN last_preview_date TEXT"
            )



def _iso(dt):
    return dt.isoformat(timespec="seconds")


# ---------------- users ----------------
def list_users():
    with _conn() as c:
        return [dict(r) for r in c.execute("SELECT * FROM users ORDER BY name")]


def get_user(user_id):
    with _conn() as c:
        row = c.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if not row:
        return None
    user = dict(row)
    user["profile"] = json.loads(user["profile_json"] or "{}")
    return user


def create_user(name, reading_time=10, style="balanced", profile=None):
    with _conn() as c:
        cur = c.execute(
            "INSERT INTO users (name, reading_time, style, profile_json) VALUES (?, ?, ?, ?)",
            (name, reading_time, style, json.dumps(profile or {})),
        )
        return cur.lastrowid


def update_profile(user_id, profile):
    with _conn() as c:
        c.execute("UPDATE users SET profile_json = ? WHERE id = ?",
                  (json.dumps(profile), user_id))



def set_user_pref(user_id: int, dark_mode: bool, preview_date: str | None = None):
    """Store UI preferences for a user."""
    with _conn() as c:
        c.execute(
            "UPDATE users SET dark_mode = ?, last_preview_date = ? WHERE id = ?",
            (int(dark_mode), preview_date, user_id),
        )

def update_user(user_id, name=None, reading_time=None, style=None):
    """Update editable fields for a user."""
    fields, args = [], []
    if name is not None:
        fields.append("name=?"); args.append(name)
    if reading_time is not None:
        fields.append("reading_time=?"); args.append(reading_time)
    if style is not None:
        fields.append("style=?"); args.append(style)
    if not fields:
        return
    args.append(user_id)
    with _conn() as c:
        c.execute(f"UPDATE users SET {', '.join(fields)} WHERE id=?", args)



def event_counts(user_id):
    with _conn() as c:
        rows = c.execute(
            "SELECT action, COUNT(*) AS n FROM events WHERE user_id=? GROUP BY action",
            (user_id,),
        )
        return {r["action"]: r["n"] for r in rows}


# ---------------- articles ----------------
def _article(row):
    a = dict(row)
    a["topics"] = json.loads(a.pop("topics_json") or "[]")
    return a


def upsert_article(a):
    """Insert a new article; return True if it was new."""
    # Serialize writes to avoid SQLite lock errors in multithreaded fetches.
    with _write_lock:
        with _conn() as c:
            cur = c.execute(
                """INSERT OR IGNORE INTO articles
                   (url, title, source, published, snippet, image, hint_topic, fetched_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (a["url"], a["title"], a.get("source"), a["published"], a.get("snippet", ""),
                 a.get("image"), a.get("hint_topic"), _iso(utcnow())),
            )
            return cur.rowcount > 0


def count_articles():
    with _conn() as c:
        return c.execute("SELECT COUNT(*) FROM articles").fetchone()[0]


def get_unenriched(limit=500):
    with _conn() as c:
        rows = c.execute("SELECT * FROM articles WHERE enriched = 0 LIMIT ?", (limit,))
        return [_article(r) for r in rows]


def save_enrichment(article_id, topics, summary, reading_min):
    with _conn() as c:
        c.execute(
            "UPDATE articles SET topics_json=?, summary=?, reading_min=?, enriched=1 WHERE id=?",
            (json.dumps(topics), summary, reading_min, article_id),
        )


def set_importance(article_id, importance):
    with _conn() as c:
        c.execute("UPDATE articles SET importance=? WHERE id=?", (importance, article_id))


def recent_articles(max_age_hours=72):
    cutoff = _iso(utcnow() - timedelta(hours=max_age_hours))
    with _conn() as c:
        rows = c.execute(
            "SELECT * FROM articles WHERE enriched = 1 AND published >= ?", (cutoff,))
        return [_article(r) for r in rows]


def get_articles_by_ids(ids):
    ids = list(ids)
    if not ids:
        return {}
    marks = ",".join("?" * len(ids))
    with _conn() as c:
        rows = c.execute(f"SELECT * FROM articles WHERE id IN ({marks})", ids)
        return {r["id"]: _article(r) for r in rows}


# ---------------- events ----------------
def log_event(user_id, article_id, action):
    with _conn() as c:
        c.execute("INSERT INTO events (user_id, article_id, action, ts) VALUES (?, ?, ?, ?)",
                  (user_id, article_id, action, _iso(utcnow())))


def events_after(user_id, last_id=0):
    with _conn() as c:
        rows = c.execute(
            "SELECT * FROM events WHERE user_id = ? AND id > ? ORDER BY id", (user_id, last_id))
        return [dict(r) for r in rows]


def user_action_ids(user_id, actions):
    marks = ",".join("?" * len(actions))
    with _conn() as c:
        rows = c.execute(
            f"SELECT DISTINCT article_id FROM events WHERE user_id = ? "
            f"AND article_id IS NOT NULL AND action IN ({marks})", (user_id, *actions))
        return {r[0] for r in rows}


# ---------------- editions ----------------
def save_edition(user_id, date, edition_no, json_path):
    with _conn() as c:
        c.execute(
            """INSERT INTO editions (user_id, date, edition_no, json_path) VALUES (?, ?, ?, ?)
               ON CONFLICT(user_id, date) DO UPDATE SET json_path=excluded.json_path, pdf_path=NULL""",
            (user_id, date, edition_no, str(json_path)),
        )


def get_edition_row(user_id, date):
    with _conn() as c:
        row = c.execute("SELECT * FROM editions WHERE user_id=? AND date=?",
                        (user_id, date)).fetchone()
    return dict(row) if row else None


def list_editions(user_id):
    with _conn() as c:
        rows = c.execute("SELECT * FROM editions WHERE user_id=? ORDER BY date DESC", (user_id,))
        return [dict(r) for r in rows]


def count_editions(user_id):
    with _conn() as c:
        return c.execute("SELECT COUNT(*) FROM editions WHERE user_id=?", (user_id,)).fetchone()[0]


def set_pdf_path(user_id, date, path):
    with _conn() as c:
        c.execute("UPDATE editions SET pdf_path=? WHERE user_id=? AND date=?",
                  (str(path), user_id, date))


def record_shown(user_id, article_ids, date):
    with _conn() as c:
        c.execute("DELETE FROM shown WHERE user_id=? AND date=?", (user_id, date))
        c.executemany("INSERT OR IGNORE INTO shown (user_id, article_id, date) VALUES (?, ?, ?)",
                      [(user_id, a, date) for a in article_ids])


def seen_ids(user_id, before_date):
    """Articles already printed in an earlier edition (so we don't repeat them)."""
    with _conn() as c:
        rows = c.execute("SELECT article_id FROM shown WHERE user_id=? AND date < ?",
                         (user_id, before_date))
        return {r[0] for r in rows}