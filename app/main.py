from datetime import datetime, timezone

from app.agent.observer import observe
from app.agent.reasoner import reason
from app.agent.decision import decide
from app.agent.executor import execute
from app.agent.memory import remember
from app.services.database_service import initialize_database


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _timeline_event(
    event: str,
    detail: str,
    timestamp: str | None = None,
) -> dict[str, str]:
    return {
        "event": event,
        "detail": detail,
        "timestamp": timestamp or _utc_timestamp(),
    }


def run():
    initialize_database()
    incidents = observe()

    print("\nDetected Incidents:")

    for incident in incidents:
        timeline = [
            _timeline_event(
                "Incident detected",
                ", ".join(incident["errors"]),
                incident.get("detected_at"),
            )
        ]

        diagnosis = reason(incident)
        timeline.append(
            _timeline_event(
                "Diagnosis complete",
                diagnosis["root_cause"],
            )
        )

        decision = decide(incident, diagnosis)
        timeline.append(
            _timeline_event(
                "Decision made",
                decision["reason"],
            )
        )

        timeline.append(
            _timeline_event(
                f"{decision['final_action'].title()} initiated",
                f"Executing {decision['final_action']} action",
            )
        )
        result = execute(incident, decision)
        timeline.append(
            _timeline_event(
                (
                    "Container healthy"
                    if result["success"]
                    and decision["final_action"] == "restart"
                    else "Recovery action complete"
                    if result["success"]
                    else "Recovery failed"
                ),
                result["message"],
            )
        )
        incident["timeline"] = timeline

        record = remember(incident, diagnosis, decision, result)

        print("\nIncident:")
        print(incident["container"])

        print("\nDiagnosis:")
        print(diagnosis)

        print("\nDecision:")
        print(decision)

        print("\nExecution Result:")
        print(result)

        print("\nMemory Record:")
        print(record)


if __name__ == "__main__":
    run()
