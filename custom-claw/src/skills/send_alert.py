import html as html_lib
import os

import requests

BOT_TOKEN = os.getenv("CUSTOM_CLAW_TELEGRAM_BOT_TOKEN", "")
CHAT_ID = os.getenv("CUSTOM_CLAW_TELEGRAM_CHAT_ID", "")


def send_alert(state: str, subject: str, url: str, summary: str) -> str:
    """Send a Telegram alert about a detected compliance change.
    Returns 'sent' on success or a description of why it was skipped/failed.
    """
    if not BOT_TOKEN or not CHAT_ID:
        return "skipped: CUSTOM_CLAW_TELEGRAM_BOT_TOKEN or CUSTOM_CLAW_TELEGRAM_CHAT_ID not set"

    msg = (
        f"🚨 <b>Compliance Update Detected</b>\n\n"
        f"<b>State:</b> {html_lib.escape(state)}\n"
        f"<b>Area:</b> {html_lib.escape(subject)}\n"
        f"<b>URL:</b> {html_lib.escape(url)}\n\n"
        f"{html_lib.escape(summary[:500])}"
    )

    try:
        resp = requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"},
            timeout=10,
        )
        resp.raise_for_status()
        return "sent"
    except requests.HTTPError as exc:
        return f"failed: HTTP {exc.response.status_code}"
    except Exception as exc:
        return f"failed: {type(exc).__name__}"
