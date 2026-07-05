restart_history = {}


def decide(incident, diagnosis):
    container = incident["container"]

    action = diagnosis["action"]

    if action == "restart":
        count = restart_history.get(container, 0)

        if count >= 3:
            return {
                "approved": False,
                "final_action": "alert",
                "reason": "Restart limit exceeded"
            }

        return {
            "approved": True,
            "final_action": "restart",
            "reason": "Safe to restart"
        }

    return {
        "approved": True,
        "final_action": action,
        "reason": "Normal action"
    }