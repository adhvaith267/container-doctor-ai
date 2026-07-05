import requests
from app.config import SLACK_WEBHOOK

def send_slack_alert(container_name, diagnosis, extra=""):
    if not SLACK_WEBHOOK:
        return

    payload = {
        "text": f"""
Container Alert: {container_name}
Severity: {diagnosis.get('severity')}
Root Cause: {diagnosis.get('root_cause')}
Fix: {diagnosis.get('suggested_fix')}
{extra}
"""
    }

    try:
        requests.post(SLACK_WEBHOOK, json=payload)
    except Exception as e:
        print(f"Slack alert failed: {e}")