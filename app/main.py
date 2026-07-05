from app.agent.observer import observe
from app.agent.reasoner import reason
from app.agent.decision import decide
from app.agent.executor import execute
from app.agent.memory import remember


def run():
    incidents = observe()

    print("\nDetected Incidents:")

    for incident in incidents:
        diagnosis = reason(incident)
        decision = decide(incident, diagnosis)
        result = execute(incident, decision)
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