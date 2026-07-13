from __future__ import annotations

import logging
import time
from typing import Any

import docker


logger = logging.getLogger(__name__)
_docker_client: Any | None = None


def get_docker_client() -> Any:
    global _docker_client
    if _docker_client is None:
        _docker_client = docker.from_env()
    return _docker_client


def is_docker_connected() -> bool:
    """Return whether the Docker daemon is reachable."""
    try:
        return bool(get_docker_client().ping())
    except Exception as exc:
        logger.debug("Docker daemon is unavailable: %s", exc)
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


def get_container_logs(container_name: str, log_lines: int) -> str | None:
    """Return recent Docker logs for a container, or None when unavailable."""
    try:
        container = get_docker_client().containers.get(container_name)
        logs = container.logs(
            tail=log_lines,
            timestamps=True,
        ).decode("utf-8", errors="replace")
        return logs
    except Exception as exc:
        logger.warning(
            "Unable to fetch logs for container '%s': %s",
            container_name,
            exc,
        )
        return None


def restart_container(container_name: str) -> bool:
    """Restart a container and return whether it is running afterwards."""
    try:
        container = get_docker_client().containers.get(container_name)
        container.restart(timeout=30)

        time.sleep(5)
        container.reload()

        return container.status == "running"
    except Exception as exc:
        logger.warning(
            "Unable to restart container '%s': %s",
            container_name,
            exc,
        )
        return False
