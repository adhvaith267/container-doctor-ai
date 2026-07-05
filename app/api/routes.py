from datetime import datetime
from app.monitor import diagnosis_history, fix_history
from app.services.docker_service import get_docker_client

def health():
    try:
        get_docker_client().ping()
        docker_ok = True
    except:
        docker_ok = False

    return {
        "status": "healthy" if docker_ok else "degraded",
        "docker_connected": docker_ok,
        "total_diagnoses": len(diagnosis_history),
        "fixes_applied": {k: len(v) for k, v in fix_history.items()},
        "uptime_check": datetime.now().isoformat()
    }

def history():
    return diagnosis_history[-50:]