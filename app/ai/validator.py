from typing import Any


ALLOWED_SEVERITIES = {"low", "medium", "high", "critical"}
ALLOWED_ACTIONS = {"restart", "alert", "ignore"}


class DiagnosisValidationError(ValueError):
    pass


def validate_diagnosis(payload: dict[str, Any]) -> dict[str, Any]:
    root_cause = str(payload.get("root_cause", "")).strip()
    severity = str(payload.get("severity", "")).strip().lower()
    action = str(payload.get("action", "")).strip().lower()

    try:
        confidence = float(payload.get("confidence", 0.0))
    except (TypeError, ValueError) as exc:
        raise DiagnosisValidationError("confidence must be a number.") from exc

    if not root_cause:
        raise DiagnosisValidationError("root_cause is required.")

    if severity not in ALLOWED_SEVERITIES:
        raise DiagnosisValidationError(
            f"severity must be one of {sorted(ALLOWED_SEVERITIES)}."
        )

    if action not in ALLOWED_ACTIONS:
        raise DiagnosisValidationError(
            f"action must be one of {sorted(ALLOWED_ACTIONS)}."
        )

    confidence = max(0.0, min(confidence, 1.0))

    return {
        "root_cause": root_cause,
        "severity": severity,
        "action": action,
        "confidence": round(confidence, 3),
    }
