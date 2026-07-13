from datetime import datetime, timezone
from app.config import TARGET_CONTAINERS, LOG_LINES
from app.services.log_service import detect_errors
from app.services.docker_service import get_container_logs


def observe():
    incidents = []

    for container_name in TARGET_CONTAINERS:
        container_name = container_name.strip()

        logs = get_container_logs(container_name, LOG_LINES)

        if not logs:
            continue

        errors = detect_errors(logs)

        if errors:
            incidents.append({
                "container": container_name,
                "logs": "\n".join(logs.split("\n")[-10:]),
                "errors": errors,
                "detected_at": datetime.now(timezone.utc).isoformat(),
            })
    

    return incidents
