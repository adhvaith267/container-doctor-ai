import os
from dotenv import load_dotenv

load_dotenv()

TARGET_CONTAINERS = os.getenv("TARGET_CONTAINERS", "").split(",")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "10"))
LOG_LINES = int(os.getenv("LOG_LINES", "50"))
AUTO_FIX = os.getenv("AUTO_FIX", "true").lower() == "true"
SLACK_WEBHOOK = os.getenv("SLACK_WEBHOOK_URL", "")
MAX_DIAGNOSES = int(os.getenv("MAX_DIAGNOSES_PER_HOUR", "20"))