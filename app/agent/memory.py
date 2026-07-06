from typing import Any

from app.services.database_service import insert_incident


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
        "logs": incident.get("logs", ""),
        "root_cause": diagnosis["root_cause"],
        "severity": diagnosis["severity"],
        "action": decision["final_action"],
        "decision": decision,
        "result": result,
        "timeline": incident.get("timeline", []),
        "timestamp": (
            incident["timeline"][-1]["timestamp"]
            if incident.get("timeline")
            else None
        ),
    }

    return insert_incident(record)
