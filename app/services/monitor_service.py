"""Background orchestration for the ContainerDoctor autonomous agent cycle."""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Any

from app.agents.decision import decide
from app.agents.executor import execute
from app.agents.memory import remember, should_suppress
from app.agents.observer import observe
from app.agents.reasoner import reason
from app.config import CHECK_INTERVAL, TARGET_CONTAINERS


logger = logging.getLogger(__name__)


async def monitor_forever() -> None:
    """Run agent cycles until FastAPI cancels this task during shutdown."""
    logger.info("ContainerDoctor background monitor started (interval=%ss).", CHECK_INTERVAL)

    while True:
        try:
            run_monitoring_cycle()
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Unexpected monitoring cycle failure; continuing.")

        try:
            await asyncio.sleep(CHECK_INTERVAL)
        except asyncio.CancelledError:
            logger.info("ContainerDoctor background monitor stopped.")
            raise


def run_monitoring_cycle() -> dict[str, int | float]:
    """Run one complete observe → reason → decide → act → learn cycle."""
    started = time.monotonic()
    metrics: dict[str, int | float] = {
        "containers_checked": len(TARGET_CONTAINERS),
        "incidents_detected": 0,
        "incidents_suppressed": 0,
        "llm_calls_made": 0,
        "recoveries_attempted": 0,
        "notifications_sent": 0,
        "cycle_duration": 0.0,
    }
    logger.info("Starting monitoring cycle.")

    try:
        incidents = observe()
    except Exception:
        logger.exception("Observer failed for this cycle; continuing with the next cycle.")
        incidents = []

    metrics["incidents_detected"] = len(incidents)

    for incident in incidents:
        _process_incident(incident, metrics)

    metrics["cycle_duration"] = round(time.monotonic() - started, 3)
    logger.info(
        "Monitoring cycle complete | containers checked=%d incidents detected=%d "
        "suppressed=%d LLM calls made=%d recoveries attempted=%d "
        "notifications sent=%d duration=%.3fs",
        metrics["containers_checked"],
        metrics["incidents_detected"],
        metrics["incidents_suppressed"],
        metrics["llm_calls_made"],
        metrics["recoveries_attempted"],
        metrics["notifications_sent"],
        metrics["cycle_duration"],
    )
    return metrics


def _process_incident(incident: dict[str, Any], metrics: dict[str, int | float]) -> None:
    container = incident.get("container", "unknown")
    try:
        if should_suppress(incident):
            metrics["incidents_suppressed"] += 1
            logger.info("Suppressed duplicate incident for container '%s'.", container)
            return

        timeline = [_timeline_event(
            "Incident detected",
            ", ".join(incident.get("errors", [])),
            incident.get("detected_at"),
        )]

        metrics["llm_calls_made"] += 1
        diagnosis = reason(incident)
        timeline.append(_timeline_event(
            "LLM analysis complete" if diagnosis.get("ai_available") else "AI unavailable",
            diagnosis.get("root_cause") if diagnosis.get("ai_available") else diagnosis.get("ai_error", "Ollama diagnosis unavailable"),
        ))

        decision = decide(incident, diagnosis)
        timeline.append(_timeline_event("Decision made", decision["reason"]))
        timeline.append(_timeline_event(
            f"{decision['final_action'].title()} initiated",
            f"Executing {decision['final_action']} action",
        ))

        if decision["final_action"] == "restart":
            metrics["recoveries_attempted"] += 1

        result = execute(incident, decision, diagnosis)
        if decision["final_action"] in {"restart", "alert"}:
            metrics["notifications_sent"] += 1
        timeline.append(_timeline_event(_outcome_event(decision, result), result["message"]))
        incident["timeline"] = timeline
        remember(incident, diagnosis, decision, result)
        logger.info("Processed incident for container '%s'.", container)
    except Exception:
        logger.exception("Incident processing failed for container '%s'; continuing.", container)


def _timeline_event(event: str, detail: str, timestamp: str | None = None) -> dict[str, str]:
    return {
        "event": event,
        "detail": detail,
        "timestamp": timestamp or datetime.now(timezone.utc).isoformat(),
    }


def _outcome_event(decision: dict[str, Any], result: dict[str, Any]) -> str:
    if not result["success"]:
        return "Recovery failed"
    if decision["final_action"] == "restart":
        return "Container healthy"
    if decision["final_action"] == "alert":
        return "Alert triggered"
    if decision["final_action"] == "ignore":
        return "No action required"
    return "Recovery action complete"
