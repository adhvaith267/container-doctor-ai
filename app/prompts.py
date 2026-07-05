DIAGNOSIS_PROMPT = """
You are a DevOps expert analyzing container logs.

Container: {container_name}
Timestamp: {timestamp}
Detected patterns: {error_patterns}

Recent logs:
---
{logs}
---

Analyze these logs and respond with ONLY valid JSON:

{
    "root_cause": "...",
    "severity": "low|medium|high",
    "suggested_fix": "...",
    "auto_restart_safe": true,
    "config_suggestions": [],
    "likely_recurring": false,
    "estimated_impact": "..."
}
"""