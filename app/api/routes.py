from typing import Any, Literal

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.config import TARGET_CONTAINERS
from app.services.analytics_service import calculate_incident_analytics
from app.services.database_service import count_incidents, fetch_incidents
from app.services.docker_service import is_docker_connected

router = APIRouter()


class HealthResponse(BaseModel):
    docker_status: Literal["connected", "unavailable"]
    monitored_containers: list[str]
    total_incidents: int = Field(ge=0)


class IncidentResponse(BaseModel):
    id: int
    container: str
    errors: list[str]
    detected_errors: list[str]
    logs: str
    prompt: str
    llm_provider: str
    llm_model: str
    llm_latency: float = Field(ge=0.0)
    llm_response: str
    confidence: float = Field(ge=0.0, le=1.0)
    root_cause: str
    severity: str
    action: str
    decision: dict[str, Any]
    result: dict[str, Any]
    execution_result: dict[str, Any]
    timeline: list[dict[str, Any]]
    timestamp: str


class AnalyticsResponse(BaseModel):
    total_incidents: int = Field(ge=0)
    restart_success_rate: float = Field(ge=0.0, le=100.0)
    most_problematic_container: str | None


def _monitored_containers() -> list[str]:
    names = (name.strip() for name in TARGET_CONTAINERS)
    return list(dict.fromkeys(name for name in names if name))


@router.get("/health", response_model=HealthResponse, tags=["system"])
def health() -> HealthResponse:
    docker_status = (
        "connected" if is_docker_connected() else "unavailable"
    )

    return HealthResponse(
        docker_status=docker_status,
        monitored_containers=_monitored_containers(),
        total_incidents=count_incidents(),
    )


@router.get("/incidents", response_model=list[IncidentResponse], tags=["incidents"])
def incidents() -> list[dict[str, Any]]:
    return fetch_incidents()


@router.get("/analytics", response_model=AnalyticsResponse, tags=["analytics"])
def analytics() -> AnalyticsResponse:
    records = fetch_incidents()
    incident_analytics = calculate_incident_analytics(records)

    return AnalyticsResponse(
        total_incidents=incident_analytics["total_incidents"],
        restart_success_rate=incident_analytics["restart_success_rate"],
        most_problematic_container=incident_analytics[
            "most_problematic_container"
        ],
    )
