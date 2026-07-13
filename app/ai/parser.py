import json
from typing import Any


class DiagnosisParseError(ValueError):
    pass


def parse_json_object(payload: Any) -> dict[str, Any]:
    if isinstance(payload, dict):
        return payload

    if not payload:
        raise DiagnosisParseError("Empty LLM response.")

    text = str(payload).strip()

    if text.startswith("```"):
        text = text.strip("`").strip()
        if text.lower().startswith("json"):
            text = text[4:].strip()

    if text.startswith("["):
        raise DiagnosisParseError("Expected a JSON object, received an array.")

    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end <= start:
        raise DiagnosisParseError("No JSON object found in LLM response.")

    try:
        parsed = json.loads(text[start : end + 1])
    except json.JSONDecodeError as exc:
        raise DiagnosisParseError(f"Invalid LLM JSON: {exc}") from exc

    if not isinstance(parsed, dict):
        raise DiagnosisParseError("Expected a top-level JSON object.")

    return parsed
