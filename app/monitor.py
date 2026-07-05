from datetime import datetime, timedelta
from collections import defaultdict

diagnosis_history = []
fix_history = defaultdict(list)
last_error_seen = {}
rate_limit_counter = defaultdict(int)
rate_limit_reset = datetime.now() + timedelta(hours=1)

def detect_errors(logs):
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
        "connection refused"
    ]

    ignore_patterns = [
        "query timeout",
        "timeout policy",
        "configuration"
    ]

    found = []
    lines = logs.lower().split("\n")

    for line in lines:
        skip = False

        for ignore in ignore_patterns:
            if ignore in line:
                skip = True
                break

        if skip:
            continue

        for pattern in error_patterns:
            if pattern in line:
                found.append(pattern)

    return list(set(found))

def is_new_error(container_name, logs):
    log_hash = hash(logs[-200:])

    if last_error_seen.get(container_name) == log_hash:
        return False

    last_error_seen[container_name] = log_hash
    return True

def check_rate_limit(max_diagnoses):
    global rate_limit_counter, rate_limit_reset

    now = datetime.now()

    if now > rate_limit_reset:
        rate_limit_counter.clear()
        rate_limit_reset = now + timedelta(hours=1)

    total = sum(rate_limit_counter.values())

    if total >= max_diagnoses:
        return False

    return True