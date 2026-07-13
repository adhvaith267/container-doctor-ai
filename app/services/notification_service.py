"""Best-effort delivery of autonomous recovery notifications."""

from __future__ import annotations

import html
import logging
import smtplib
from datetime import datetime, timezone
from email.message import EmailMessage
from typing import Any

import requests

from app.config import (
    DISCORD_ENABLED,
    DISCORD_WEBHOOK_URL,
    EMAIL_ENABLED,
    EMAIL_FROM,
    EMAIL_TO,
    NOTIFICATION_TIMEOUT_SECONDS,
    SLACK_ENABLED,
    SLACK_WEBHOOK_URL,
    SMTP_HOST,
    SMTP_PASSWORD,
    SMTP_PORT,
    SMTP_USERNAME,
)


logger = logging.getLogger(__name__)


def send_notification(
    title: str,
    container: str,
    severity: str,
    action: str,
    root_cause: str,
    confidence: float | int | None,
    logs: str,
    recovery_result: dict[str, Any],
) -> None:
    """Notify enabled channels without allowing delivery failures to stop recovery."""
    payload = _build_payload(
        title=title,
        container=container,
        severity=severity,
        action=action,
        root_cause=root_cause,
        confidence=confidence,
        logs=logs,
        recovery_result=recovery_result,
    )

    _log_to_console(payload)

    if EMAIL_ENABLED:
        _send_email(payload)
    if SLACK_ENABLED:
        _send_slack(payload)
    if DISCORD_ENABLED:
        _send_discord(payload)


def _build_payload(
    *,
    title: str,
    container: str,
    severity: str,
    action: str,
    root_cause: str,
    confidence: float | int | None,
    logs: str,
    recovery_result: dict[str, Any],
) -> dict[str, Any]:
    try:
        confidence_percent = round(float(confidence or 0) * 100)
    except (TypeError, ValueError):
        confidence_percent = 0

    return {
        "title": title,
        "container": container,
        "severity": severity.lower(),
        "action": action,
        "root_cause": root_cause,
        "confidence_percent": confidence_percent,
        "logs": logs[-4000:] if logs else "No logs captured.",
        "result": recovery_result.get("message", "No recovery result recorded."),
        "success": bool(recovery_result.get("success")),
        "container_status": recovery_result.get("container_status", "unknown"),
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
    }


def _log_to_console(payload: dict[str, Any]) -> None:
    logger.info(
        "Notification event | title=%s container=%s severity=%s action=%s result=%s",
        payload["title"],
        payload["container"],
        payload["severity"],
        payload["action"],
        payload["result"],
    )


def _send_email(payload: dict[str, Any]) -> None:
    recipients = [address.strip() for address in EMAIL_TO.split(",") if address.strip()]
    if not SMTP_HOST or not EMAIL_FROM or not recipients:
        logger.warning("Email notification skipped: SMTP_HOST, EMAIL_FROM, or EMAIL_TO is missing.")
        return

    message = EmailMessage()
    message["Subject"] = f"[{payload['severity'].upper()}] {payload['title']} — {payload['container']}"
    message["From"] = EMAIL_FROM
    message["To"] = ", ".join(recipients)
    message.set_content(_plain_text_body(payload))
    message.add_alternative(_html_body(payload), subtype="html")

    try:
        if SMTP_PORT == 465:
            with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=NOTIFICATION_TIMEOUT_SECONDS) as client:
                _authenticate_and_send(client, message, recipients)
        else:
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=NOTIFICATION_TIMEOUT_SECONDS) as client:
                client.ehlo()
                client.starttls()
                client.ehlo()
                _authenticate_and_send(client, message, recipients)
    except (OSError, smtplib.SMTPException) as exc:
        logger.warning("Email notification failed: %s", exc)


def _authenticate_and_send(
    client: smtplib.SMTP,
    message: EmailMessage,
    recipients: list[str],
) -> None:
    if SMTP_USERNAME:
        client.login(SMTP_USERNAME, SMTP_PASSWORD)
    client.send_message(message, to_addrs=recipients)


