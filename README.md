# ODSC 2026: Deploying a Secure Autonomous Agent

A hands-on workshop demonstrating how to build and deploy a secure autonomous agent that monitors teacher licensure and Praxis exam compliance requirements across US states and school districts.

The agent autonomously hunts for changes to educator certification requirements — state DOE pages, Praxis exam requirements, endorsement rules — and sends a Telegram notification the moment something changes. Full traces captured in Opik for observability.

## Architecture

```
+----------------------+        +---------------------------+
| Custom Claw (Python) |        | OpenClaw (Framework)      |
| - ~150 lines         |  →     | - Production agent        |
| - Fetch + hash URLs  | evolve | - Scheduling built in     |
| - SQLite snapshots   |        | - Web dashboard           |
| - Telegram alerts    |        | - 50+ skills              |
+----------------------+        +-------------+-------------+
       Part 2-3                        Part 4-5
  "Build it yourself"             "Use a framework"
                  ↓                       ↓
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

### Required

| Service | What it's for | Sign up | Free tier? |
|---------|--------------|---------|------------|
| **Docker Desktop** | Runs both agents in isolated containers | [docker.com](https://www.docker.com/products/docker-desktop/) | Yes |
| **OpenAI** | Powers the OpenClaw agent reasoning | [platform.openai.com](https://platform.openai.com) | Credit required |
| **Brave Search** | Web search skill for finding compliance pages | [brave.com/search/api](https://brave.com/search/api/) | Yes (2000 queries/month) |

### Optional

| Service | What it's for | Sign up | Free tier? |
|---------|--------------|---------|------------|
| **Telegram** | Receive alerts on your phone | [telegram.org](https://telegram.org) | Yes |
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

# Optional — set up during the workshop
OPIK_API_KEY=
OPIK_WORKSPACE=
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
```

### 3. Set up the Python environment

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Make sure Docker is running

**On Docker Desktop (Mac/Windows):** Open Docker Desktop or confirm with `docker info`.

**On Linux without Docker Desktop:** Start the daemon manually:
```bash
sudo service docker start
```

### 5. Open the notebook

```bash
jupyter lab agent_setup.ipynb
```

Run through Parts 1–5 in order.

---

## Workshop Notebooks

| Notebook | What it covers |
| --- | --- |
| `agent_setup.ipynb` | Full workshop — Parts 1-5, Custom Claw through OpenClaw |
| `opik_observability.ipynb` | Install Opik plugin, trace every agent turn |
| `opik_evaluation.ipynb` | Batch LLM-as-a-judge evaluation of agent response quality |

---

## Two Agent Versions

### Custom Claw — Build It Yourself
~150 lines of Python in `custom-claw/src/monitor.py`. Fetches state DOE pages, hashes the content, diffs against SQLite snapshots, fires Telegram alerts. You can read every line and understand exactly what it does. No framework, no abstraction.

### OpenClaw — Use a Framework
The [OpenClaw](https://github.com/openclaw/openclaw) agent framework running in Docker. Same core logic, but with persistent memory, a web dashboard, built-in scheduling, multi-channel support (Telegram, Discord, Slack, WhatsApp), and Opik observability. Skills are defined as Markdown files — the `check-compliance-updates` skill is the framework version of `monitor.py`.

---

## Docker Commands

### Custom Claw

```bash
# Build
docker compose -f custom-claw/docker-compose.yml build

# Run a full compliance check
docker compose -f custom-claw/docker-compose.yml run --rm custom-claw

# Check a specific state
docker compose -f custom-claw/docker-compose.yml run --rm custom-claw python monitor.py Ohio

# Watch logs
docker compose -f custom-claw/docker-compose.yml logs -f
```

### OpenClaw

```bash
# Start the gateway
docker compose -f openclaw-agent/docker-compose.yml up -d openclaw-gateway

# Check gateway health
docker compose -f openclaw-agent/docker-compose.yml exec openclaw-gateway curl -sf http://localhost:18789/healthz

# Send the agent a message
docker compose -f openclaw-agent/docker-compose.yml exec openclaw-gateway \
  node /app/openclaw.mjs agent -m "Check for compliance updates in Texas"

# Open the web dashboard
docker compose -f openclaw-agent/docker-compose.yml exec openclaw-gateway \
  node /app/openclaw.mjs dashboard --no-open

# Stop everything
docker compose -f openclaw-agent/docker-compose.yml down
```

---

## Telegram Setup

Telegram alerts are optional but make for a compelling live demo.

### Step 1: Create a bot

1. Open Telegram and search for **@BotFather**
2. Send `/newbot`
3. Choose a display name (e.g. "Compliance Alert Bot")
4. Choose a username ending in `bot` (e.g. `my_compliance_bot`)
5. BotFather replies with your **HTTP API token** — copy it

### Step 2: Get your chat ID

1. Send your new bot any message (e.g. "hello")
2. Open this URL in your browser (replace `<TOKEN>` with your token):
   ```
   https://api.telegram.org/bot<TOKEN>/getUpdates
   ```
3. In the JSON, find `"chat":{"id":123456789}` — that number is your chat ID

### Step 3: Add to .env

```env
TELEGRAM_BOT_TOKEN=7123456789:AAF1234abcd...
TELEGRAM_CHAT_ID=123456789
```

---

## Project Structure

```
odsc-2026-autonomous-compliance-agent/
├── agent_setup.ipynb                   # Main workshop notebook (Parts 1-5)
├── opik_observability.ipynb            # Opik plugin setup and tracing
├── opik_evaluation.ipynb               # LLM-as-a-judge batch evaluation
├── requirements.txt                    # Python dependencies
├── example.env                         # API key template (safe to commit)
├── .env                                # Your actual keys (git-ignored)
├── AGENTS.md                           # Agent context and domain knowledge
│
├── custom-claw/                        # "Build it yourself" — Parts 2-3
│   ├── src/
│   │   ├── monitor.py                  # Core logic: fetch, hash, diff, alert
│   │   └── compliance_urls.py          # URLs to monitor
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── requirements.txt
│
├── openclaw-agent/                     # "Use a framework" — Parts 4-5
│   ├── skills/
│   │   ├── brave-search/               # Web search skill
│   │   └── check-compliance-updates/  # Compliance monitoring skill
│   ├── docker-compose.yml
│   └── config/                         # Gateway config (git-ignored)
│
└── data/                               # SQLite database (git-ignored)
    └── compliance.db                   # Snapshots and change history
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `docker: permission denied` | Prefix commands with `sudo`, or add your user to the docker group: `sudo usermod -aG docker $USER` |
| Custom Claw shows no changes | First run captures baselines — changes appear on subsequent runs when a page updates |
| `429` from Brave Search | Free tier is 1 req/sec. The agent has built-in delays but back off and retry if you hit the limit |
| OpenClaw gateway stuck at "pairing required" | Run `docker compose --profile cli run --rm openclaw-cli node /app/openclaw.mjs devices list` then `devices approve <id>` |
| Telegram message not received | Send your bot a message first (it can't initiate), then confirm your chat ID is correct |
| OpenClaw config reset after restart | Config lives in `openclaw-agent/config/` (git-ignored). Don't delete this directory between sessions |

---

## Resources

| Resource | Link |
|----------|------|
| OpenClaw | https://github.com/openclaw/openclaw |
| Opik | https://www.comet.com/opik |
| Brave Search API | https://brave.com/search/api/ |
| ETS Praxis State Requirements | https://www.ets.org/praxis/states.html |
| NASDTEC Interstate Agreements | https://www.nasdtec.net/page/NAEPCE |
