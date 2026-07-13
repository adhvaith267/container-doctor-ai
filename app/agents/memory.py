from typing import Any

from app.config import INCIDENT_SUPPRESSION_SECONDS
from app.services.database_service import (
    has_recent_matching_incident,
    insert_incident,
)


def should_suppress(incident: dict[str, Any]) -> bool:
    """Return whether Memory already holds this incident inside the suppression window."""
    return has_recent_matching_incident(
        container=incident["container"],
        errors=incident["errors"],
        suppression_seconds=INCIDENT_SUPPRESSION_SECONDS,
    )


def remember(
    incident: dict[str, Any],
    diagnosis: dict[str, Any],
    decision: dict[str, Any],
    result: dict[str, Any],
) -> dict[str, Any]:
    """Persist the completed agent cycle and return the stored incident."""
    record = {
        "container": incident["container"],
        "errors": incident["errors"],
        "detected_errors": incident["errors"],
        "logs": incident.get("logs", ""),
        "prompt": diagnosis.get("prompt", ""),
        "llm_provider": diagnosis.get("llm_provider", ""),
        "llm_model": diagnosis.get("llm_model", ""),
        "llm_latency": diagnosis.get("llm_latency", 0.0),
        "llm_response": diagnosis.get("llm_response", ""),
        "confidence": diagnosis.get("confidence", 0.0),
        "root_cause": diagnosis["root_cause"],
        "severity": diagnosis["severity"],
        "action": decision["final_action"],
        "decision": decision,
        "result": result,
        "execution_result": result,
        "timeline": incident.get("timeline", []),
        "timestamp": (
            incident["timeline"][-1]["timestamp"]
            if incident.get("timeline")
            else None
        ),
    }

    return insert_incident(record)
