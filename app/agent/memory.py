memory_store = []


def remember(incident, diagnosis, decision, result):
    record = {
        "container": incident["container"],
        "errors": incident["errors"],
        "diagnosis": diagnosis,
        "decision": decision,
        "result": result
    }

    memory_store.append(record)

    return record