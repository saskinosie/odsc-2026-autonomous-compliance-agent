---
name: check-compliance-updates
description: "Check for teacher licensure and Praxis exam requirement updates for a given US state, county, or school district. Use when: asked about licensure changes, Praxis requirements, certification updates, endorsement changes, or compliance monitoring for educator preparation programs. NOT for: real-time news unrelated to educator certification."
metadata: { "openclaw": { "emoji": "🏫", "requires": { "bins": ["curl", "python3", "sqlite3"], "env": [] } } }
---

# Teacher Licensure Compliance Checker

Checks for updates to teacher licensure requirements and stores change history in a local SQLite database.

## When to Use

✅ **USE this skill when:**

- "Check for licensure updates in Ohio"
- "Have Praxis requirements changed for Math 7-12 in Texas?"
- "What certification changes happened this week?"
- "Are there any new endorsement requirements in California?"
- "Show me the compliance change log"
- Any question about educator certification, Praxis exams, or licensure requirements

## When NOT to Use

❌ **DON'T use this skill when:**

- General education news not related to licensure → use `brave-search`
- Federal education policy (not state/district specific) → use `brave-search`

## Commands

**Check a specific state for updates:**
```bash
bash /app/skills/check-compliance-updates/check.sh "Ohio" "Mathematics 7-12"
```

**Check all monitored states:**
```bash
bash /app/skills/check-compliance-updates/check.sh "all"
```

**View recent changes in the database:**
```bash
bash /app/skills/check-compliance-updates/check.sh "log"
```

## Notes

- All findings are stored in `/home/user/data/compliance.db` with timestamps
- A change is flagged when a page's content hash differs from the stored snapshot
- Always report the state, subject area, and URL of any detected change
- When changes are found, summarize what appears different and send a notification
