---
name: brave-search
description: "Search the live web using Brave Search API for current events, news, stock prices, company info, and real-time information. Use when: user asks about current events, stock prices, market data, or anything needing up-to-date information. NOT for: SEC filing queries (use query-sec-filings instead)."
metadata: { "openclaw": { "emoji": "🔍", "requires": { "bins": ["curl", "python3"], "env": ["BRAVE_API_KEY"] } } }
---

# Brave Web Search

Search the live web using the Brave Search API.

## When to Use

✅ **USE this skill when:**

- "What's Tesla's stock price right now?"
- "Latest news about SEC crypto regulation"
- "Compare NVDA and AMD market caps"
- "What happened with [company] today?"
- Any question requiring real-time or current information

## When NOT to Use

❌ **DON'T use this skill when:**

- User asks about SEC filings in our database → use `query-sec-filings`
- User asks about documents we've already scraped → use `query-sec-filings`
- General knowledge questions the LLM can answer directly

## Commands

Run the search script with the user's query. The script handles authentication and response formatting automatically:

```bash
bash /app/skills/brave-search/search.sh "Tesla stock price today"
```

Always use this script — do NOT attempt to run curl with API keys directly.

## Notes

- Free tier: 1 request/sec, 2000/month
- Always cite the source URL when presenting results
- Summarize the top results rather than dumping everything
