"""
Custom Claw — Teacher Licensure Compliance Monitor
~150 lines of Python. No framework, no magic.

What it does:
  1. Fetches each URL in the watch list
  2. Hashes the meaningful text content (strips HTML)
  3. Compares against the stored snapshot in SQLite
  4. Sends a Telegram alert when a change is detected
  5. Runs once per invocation (schedule via cron or the notebook)
"""

import hashlib
import html as html_lib
import os
import re
import sqlite3
import time
from datetime import datetime, timezone

import requests
from dotenv import load_dotenv

from compliance_urls import WATCH_LIST

load_dotenv()

DB_PATH    = os.getenv("DB_PATH", "/data/compliance.db")
BOT_TOKEN  = os.getenv("CUSTOM_CLAW_TELEGRAM_BOT_TOKEN", "")
CHAT_ID    = os.getenv("CUSTOM_CLAW_TELEGRAM_CHAT_ID", "")
USER_AGENT = "Mozilla/5.0 (compatible; compliance-monitor/1.0)"
FETCH_TIMEOUT = 20  # seconds


# ── Database ──────────────────────────────────────────────────────────────────

def init_db(db_path: str) -> sqlite3.Connection:
    db_dir = os.path.dirname(db_path)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS snapshots (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            state        TEXT NOT NULL,
            subject      TEXT,
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
            subject      TEXT,
            url          TEXT NOT NULL,
            old_hash     TEXT,
            new_hash     TEXT NOT NULL,
            excerpt      TEXT,
            detected_at  TEXT NOT NULL
        )
    """)
    conn.commit()
    return conn


def get_last_hash(conn: sqlite3.Connection, url: str, state: str, subject: str) -> str | None:
    row = conn.execute(
        "SELECT content_hash FROM snapshots WHERE url = ? AND state = ? AND subject = ? "
        "ORDER BY checked_at DESC LIMIT 1",
        (url, state, subject)
    ).fetchone()
    return row[0] if row else None


def save_snapshot(conn: sqlite3.Connection, state: str, subject: str, url: str,
                  content_hash: str, excerpt: str) -> None:
    conn.execute(
        "INSERT INTO snapshots (state, subject, url, content_hash, excerpt, checked_at) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (state, subject, url, content_hash, excerpt[:500], datetime.now(timezone.utc).isoformat())
    )
    conn.commit()


def save_change(conn: sqlite3.Connection, state: str, subject: str, url: str,
                old_hash: str | None, new_hash: str, excerpt: str) -> None:
    conn.execute(
        "INSERT INTO changes (state, subject, url, old_hash, new_hash, excerpt, detected_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (state, subject, url, old_hash, new_hash, excerpt[:500], datetime.now(timezone.utc).isoformat())
    )
    conn.commit()


# ── Fetching & Hashing ────────────────────────────────────────────────────────

def fetch_text(url: str) -> str | None:
    """Fetch a URL and return stripped plain text, or None on failure."""
    try:
        resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=FETCH_TIMEOUT)
        resp.raise_for_status()
        raw = resp.text
        # Remove script/style blocks before stripping tags to avoid hashing
        # dynamic JS payloads, nonces, or analytics that change on every load.
        raw = re.sub(r"<(script|style)[^>]*>.*?</(script|style)>", " ", raw, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<[^>]+>", " ", raw)
        text = html_lib.unescape(text)
        text = re.sub(r"\s+", " ", text).strip()
        return text
    except Exception as exc:
        print(f"  ⚠️  Fetch failed for {url}: {exc}")
        return None


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


# ── Telegram ──────────────────────────────────────────────────────────────────

def send_telegram(message: str) -> None:
    if not BOT_TOKEN or not CHAT_ID:
        print("  ℹ️  Telegram not configured — skipping notification")
        return
    try:
        resp = requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"},
            timeout=10,
        )
        resp.raise_for_status()
    except requests.HTTPError as exc:
        print(f"  ⚠️  Telegram send failed: HTTP {exc.response.status_code}")
    except Exception as exc:
        print(f"  ⚠️  Telegram send failed: {type(exc).__name__}")


# ── Main loop ─────────────────────────────────────────────────────────────────

def run_check(states: list[str] | None = None) -> list[dict]:
    """
    Check all URLs (or a filtered list of states).
    Returns list of detected changes.
    """
    conn = init_db(DB_PATH)
    changes_found = []

    watch = WATCH_LIST
    if states:
        watch = [(s, sub, u) for s, sub, u in WATCH_LIST
                 if any(f.lower() == s.lower() for f in states)]

    print(f"\n{'='*55}")
    print(f"  Compliance Monitor — {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"  Checking {len(watch)} URL(s)")
    print(f"{'='*55}\n")

    for state, subject, url in watch:
        print(f"Checking {state} ({subject})...")
        text = fetch_text(url)
        if text is None:
            continue

        new_hash = content_hash(text)
        excerpt  = text[:400]
        old_hash = get_last_hash(conn, url, state, subject)

        if old_hash is None:
            save_snapshot(conn, state, subject, url, new_hash, excerpt)
            print(f"  📌 Baseline captured")
        elif old_hash != new_hash:
            save_snapshot(conn, state, subject, url, new_hash, excerpt)
            save_change(conn, state, subject, url, old_hash, new_hash, excerpt)
            print(f"  🚨 CHANGE DETECTED")
            change = {"state": state, "subject": subject, "url": url, "excerpt": excerpt}
            changes_found.append(change)

            msg = (
                f"🚨 <b>Compliance Update Detected</b>\n\n"
                f"<b>State:</b> {html_lib.escape(state)}\n"
                f"<b>Area:</b> {html_lib.escape(subject)}\n"
                f"<b>URL:</b> {html_lib.escape(url)}\n\n"
                f"<i>{html_lib.escape(excerpt[:300])}...</i>"
            )
            send_telegram(msg)
        else:
            print(f"  ✅ No change")

        time.sleep(1)  # be polite to state DOE servers

    conn.close()

    print(f"\n{'='*55}")
    print(f"  Done. {len(changes_found)} change(s) detected.")
    print(f"{'='*55}\n")

    return changes_found


if __name__ == "__main__":
    import sys
    states = sys.argv[1:] or None
    run_check(states)
