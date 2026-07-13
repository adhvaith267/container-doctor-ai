import os
from dotenv import load_dotenv

load_dotenv()

# -----------------------
# Container Monitoring
# -----------------------

TARGET_CONTAINERS = [
    c.strip()
    for c in os.getenv("TARGET_CONTAINERS", "").split(",")
    if c.strip()
]

CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "10"))
INCIDENT_SUPPRESSION_SECONDS = int(
    os.getenv("INCIDENT_SUPPRESSION_SECONDS", "300")
)
LOG_LINES = int(os.getenv("LOG_LINES", "50"))
AUTO_FIX = os.getenv("AUTO_FIX", "true").lower() == "true"
MAX_DIAGNOSES = int(os.getenv("MAX_DIAGNOSES_PER_HOUR", "20"))

# -----------------------
# Notifications
# -----------------------


def _env_flag(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


EMAIL_ENABLED = _env_flag("EMAIL_ENABLED")
SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
EMAIL_FROM = os.getenv("EMAIL_FROM", "")
EMAIL_TO = os.getenv("EMAIL_TO", "")

SLACK_ENABLED = _env_flag("SLACK_ENABLED")
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")

DISCORD_ENABLED = _env_flag("DISCORD_ENABLED")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")

NOTIFICATION_TIMEOUT_SECONDS = float(
    os.getenv("NOTIFICATION_TIMEOUT_SECONDS", "10")
)

# Backward-compatible name for the original Slack-only helper.
SLACK_WEBHOOK = SLACK_WEBHOOK_URL

# -----------------------
# AI Configuration
# -----------------------

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama").lower()

OLLAMA_BASE_URL = os.getenv(
    "OLLAMA_BASE_URL",
    "http://127.0.0.1:11434"
)

OLLAMA_MODEL = os.getenv(
    "OLLAMA_MODEL",
    "qwen2.5:7b"
)

OLLAMA_TIMEOUT_SECONDS = float(
    os.getenv("OLLAMA_TIMEOUT_SECONDS", "60")
)
