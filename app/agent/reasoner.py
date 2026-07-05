def reason(incident):
    logs = incident["logs"].lower()
    errors = incident["errors"]

    diagnosis = {
        "root_cause": "Unknown issue",
        "severity": "low",
        "action": "ignore"
    }

    if "connection refused" in logs:
        diagnosis["root_cause"] = "Database connection failure"
        diagnosis["severity"] = "high"
        diagnosis["action"] = "restart"

    elif "out of memory" in logs:
        diagnosis["root_cause"] = "Memory exhaustion"
        diagnosis["severity"] = "high"
        diagnosis["action"] = "restart"

    elif "timeout" in errors:
        diagnosis["root_cause"] = "Service timeout"
        diagnosis["severity"] = "medium"
        diagnosis["action"] = "alert"

    return diagnosis