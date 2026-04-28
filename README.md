# ODSC 2026: Deploying a Secure Autonomous Agent

A hands-on workshop demonstrating how to build and deploy a secure autonomous agent that monitors teacher licensure and Praxis exam compliance requirements across US states and school districts.

## Architecture

```
+---------------------------+        +---------------------------+
| Custom Claw (Notebook 1)  |        | OpenClaw (Notebook 2)     |
| - pydantic-ai agent       |  →     | - Production framework    |
| - Runs in Jupyter         | evolve | - Runs in Docker          |
| - Fetch + hash URLs       |        | - Scheduling built in     |
| - SQLite snapshots        |        | - Web dashboard           |
| - Brave Search discovery  |        | - Telegram notifications  |
+---------------------------+        +---------------------------+
   "Build it yourself"                  "Use a framework"
                  ↓                            ↓
          +---------------------------------------+
          |           SQLite Database             |
          |  - Compliance URL snapshots           |
          |  - Change history with timestamps     |
          +---------------------------------------+
                           ↓
                  Change detected
                           ↓
             Telegram notification → Opik trace
```

---

## Prerequisites

### Required for both notebooks

| Service | What it's for | Sign up | Free tier? |
|---------|--------------|---------|------------|
| **OpenAI** | Powers agent reasoning | [platform.openai.com](https://platform.openai.com) | Credit required |
| **Brave Search** | Web search skill for finding compliance pages | [brave.com/search/api](https://brave.com/search/api/) | Yes (2000 queries/month) |

### Required for Notebook 2 only

| Service | What it's for | Sign up | Free tier? |
|---------|--------------|---------|------------|
| **Docker Desktop** | Runs the OpenClaw agent | [docker.com](https://www.docker.com/products/docker-desktop/) | Yes |

### Optional

| Service | What it's for | Sign up | Free tier? |
|---------|--------------|---------|------------|
| **Telegram** | Receive alerts and chat with your agent | [telegram.org](https://telegram.org) | Yes |
| **Opik** | Full agent observability and tracing | [comet.com/opik](https://www.comet.com/opik) | Yes |

---

## Quick Start

### 1. Clone the repo

```bash
git clone https://github.com/saskinosie/odsc-2026-autonomous-compliance-agent.git
cd odsc-2026-autonomous-compliance-agent
```

### 2. Set up API keys

```bash
cp example.env .env
```

Open `.env` and fill in your keys:

```env
OPENAI_API_KEY=your-openai-api-key
BRAVE_API_KEY=your-brave-api-key

# Optional — OpenClaw Telegram (Notebook 2)
OPENCLAW_TELEGRAM_BOT_TOKEN=

# Optional — Opik observability (Notebook 2)
OPIK_API_KEY=
OPIK_WORKSPACE=
```

### 3. Set up the Python environment

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Open the notebooks

```bash
jupyter lab
```

Work through `1_custom_claw.ipynb` first, then `2_openclaw.ipynb`.

---

## Workshop Notebooks

| Notebook | What it covers |
| --- | --- |
| `1_custom_claw.ipynb` | Build Custom Claw with pydantic-ai — fetch pages, detect changes, add Brave Search |
| `2_openclaw.ipynb` | OpenClaw framework — AGENTS.md, Telegram pairing, Opik observability |

---

## Two Agent Versions

### Custom Claw — Build It Yourself

A pydantic-ai agent in `custom-claw/src/agent.py`. Skills are plain Python functions decorated with `agent.tool_plain()`:

- `fetch_compliance_page` — SSRF-safe page fetching with IP pinning
- `check_for_change` — SHA-256 content hashing against SQLite snapshots
- `discover_urls` — Brave Search to find compliance pages for any state

You can read every line and understand exactly what it does. No scheduling, no persistence, no multi-channel support — run it from the notebook.

### OpenClaw — Use a Framework

The [OpenClaw](https://github.com/openclaw/openclaw) agent framework running in Docker. Same core compliance logic, but with persistent memory, a web dashboard, Telegram support, and Opik observability built in. Skills are defined as Markdown + shell scripts — no Python required.

---

## OpenClaw CLI Reference

```bash
# Start the gateway
docker compose -f openclaw-agent/docker-compose.yml up -d openclaw-gateway

# Run a compliance check
docker compose -f openclaw-agent/docker-compose.yml exec openclaw-gateway \
  node /app/openclaw.mjs agent --agent main -m "Check for compliance updates in Texas"

# Check channel status
docker compose -f openclaw-agent/docker-compose.yml exec openclaw-gateway \
  node /app/openclaw.mjs channels status

# Approve a Telegram pairing request
docker compose -f openclaw-agent/docker-compose.yml exec openclaw-gateway \
  node /app/openclaw.mjs pairing approve telegram <CODE>

# Check Opik plugin status
docker compose -f openclaw-agent/docker-compose.yml exec openclaw-gateway \
  node /app/openclaw.mjs opik status

# Stop everything
docker compose -f openclaw-agent/docker-compose.yml down
```

---

## Telegram Setup (Notebook 2)

1. Open Telegram and search for **@BotFather** → send `/newbot` → follow the prompts → copy the token
2. Add to `.env`:
   ```env
   OPENCLAW_TELEGRAM_BOT_TOKEN=your-token
   ```
3. Run the Telegram cells in Notebook 2 — the first cell registers your bot, the second approves the pairing code your bot sends back

---

## Project Structure

```
odsc-2026-autonomous-compliance-agent/
├── 1_custom_claw.ipynb             # Notebook 1 — pydantic-ai agent
├── 2_openclaw.ipynb                # Notebook 2 — OpenClaw framework
├── AGENTS.md                       # Agent domain knowledge for OpenClaw
├── requirements.txt                # Python dependencies
├── example.env                     # API key template (safe to commit)
├── .env                            # Your actual keys (git-ignored)
│
├── custom-claw/                    # Custom Claw source
│   └── src/
│       ├── agent.py                # pydantic-ai agent + skill registration
│       ├── compliance_urls.py      # URLs to monitor
│       └── skills/
│           ├── fetch_page.py       # SSRF-safe page fetcher
│           ├── check_change.py     # SQLite snapshot diff
│           └── discover_urls.py    # Brave Search URL discovery
│
├── openclaw-agent/                 # OpenClaw framework
│   ├── skills/
│   │   ├── brave-search/           # Web search skill (SKILL.md + script)
│   │   └── check-compliance-updates/ # Compliance monitoring skill
│   ├── docker-compose.yml
│   └── config/                     # Gateway config + Opik plugin (git-ignored)
│
└── data/                           # SQLite database (git-ignored)
    └── compliance.db
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `docker: permission denied` | Add your user to the docker group: `sudo usermod -aG docker $USER` |
| Custom Claw shows no changes | First run captures baselines — changes appear on subsequent runs |
| `429` from Brave Search | Rate limit hit — wait a moment and retry |
| OpenClaw not responding on Telegram | Run `channels status` to verify the bot is polling; re-run the `channels add` cell if needed |
| Telegram pairing code not appearing | Make sure you sent your bot a message first — it replies with the code |
| Opik traces not appearing | Run `opik status` and check the project name is `compliance-agent` in workspace `your-username` |

---

## Resources

| Resource | Link |
|----------|------|
| OpenClaw | https://github.com/openclaw/openclaw |
| opik-openclaw plugin | https://github.com/comet-ml/opik-openclaw |
| Opik | https://www.comet.com/opik |
| Brave Search API | https://brave.com/search/api/ |
| ETS Praxis State Requirements | https://www.ets.org/praxis/states.html |
| NASDTEC Interstate Agreements | https://www.nasdtec.net/page/NAEPCE |
