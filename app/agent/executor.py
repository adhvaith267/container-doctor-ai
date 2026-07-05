from app.services.docker_service import restart_container
from app.agent.decision import restart_history


def execute(incident, decision):
    container = incident["container"]
    action = decision["final_action"]

    if not decision["approved"]:
        return {
            "success": False,
            "message": "Action not approved"
        }

    if action == "restart":
        success = restart_container(container)

        if success:
            restart_history[container] = restart_history.get(container, 0) + 1

            return {
                "success": True,
                "message": f"{container} restarted successfully"
            }

        return {
            "success": False,
            "message": f"Failed to restart {container}"
        }

    if action == "alert":
        return {
            "success": True,
            "message": "Alert triggered"
        }

    return {
        "success": False,
        "message": "Unknown action"
    }