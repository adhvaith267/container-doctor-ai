import logging
import time

import docker


logger = logging.getLogger(__name__)
docker_client = None


def get_docker_client():
    global docker_client
    if docker_client is None:
        docker_client = docker.from_env()
    return docker_client


def is_docker_connected() -> bool:
    """Return whether the Docker daemon is reachable."""
    try:
        return bool(get_docker_client().ping())
    except Exception:
        return False


def get_active_container_names() -> list[str]:
    """Return the names of currently running Docker containers."""
    try:
        containers = get_docker_client().containers.list(
            filters={"status": "running"}
        )
        return sorted(container.name for container in containers)
    except Exception as exc:
        logger.warning("Unable to list active Docker containers: %s", exc)
        return []


def get_container_logs(container_name, log_lines):
    try:
        container = get_docker_client().containers.get(container_name)
        logs = container.logs(
            tail=log_lines,
            timestamps=True
        ).decode("utf-8")
        return logs
    except Exception as e:
        print(f"Error fetching logs: {e}")
        return None


def restart_container(container_name):
    try:
        container = get_docker_client().containers.get(container_name)
        container.restart(timeout=30)

        time.sleep(5)
        container.reload()

        return container.status == "running"
    except Exception as e:
        print(f"Restart failed: {e}")
        return False
