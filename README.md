# ODSC 2026: Deploying a Secure Autonomous Agent

A hands-on workshop demonstrating how to build and deploy a secure autonomous agent that monitors teacher licensure and Praxis exam compliance requirements across US states and school districts.

## What This Does

The agent autonomously hunts for changes to educator certification requirements — state DOE pages, Praxis exam requirements, endorsement rules — and sends you a Telegram notification the moment something changes. Full traces captured in Opik for observability.

## Architecture

```
Scheduled trigger
    ↓
OpenClaw agent (GPT-4o)
    ├── brave-search skill       — find relevant compliance pages
    └── check-compliance-updates — fetch, hash, diff, store in SQLite
    ↓
Change detected → Telegram notification
    ↓
Opik trace (full LLM + tool span visibility)
```

## Prerequisites

- Docker
- OpenAI API key
- Brave Search API key
- (Optional) Opik API key for observability
- (Optional) Telegram bot for notifications

## Setup

1. Copy `example.env` to `.env` and fill in your keys
2. Start the OpenClaw gateway: `docker compose -f openclaw-agent/docker-compose.yml up -d`
3. Follow the workshop notebooks in order

## Workshop Notebooks

| Notebook | What it covers |
| --- | --- |
| `agent_setup.ipynb` | Spin up OpenClaw, connect Telegram, run first compliance check |
| `opik_observability.ipynb` | Install Opik plugin, trace every agent turn |
| `opik_evaluation.ipynb` | Batch evaluation of agent response quality |
