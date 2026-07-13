# ContainerDoctor

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/Docker-SDK-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![Ollama](https://img.shields.io/badge/Ollama-Local%20LLM-000000)](https://ollama.com/)
[![SQLite](https://img.shields.io/badge/SQLite-Database-003B57?logo=sqlite&logoColor=white)](https://sqlite.org/)

## Overview

ContainerDoctor AI is an autonomous AI-powered Site Reliability
Engineering (SRE) agent that continuously monitors Docker containers,
detects failures from runtime logs, analyzes incidents using a local
Large Language Model (Ollama), decides recovery actions, executes
remediation, stores incident history, and visualizes the complete
operational workflow through a FastAPI dashboard.

Unlike traditional monitoring tools that only detect failures,
ContainerDoctor AI demonstrates an autonomous observe → reason → decide
→ act pipeline.

## Key Features

-   Continuous Docker container monitoring
-   AI-assisted root cause analysis using Ollama
-   Autonomous decision engine
-   Automatic container restart
-   Multi-channel notifications (Email, Slack, Discord, Console)
-   Duplicate incident suppression
-   SQLite incident persistence
-   Analytics dashboard
-   Timeline and AI reasoning visualization
-   Local-first deployment (no cloud AI dependency)

## Architecture

``` text
Docker Containers
        │
        ▼
 Observer
        │
        ▼
 Reasoner
        │
        ▼
 AI Service
        │
        ▼
 Ollama
        │
        ▼
 Decision
        │
        ▼
 Executor
        │
        ├────────► Notification Service
        ▼
 Memory
        │
        ▼
 SQLite
        │
        ▼
 Dashboard
```

## Project Structure

``` text
app/
├── agents/
├── ai/
├── api/
├── services/
├── static/
├── templates/
├── db/
├── config.py
└── main.py
```

## Technology Stack

  Layer               Technology
  ------------------- -------------------------------
  Backend             FastAPI
  Language            Python
  AI                  Ollama + Qwen2.5
  Container Runtime   Docker SDK
  Database            SQLite
  Frontend            HTML, CSS, JavaScript, Jinja2

## Installation

``` bash
git clone <repository-url>
cd container-doctor-ai
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Install Ollama

``` bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull qwen2.5:7b
```

## Example Configuration

``` env
TARGET_CONTAINERS=web,redis,broken-app
CHECK_INTERVAL=10
LOG_LINES=50

LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=qwen2.5:7b

EMAIL_ENABLED=false
SLACK_ENABLED=false
DISCORD_ENABLED=false
```

## Run

``` bash
uvicorn app.api.server:app --reload
```

Dashboard:

    http://127.0.0.1:8000

## Agent Workflow

1.  Observe Docker logs.
2.  Detect runtime failures.
3.  Generate an incident.
4.  Send incident to Ollama.
5.  Parse and validate AI output.
6.  Select a recovery action.
7.  Execute recovery.
8.  Send notifications.
9.  Persist the incident.
10. Update dashboard analytics.

## Dashboard

The dashboard provides:

-   System overview
-   AI engine status
-   Incident history
-   Recovery statistics
-   Timeline
-   Container analytics
-   AI reasoning
-   Execution results

## Repository Topics

    python
    fastapi
    docker
    docker-sdk
    ollama
    llm
    ai-agents
    site-reliability-engineering
    observability
    incident-response
    container-monitoring
    sqlite
    devops
    autonomous-agent

## Future Enhancements

-   Additional notification providers
-   Container health scoring
-   Kubernetes support
-   Scheduled reports
-   Advanced analytics

## License

This project is released under the MIT License.
