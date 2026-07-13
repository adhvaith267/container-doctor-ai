from app.services.docker_service import restart_container
from app.services.notification_service import send_notification
from app.agents.decision import restart_history


def execute(incident, decision, diagnosis=None):
    container = incident["container"]
    action = decision["final_action"]

    if action == "alert":
        result = {
            "success": True,
            "message": "Alert triggered",
            "executed_action": "alert",
            "container_status": "not_checked",
        }
        _notify(incident, decision, diagnosis, "Container alert requires attention", result)
        return result

    if not decision["approved"]:
        return {
            "success": False,
            "message": "Action not approved",
            "executed_action": "none",
            "container_status": "not_checked",
        }

    if action == "restart":
        success = restart_container(container)

        if success:
            restart_history[container] = restart_history.get(container, 0) + 1
            result = {
                "success": True,
                "message": f"{container} restarted successfully",
                "executed_action": "restart",
                "container_status": "running",
            }
            _notify(incident, decision, diagnosis, "Container recovery succeeded", result)
            return result

        result = {
            "success": False,
            "message": f"Failed to restart {container}",
            "executed_action": "restart",
            "container_status": "unknown",
        }
        _notify(incident, decision, diagnosis, "Critical container recovery failure", result)
        return result

    if action == "ignore":
        return {
            "success": True,
            "message": "No recovery action required",
            "executed_action": "ignore",
            "container_status": "not_checked",
        }

    return {
        "success": False,
        "message": "Unknown action",
        "executed_action": action,
        "container_status": "unknown",
    }


def _notify(incident, decision, diagnosis, title, result):
    """Build the executor-owned notification payload without affecting recovery."""
    diagnosis = diagnosis or {}
    try:
        send_notification(
            title=title,
            container=incident["container"],
            severity=(
                "critical"
                if not result["success"]
                else diagnosis.get("severity", "medium")
            ),
            action=decision["final_action"],
            root_cause=diagnosis.get("root_cause", "No AI diagnosis recorded."),
            confidence=diagnosis.get("confidence", 0.0),
            logs=incident.get("logs", ""),
            recovery_result=result,
        )
    except Exception:
        # Notification delivery is best effort; executor results must remain reliable.
        return
