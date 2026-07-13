# ContainerDoctor AI

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/Docker-SDK-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![Ollama](https://img.shields.io/badge/Ollama-Local%20LLM-000000)](https://ollama.com/)
[![SQLite](https://img.shields.io/badge/SQLite-Database-003B57?logo=sqlite&logoColor=white)](https://sqlite.org/)

**ContainerDoctor AI** is an autonomous Site Reliability Engineering (SRE) agent for Docker. It watches container logs, uses a locally-hosted LLM (via [Ollama](https://ollama.com/)) to diagnose failures, decides on a recovery action, executes it, and records the entire incident lifecycle in a browser dashboard — all without sending your logs to the cloud.

Where a typical monitoring tool stops at "something broke," ContainerDoctor AI runs a full closed loop:

```
observe  →  reason  →  decide  →  act  →  remember
```

---

## Table of Contents

- [Why ContainerDoctor AI](#why-containerdoctor-ai)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Technology Stack](#technology-stack)
- [Getting Started](#getting-started)
- [Configuration](#configuration)
- [Running the Service](#running-the-service)
- [Dashboard & Web Routes](#dashboard--web-routes)
- [REST API](#rest-api)
- [Agent Workflow](#agent-workflow)
- [Safety & Recovery Limits](#safety--recovery-limits)
- [Roadmap](#roadmap)
- [License](#license)

---

## Why ContainerDoctor AI

Most container monitoring stacks tell you *that* a container is unhealthy. ContainerDoctor AI goes a step further: it reads the actual runtime logs, asks a local LLM to reason about the root cause, and — within configurable safety limits — takes corrective action automatically, notifying you along the way. Because the reasoning model runs locally through Ollama, no incident data ever leaves your infrastructure.

## Key Features

- **Continuous Docker monitoring** — polls configured containers on a fixed interval and pulls recent logs via the Docker SDK.
- **AI-assisted root cause analysis** — sends structured incident context to a local LLM and validates its structured JSON response before trusting it.
- **Autonomous decision engine** — turns a diagnosis into an approved action, capping repeated restarts to avoid restart loops.
- **Automatic remediation** — executes restarts (or alerts) and records the outcome of every action taken.
- **Multi-channel notifications** — Email, Slack, and Discord, each independently toggleable.
- **Duplicate incident suppression** — a configurable time window prevents the same failure from re-triggering the pipeline repeatedly.
- **Persistent incident history** — every cycle (logs, prompt, LLM response, decision, and result) is stored in SQLite.
- **Analytics dashboard** — restart success rate, most problematic containers, and full incident timelines, rendered server-side with Jinja2.
- **Local-first** — no cloud AI dependency; the only external services you opt into are your own notification webhooks.

## Architecture

```
 Docker Containers
        │  logs
        ▼
   Observer  ──────────────► detects errors, builds incident
        │
        ▼
   Reasoner  ──────────────► delegates to AI Service
        │
        ▼
   AI Service ─────────────► prompts, parses & validates
        │
        ▼
     Ollama  ──────────────► local LLM (default: qwen2.5:7b)
        │
        ▼
   Decision  ──────────────► approves / caps the recovery action
        │
        ▼
   Executor  ──────────────► restarts container or raises an alert
        │              │
        │              └──► Notification Service (Email / Slack / Discord)
        ▼
    Memory   ──────────────► suppression check + persistence
        │
        ▼
    SQLite
        │
        ▼
   Dashboard (FastAPI + Jinja2)
```

## Project Structure

```
app/
├── agents/            # Observe → Reason → Decide → Act → Remember pipeline
│   ├── observer.py     # Pulls logs, detects errors, builds an incident
│   ├── reasoner.py      # Delegates diagnosis to the AI service
│   ├── decision.py      # Approves actions, enforces restart limits
│   ├── executor.py      # Executes the approved action, fires notifications
│   └── memory.py        # Suppression checks + incident persistence
├── ai/                 # LLM integration
│   ├── ollama_client.py  # HTTP client for the local Ollama server
│   ├── prompts.py         # Diagnosis prompt construction
│   ├── parser.py          # Parses raw LLM output into JSON
│   ├── validator.py       # Validates/normalizes the diagnosis schema
│   └── ai_service.py      # Orchestrates prompt → call → parse → validate
├── api/
│   ├── server.py        # FastAPI app factory, lifespan-managed monitor loop
│   ├── routes.py         # JSON REST API (/health, /incidents, /analytics)
│   └── web_routes.py     # Server-rendered dashboard routes
├── services/
│   ├── docker_service.py       # Docker SDK integration (logs, restarts, status)
│   ├── log_service.py          # Error/failure detection in raw log text
│   ├── monitor_service.py      # Runs and loops the agent pipeline
│   ├── database_service.py     # SQLite schema, reads/writes for incidents
│   ├── analytics_service.py    # Aggregate incident statistics
│   └── notification_service.py # Email / Slack / Discord delivery
├── templates/           # Jinja2 templates for the dashboard
├── static/              # Dashboard CSS/JS
├── db/                  # SQLite database file
├── config.py            # Environment-driven configuration
└── main.py              # Single-cycle entry point for local debugging
```

## Technology Stack

| Layer             | Technology                     |
|-------------------|---------------------------------|
| Backend           | FastAPI                         |
| Language          | Python 3.11+                    |
| AI / LLM          | Ollama (default model: `qwen2.5:7b`) |
| Container Runtime | Docker SDK for Python            |
| Database          | SQLite (via SQLAlchemy)          |
| Frontend          | Jinja2, HTML, CSS, JavaScript     |
| Notifications     | SMTP, Slack webhooks, Discord webhooks |

## Getting Started

### Prerequisites

- Python 3.11+
- Docker Engine running locally, with the containers you want to monitor
- [Ollama](https://ollama.com/) installed, with a model pulled

### Installation

```bash
git clone <repository-url>
cd container-doctor-ai
python -m venv venv
source venv/bin/activate       # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Install and start Ollama

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull qwen2.5:7b
```

## Configuration

ContainerDoctor AI is configured entirely through environment variables (loaded from a `.env` file via `python-dotenv`). Create a `.env` file in the project root:

```env
# Container Monitoring
TARGET_CONTAINERS=web,redis,broken-app
CHECK_INTERVAL=10
LOG_LINES=50
INCIDENT_SUPPRESSION_SECONDS=300
AUTO_FIX=true
MAX_DIAGNOSES_PER_HOUR=20

# AI / Ollama
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=qwen2.5:7b
OLLAMA_TIMEOUT_SECONDS=60

# Notifications
EMAIL_ENABLED=false
SMTP_HOST=
SMTP_PORT=587
SMTP_USERNAME=
SMTP_PASSWORD=
EMAIL_FROM=
EMAIL_TO=

SLACK_ENABLED=false
SLACK_WEBHOOK_URL=

DISCORD_ENABLED=false
DISCORD_WEBHOOK_URL=

NOTIFICATION_TIMEOUT_SECONDS=10
```

| Variable | Description | Default |
|---|---|---|
| `TARGET_CONTAINERS` | Comma-separated list of container names to monitor | *(empty)* |
| `CHECK_INTERVAL` | Seconds between monitoring cycles | `10` |
| `LOG_LINES` | Number of trailing log lines fetched per container | `50` |
| `INCIDENT_SUPPRESSION_SECONDS` | Window during which a matching incident is suppressed as a duplicate | `300` |
| `AUTO_FIX` | Whether the executor is allowed to take automatic recovery action | `true` |
| `MAX_DIAGNOSES_PER_HOUR` | Upper bound on AI diagnoses per hour | `20` |
| `OLLAMA_BASE_URL` | Base URL of the local Ollama server | `http://127.0.0.1:11434` |
| `OLLAMA_MODEL` | Ollama model used for diagnosis | `qwen2.5:7b` |
| `EMAIL_ENABLED` / `SLACK_ENABLED` / `DISCORD_ENABLED` | Enable each notification channel independently | `false` |

## Running the Service

Start the FastAPI application (this also spins up the background monitoring loop via the app's lifespan handler):

```bash
uvicorn app.api.server:app --reload
```

Dashboard: [http://127.0.0.1:8000](http://127.0.0.1:8000)

For a single, one-off monitoring cycle (useful for local debugging without the web server):

```bash
python -m app.main
```

## Dashboard & Web Routes

| Route | Description |
|---|---|
| `GET /` | Main dashboard — system overview, AI engine status, live metrics |
| `GET /dashboard/metrics` | Partial/AJAX endpoint powering live dashboard updates |
| `GET /history` | Full incident history list |
| `GET /history/{incident_id}` | Incident detail view, including AI reasoning and per-stage timeline |
| `GET /analytics-dashboard` | Aggregate analytics — restart success rate, most problematic containers |

## REST API

| Method & Path | Description |
|---|---|
| `GET /health` | Docker connection status, monitored containers, total incident count |
| `GET /incidents` | Full list of stored incidents (logs, diagnosis, decision, result, timeline) |
| `GET /analytics` | Total incidents, restart success rate, most problematic container |

Interactive OpenAPI docs are available at `/docs` once the server is running.

## Notifications

Every completed recovery attempt — success, failure, or an escalated alert — is sent through `notification_service.send_notification()`. Delivery is **best-effort**: each channel is wrapped so a webhook timeout or SMTP error is logged and swallowed, never raised back into the recovery pipeline.

Three channels are supported, each toggled independently via config:

| Channel | Enable flag | Required settings | Delivery |
|---|---|---|---|
| Console | always on | — | Structured log line for every notification event |
| Email | `EMAIL_ENABLED` | `SMTP_HOST`, `EMAIL_FROM`, `EMAIL_TO` (comma-separated), optional `SMTP_USERNAME`/`SMTP_PASSWORD` | Multipart message (plain text + HTML) over SMTP; uses implicit TLS on port `465`, otherwise STARTTLS |
| Slack | `SLACK_ENABLED` | `SLACK_WEBHOOK_URL` | Formatted message via Slack incoming webhook |
| Discord | `DISCORD_ENABLED` | `DISCORD_WEBHOOK_URL` | Rich embed via Discord webhook |

**Console logging always runs**, regardless of which channels are enabled, so every notification event is visible in the application logs even with no webhooks configured.

### What's in a notification

Every message (regardless of channel) carries the same underlying payload:

- **Title** — e.g. "Container recovery succeeded", "Critical container recovery failure", "Container alert requires attention"
- **Container** name
- **Severity** — `critical` when the recovery failed, otherwise the AI's assessed severity
- **AI decision** — the final action taken (`restart`, `alert`, `ignore`) and the model's confidence, as a percentage
- **Root cause** — the AI's diagnosis, or `"No AI diagnosis recorded."` if diagnosis failed
- **Recovery result** — outcome message and container status after the action
- **Recent logs** — up to the last 4,000 characters (Email only)
- **Timestamp** — UTC, human-readable

Slack and Discord messages use a status indicator (✅ / ⚠️ / 🚨) driven by severity and success; Discord additionally colors the embed green on success and red on failure.

### Example

```env
SLACK_ENABLED=true
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/xxx/yyy/zzz

DISCORD_ENABLED=true
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/xxx/yyy

EMAIL_ENABLED=true
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=alerts@example.com
SMTP_PASSWORD=app-specific-password
EMAIL_FROM=alerts@example.com
EMAIL_TO=oncall@example.com,team@example.com
```

Any channel left disabled (or missing its required settings) is skipped silently with a warning in the logs — the notification call itself never fails the recovery cycle.

## Agent Workflow

1. **Observe** — pull recent logs for each monitored container.
2. **Detect** — scan logs for runtime failure patterns.
3. **Build incident** — package the container name, logs, and detected errors.
4. **Reason** — send the incident to the local LLM via Ollama.
5. **Parse & validate** — turn the raw LLM output into a validated diagnosis (root cause, severity, action, confidence).
6. **Decide** — approve a recovery action, enforcing a restart cap to prevent restart loops.
7. **Execute** — perform the restart (or raise an alert) and record the outcome.
8. **Notify** — send the result over any enabled channel (Email, Slack, Discord).
9. **Remember** — persist the full incident (including the AI's reasoning and the final result) to SQLite, subject to duplicate suppression.
10. **Visualize** — the dashboard reflects the updated incident history and analytics.

## Safety & Recovery Limits

- **Restart caps** — a container that has already been restarted 3 times is no longer auto-restarted; the decision engine instead escalates to an `alert` action.
- **Duplicate suppression** — repeated detections of the same underlying failure within `INCIDENT_SUPPRESSION_SECONDS` are treated as one incident, not re-triggered on every cycle.
- **Best-effort notifications** — notification failures never block or fail the recovery pipeline itself.
- **Graceful AI degradation** — if Ollama is unreachable or returns an invalid diagnosis, the agent falls back to a critical "AI unavailable" diagnosis and alerts rather than guessing.
