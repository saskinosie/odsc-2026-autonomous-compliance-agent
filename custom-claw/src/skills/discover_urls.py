import os

import requests

BRAVE_API_KEY = os.getenv("BRAVE_API_KEY", "")


def discover_urls(state: str, max_results: int = 3) -> list[str]:
    """Search Brave for official teacher licensure compliance pages for a state.
    Returns a list of URLs, or an empty list if Brave API is not configured.
    """
    if not BRAVE_API_KEY:
        return []

    try:
        resp = requests.get(
            "https://api.search.brave.com/res/v1/web/search",
            headers={"Accept": "application/json", "X-Subscription-Token": BRAVE_API_KEY},
            params={"q": f"{state} teacher licensure certification requirements site:.gov", "count": max_results},
            timeout=10,
        )
        resp.raise_for_status()
        results = resp.json().get("web", {}).get("results", [])
        return [r["url"] for r in results]
    except Exception:
        return []
