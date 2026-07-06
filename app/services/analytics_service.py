"""Incident analytics shared by API and dashboard views."""

from collections import Counter
from collections.abc import Mapping, Sequence
from typing import Any


def _breakdown(
    counter: Counter[str],
    total: int,
) -> list[dict[str, Any]]:
    return [
        {
            "name": name,
            "count": count,
            "percentage": round(count / total * 100, 1) if total else 0.0,
        }
        for name, count in sorted(
            counter.items(),
            key=lambda item: (-item[1], item[0].lower()),
        )
    ]


def calculate_incident_analytics(
    records: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Calculate recovery and incident distribution metrics."""
    total_incidents = len(records)

    container_counts = Counter(
        str(record["container"])
        for record in records
        if record.get("container")
    )
    severity_counts = Counter(
        str(record.get("severity", "unknown")).lower()
        for record in records
    )
    action_counts = Counter(
        str(record.get("action", "unknown")).lower()
        for record in records
    )

    restart_records = [
        record
        for record in records
        if str(record.get("action", "")).lower() == "restart"
    ]
    successful_restarts = sum(
        isinstance(record.get("result"), Mapping)
        and record["result"].get("success") is True
        for record in restart_records
    )
    restart_success_rate = (
        round(successful_restarts / len(restart_records) * 100, 1)
        if restart_records
        else 0.0
    )

    container_breakdown = _breakdown(container_counts, total_incidents)

    return {
        "total_incidents": total_incidents,
        "restart_attempts": len(restart_records),
        "successful_restarts": successful_restarts,
        "restart_success_rate": restart_success_rate,
        "most_problematic_container": (
            container_breakdown[0]["name"] if container_breakdown else None
        ),
        "container_breakdown": container_breakdown,
        "severity_breakdown": _breakdown(severity_counts, total_incidents),
        "action_breakdown": _breakdown(action_counts, total_incidents),
    }
