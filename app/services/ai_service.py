import json
from datetime import datetime
from app.prompts import DIAGNOSIS_PROMPT

def diagnose_issue(container_name, logs, error_patterns):
    prompt = DIAGNOSIS_PROMPT.format(
        container_name=container_name,
        timestamp=datetime.now().isoformat(),
        error_patterns=", ".join(error_patterns),
        logs=logs
    )

    print(prompt)
    return None

def parse_diagnosis(diagnosis_text):
    if not diagnosis_text:
        return None

    try:
        start = diagnosis_text.find("{")
        end = diagnosis_text.rfind("}") + 1

        if start >= 0 and end > start:
            json_str = diagnosis_text[start:end]
            return json.loads(json_str)

    except Exception as e:
        print(f"JSON parse error: {e}")

    return None