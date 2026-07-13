import logging
import time
from typing import Any

from app.ai import ollama_client
from app.ai.parser import DiagnosisParseError, parse_json_object
from app.ai.prompts import build_diagnosis_prompt
from app.ai.validator import DiagnosisValidationError, validate_diagnosis
from app.config import OLLAMA_BASE_URL, OLLAMA_MODEL, OLLAMA_TIMEOUT_SECONDS


logger = logging.getLogger(__name__)
PROVIDER = "ollama"


def diagnose(incident: dict[str, Any]) -> dict[str, Any]:
    """Return a validated diagnosis for an observed incident."""
    container_name = incident.get("container", "unknown")
    logs = incident.get("logs", "")
    errors = incident.get("errors", [])
    prompt = build_diagnosis_prompt(container_name, logs, errors)

    started = time.perf_counter()
    try:
        raw_response = ollama_client.generate(
            prompt=prompt,
            model=get_model(),
            base_url=OLLAMA_BASE_URL,
            timeout=OLLAMA_TIMEOUT_SECONDS,
        )
        latency = round(time.perf_counter() - started, 3)
        parsed_response = parse_json_object(raw_response)
        diagnosis = validate_diagnosis(parsed_response)

        return {
            **diagnosis,
            "ai_available": True,
            "llm_provider": get_provider(),
            "llm_model": get_model(),
            "llm_latency": latency,
            "prompt": prompt,
            "llm_response": raw_response,
        }
    except (
        ollama_client.OllamaClientError,
        DiagnosisParseError,
        DiagnosisValidationError,
    ) as exc:
        logger.warning(
            "Ollama diagnosis unavailable for container '%s': %s",
            container_name,
            exc,
        )
        return _unavailable_diagnosis(prompt, str(exc))


def health() -> dict[str, Any]:
    """Return Ollama availability and configured model information."""
    started = time.perf_counter()
    try:
        models = ollama_client.list_models(
            base_url=OLLAMA_BASE_URL,
            timeout=min(OLLAMA_TIMEOUT_SECONDS, 1.5),
        )
        latency_ms = round((time.perf_counter() - started) * 1000)
    except ollama_client.OllamaClientError as exc:
        logger.debug("Ollama health check failed: %s", exc)
        return {
            "available": False,
            "provider": get_provider(),
            "model": get_model(),
            "model_loaded": False,
            "latency_ms": None,
        }

    configured_model = get_model().split(":")[0]
    normalized_models = {model.split(":")[0] for model in models}

    return {
        "available": True,
        "provider": get_provider(),
        "model": get_model(),
        "model_loaded": configured_model in normalized_models,
        "latency_ms": latency_ms,
    }


def get_provider() -> str:
    return PROVIDER


def get_model() -> str:
    return OLLAMA_MODEL


def _unavailable_diagnosis(prompt: str, error: str) -> dict[str, Any]:
    return {
        "root_cause": "AI unavailable",
        "severity": "critical",
        "action": "alert",
        "confidence": 0.0,
        "ai_available": False,
        "ai_error": error,
        "llm_provider": get_provider(),
        "llm_model": get_model(),
        "llm_latency": 0.0,
        "prompt": prompt,
        "llm_response": "",
    }
