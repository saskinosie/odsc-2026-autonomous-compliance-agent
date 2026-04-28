import hashlib
import os
import sqlite3
from datetime import datetime, timezone

DB_PATH = os.getenv("DB_PATH", os.path.join(os.path.dirname(__file__), "..", "..", "compliance.db"))


def _init_db(path: str) -> sqlite3.Connection:
    db_dir = os.path.dirname(path)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS snapshots (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            state        TEXT NOT NULL,
            subject      TEXT NOT NULL,
            url          TEXT NOT NULL,
            content_hash TEXT NOT NULL,
            excerpt      TEXT,
            checked_at   TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS changes (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            state        TEXT NOT NULL,
            subject      TEXT NOT NULL,
            url          TEXT NOT NULL,
            old_hash     TEXT,
            new_hash     TEXT NOT NULL,
            excerpt      TEXT,
            detected_at  TEXT NOT NULL
        )
    """)
    conn.commit()
    return conn


def check_for_change(state: str, subject: str, url: str, content: str) -> dict:
    """Compare content against the stored snapshot. Returns a result dict with keys:
    - status: 'baseline_captured' | 'changed' | 'unchanged'
    - excerpt: first 400 chars of current content
    """
    now = datetime.now(timezone.utc).isoformat()
    new_hash = hashlib.sha256(content.encode()).hexdigest()
    excerpt = content[:400]

    conn = _init_db(DB_PATH)
    try:
        row = conn.execute(
            "SELECT content_hash FROM snapshots WHERE url=? AND state=? AND subject=? "
            "ORDER BY checked_at DESC LIMIT 1",
            (url, state, subject),
        ).fetchone()
        old_hash = row[0] if row else None

        conn.execute(
            "INSERT INTO snapshots (state, subject, url, content_hash, excerpt, checked_at) "
            "VALUES (?,?,?,?,?,?)",
            (state, subject, url, new_hash, excerpt[:500], now),
        )

        if old_hash is None:
            conn.commit()
            return {"status": "baseline_captured", "excerpt": excerpt}

        if old_hash != new_hash:
            conn.execute(
                "INSERT INTO changes (state, subject, url, old_hash, new_hash, excerpt, detected_at) "
                "VALUES (?,?,?,?,?,?,?)",
                (state, subject, url, old_hash, new_hash, excerpt[:500], now),
            )
            conn.commit()
            return {"status": "changed", "excerpt": excerpt}

        conn.commit()
        return {"status": "unchanged", "excerpt": excerpt}
    finally:
        conn.close()
