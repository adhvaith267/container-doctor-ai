from datetime import datetime, timedelta

last_error_seen = {}

rate_limit_counter = {}
rate_limit_reset = datetime.now() + timedelta(hours=1)
def detect_errors(logs: str) -> list[str]:
    """
    Scan container logs and return unique detected error patterns.
    """

    error_patterns = [
        "error",
        "exception",
        "traceback",
        "failed",
        "crash",
        "fatal",
        "panic",
        "segmentation fault",
        "out of memory",
        "killed",
        "oomkiller",
        "connection refused",
    ]

    ignore_patterns = [
        "query timeout",
        "timeout policy",
        "configuration",
    ]

    found = []
    seen = set()

    for line in logs.lower().splitlines():

        if any(ignore in line for ignore in ignore_patterns):
            continue

        for pattern in error_patterns:
            if pattern in line and pattern not in seen:
                found.append(pattern)
                seen.add(pattern)

    return found