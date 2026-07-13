import requests


class OllamaClientError(RuntimeError):
    pass


def generate(
    prompt: str,
    model: str,
    base_url: str,
    timeout: float,
) -> str:
    """Send a prompt to Ollama and return the raw model response text."""
    endpoint = f"{base_url.rstrip('/')}/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {
            "temperature": 0.1,
        },
    }

    try:
        response = requests.post(endpoint, json=payload, timeout=timeout)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as exc:
        raise OllamaClientError(f"Ollama request failed: {exc}") from exc
    except ValueError as exc:
        raise OllamaClientError("Ollama returned a non-JSON HTTP response.") from exc

    response_text = data.get("response")
    if not response_text:
        raise OllamaClientError("Ollama returned an empty response.")

    return str(response_text)


def list_models(
    base_url: str,
    timeout: float,
) -> list[str]:
    """Return model names reported by Ollama."""
    endpoint = f"{base_url.rstrip('/')}/api/tags"

    try:
        response = requests.get(endpoint, timeout=timeout)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as exc:
        raise OllamaClientError(f"Ollama health request failed: {exc}") from exc
    except ValueError as exc:
        raise OllamaClientError("Ollama returned a non-JSON health response.") from exc

    models = data.get("models", [])
    if not isinstance(models, list):
        raise OllamaClientError("Ollama health response did not include models.")

    return [
        str(model.get("name"))
        for model in models
        if isinstance(model, dict) and model.get("name")
    ]