def _send_slack(payload: dict[str, Any]) -> None:
    if not SLACK_WEBHOOK_URL:
        logger.warning("Slack notification skipped: SLACK_WEBHOOK_URL is missing.")
        return

    emoji = _status_emoji(payload)
    text = (
        f"{emoji} *{payload['title']}*\n"
        f"*Container:* `{payload['container']}`\n"
        f"*Severity:* {payload['severity'].upper()}\n"
        f"*Root cause:* {payload['root_cause']}\n"
        f"*AI decision:* {payload['action'].title()} ({payload['confidence_percent']}% confidence)\n"
        f"*Recovery:* {payload['result']}\n"
        f"*Time:* {payload['timestamp']}"
    )
    _post_webhook("Slack", SLACK_WEBHOOK_URL, {"text": text})


def _send_discord(payload: dict[str, Any]) -> None:
    if not DISCORD_WEBHOOK_URL:
        logger.warning("Discord notification skipped: DISCORD_WEBHOOK_URL is missing.")
        return

    color = 0x45D796 if payload["success"] else 0xFF7186
    embed = {
        "title": f"{_status_emoji(payload)} {payload['title']}",
        "color": color,
        "fields": [
            {"name": "Container", "value": payload["container"], "inline": True},
            {"name": "Severity", "value": payload["severity"].upper(), "inline": True},
            {"name": "AI decision", "value": f"{payload['action'].title()} ({payload['confidence_percent']}%)", "inline": True},
            {"name": "Root cause", "value": payload["root_cause"], "inline": False},
            {"name": "Recovery", "value": payload["result"], "inline": False},
        ],
        "footer": {"text": payload["timestamp"]},
    }
    _post_webhook("Discord", DISCORD_WEBHOOK_URL, {"embeds": [embed]})


def _post_webhook(name: str, url: str, body: dict[str, Any]) -> None:
    try:
        response = requests.post(url, json=body, timeout=NOTIFICATION_TIMEOUT_SECONDS)
        response.raise_for_status()
    except requests.RequestException as exc:
        logger.warning("%s notification failed: %s", name, exc)


def _status_emoji(payload: dict[str, Any]) -> str:
    if not payload["success"] or payload["severity"] == "critical":
        return ":rotating_light:"
    if payload["severity"] == "high":
        return ":warning:"
    return ":white_check_mark:"


def _plain_text_body(payload: dict[str, Any]) -> str:
    return (
        f"{payload['title']}\n\n"
        f"Container: {payload['container']}\n"
        f"Severity: {payload['severity'].upper()}\n"
        f"Root Cause: {payload['root_cause']}\n"
        f"AI Confidence: {payload['confidence_percent']}%\n"
        f"AI Decision: {payload['action'].title()}\n"
        f"Recovery Result: {payload['result']}\n"
        f"Container Status: {payload['container_status']}\n"
        f"Timestamp: {payload['timestamp']}\n\n"
        f"Recent Logs:\n{payload['logs']}"
    )


def _html_body(payload: dict[str, Any]) -> str:
    def escaped(key: str) -> str:
        return html.escape(str(payload[key])).replace("\n", "<br>")

    return f"""<!doctype html>
<html><body style="font-family:Arial,sans-serif;color:#1f2937;line-height:1.5">
  <h2>{escaped('title')}</h2>
  <table style="border-collapse:collapse">
    <tr><td><b>Container</b></td><td>{escaped('container')}</td></tr>
    <tr><td><b>Severity</b></td><td>{escaped('severity').upper()}</td></tr>
    <tr><td><b>Root Cause</b></td><td>{escaped('root_cause')}</td></tr>
    <tr><td><b>AI Confidence</b></td><td>{escaped('confidence_percent')}%</td></tr>
    <tr><td><b>AI Decision</b></td><td>{escaped('action')}</td></tr>
    <tr><td><b>Recovery Result</b></td><td>{escaped('result')}</td></tr>
    <tr><td><b>Timestamp</b></td><td>{escaped('timestamp')}</td></tr>
  </table>
  <h3>Recent Logs</h3>
  <pre style="padding:12px;background:#f4f4f5;white-space:pre-wrap">{escaped('logs')}</pre>
</body></html>"""
