from app.ai import ai_service


def reason(incident):
    return ai_service.diagnose(incident)
