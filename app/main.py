from app.services.database_service import initialize_database
from app.services.monitor_service import run_monitoring_cycle


def run():
    """Run exactly one monitoring cycle for local debugging."""
    initialize_database()
    return run_monitoring_cycle()


if __name__ == "__main__":
    run()
