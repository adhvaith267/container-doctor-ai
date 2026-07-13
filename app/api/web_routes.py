"""Server-rendered dashboard routes."""

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.ai import ai_service
from app.services.analytics_service import calculate_incident_analytics
from app.services.database_service import fetch_incident, fetch_incidents
from app.services.docker_service import (
    get_active_container_names,
    is_docker_connected,
)


templates = Jinja2Templates(
    directory=str(Path(__file__).resolve().parents[1] / "templates")
)
router = APIRouter(include_in_schema=False)


def _display_timestamp(value: str) -> str:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc).strftime("%d %b %Y, %H:%M UTC")
    except (TypeError, ValueError):
        return value


def _timeline_time(value: str) -> str:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc).strftime("%H:%M")
    except (TypeError, ValueError):
        return "--:--"


def _prepare_incidents(
    incidents: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        {
            **incident,
            "display_timestamp": _display_timestamp(incident["timestamp"]),
        }
        for incident in incidents
    ]


def _base_context(
    request: Request,
    active_page: str,
    docker_connected: bool | None = None,
) -> dict[str, Any]:
    return {
        "request": request,
        "active_page": active_page,
        "docker_connected": (
            is_docker_connected()
            if docker_connected is None
            else docker_connected
        ),
    }


def _dashboard_metrics() -> dict[str, Any]:
    incidents = fetch_incidents()
    analytics = calculate_incident_analytics(incidents)
    docker_connected = is_docker_connected()
    active_containers = (
        get_active_container_names() if docker_connected else []
    )
    ai_engine = ai_service.health()
    latest_incident = incidents[0] if incidents else None

    return {
        "incidents": incidents,
        "analytics": analytics,
        "docker_connected": docker_connected,
        "active_containers": active_containers,
        "ai_engine": ai_engine,
        "latest_ai_decision": _latest_ai_decision(latest_incident),
    }


def _latest_ai_decision(incident: dict[str, Any] | None) -> dict[str, Any] | None:
    if incident is None:
        return None

    return {
        "container": incident["container"],
        "root_cause": incident["root_cause"],
        "action": incident["action"],
        "severity": incident["severity"],
        "confidence": incident.get("confidence", 0),
        "provider": incident.get("llm_provider") or "ollama",
        "model": incident.get("llm_model") or "unknown",
    }


def _agent_statuses(incident: dict[str, Any]) -> list[dict[str, str]]:
    decision = incident.get("decision") or {}
    result = incident.get("execution_result") or incident.get("result") or {}

    return [
        {
            "agent": "Observer",
            "status": "Completed",
            "detail": f"{len(incident.get('detected_errors') or incident.get('errors') or [])} error patterns detected",
        },
        {
            "agent": "Reasoner",
            "status": (
                "Ollama response received"
                if incident.get("llm_response")
                else "AI unavailable"
            ),
            "detail": incident.get("root_cause", "No diagnosis recorded"),
        },
        {
            "agent": "Decision",
            "status": f"{decision.get('final_action', incident.get('action', 'unknown')).title()} selected",
            "detail": decision.get("reason", "No decision reason recorded"),
        },
        {
            "agent": "Executor",
            "status": (
                "Recovery successful"
                if result.get("success")
                else "Recovery failed"
            ),
            "detail": result.get("message", "No execution result recorded"),
        },
        {
            "agent": "Memory",
            "status": "Incident persisted",
            "detail": f"SQLite incident #{incident['id']}",
        },
    ]


@router.get("/", response_class=HTMLResponse, name="dashboard")
def dashboard(request: Request) -> HTMLResponse:
    metrics = _dashboard_metrics()
    analytics = metrics["analytics"]

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            **_base_context(
                request,
                "dashboard",
                metrics["docker_connected"],
            ),
            "active_containers": metrics["active_containers"],
            "analytics": analytics,
            "recent_incidents": _prepare_incidents(
                metrics["incidents"][:6]
            ),
            "problematic_containers": analytics["container_breakdown"][:5],
            "ai_engine": metrics["ai_engine"],
            "latest_ai_decision": metrics["latest_ai_decision"],
        },
    )


@router.get("/dashboard/metrics", name="dashboard_metrics")
def dashboard_metrics(response: Response) -> dict[str, Any]:
    metrics = _dashboard_metrics()
    analytics = metrics["analytics"]
    response.headers["Cache-Control"] = "no-store"

    return {
        "docker_connected": metrics["docker_connected"],
        "active_containers": len(metrics["active_containers"]),
        "total_incidents": analytics["total_incidents"],
        "recovery_success_rate": analytics["restart_success_rate"],
        "successful_restarts": analytics["successful_restarts"],
        "restart_attempts": analytics["restart_attempts"],
        "most_problematic_container": (
            analytics["most_problematic_container"] or "None"
        ),
        "ai_engine_status": (
            "online" if metrics["ai_engine"]["available"] else "unavailable"
        ),
        "ai_engine_model": metrics["ai_engine"]["model"],
        "latest_ai_decision": metrics["latest_ai_decision"],
        "recent_incidents": [
            {
                "id": incident["id"],
                "container": incident["container"],
                "root_cause": incident["root_cause"],
                "severity": incident["severity"],
                "action": incident["action"],
                "success": bool(incident["result"].get("success")),
                "display_timestamp": incident["display_timestamp"],
            }
            for incident in _prepare_incidents(metrics["incidents"][:6])
        ],
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/history", response_class=HTMLResponse, name="incident_history")
def incident_history(request: Request) -> HTMLResponse:
    incidents = _prepare_incidents(fetch_incidents())

    return templates.TemplateResponse(
        request=request,
        name="incidents.html",
        context={
            **_base_context(request, "history"),
            "incidents": incidents,
        },
    )


@router.get(
    "/history/{incident_id}",
    response_class=HTMLResponse,
    name="incident_detail",
)
def incident_detail(request: Request, incident_id: int) -> HTMLResponse:
    incident = fetch_incident(incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")

    prepared_incident = _prepare_incidents([incident])[0]
    timeline = incident["timeline"] or [
        {
            "event": "Incident recorded",
            "detail": "Detailed stage timing was not captured for this incident.",
            "timestamp": incident["timestamp"],
        }
    ]
    prepared_incident["timeline"] = [
        {
            **event,
            "display_timestamp": _display_timestamp(event["timestamp"]),
            "display_time": _timeline_time(event["timestamp"]),
        }
        for event in timeline
    ]

    return templates.TemplateResponse(
        request=request,
        name="incident_detail.html",
        context={
            **_base_context(request, "history"),
            "incident": prepared_incident,
            "agent_statuses": _agent_statuses(prepared_incident),
        },
    )


@router.get(
    "/analytics-dashboard",
    response_class=HTMLResponse,
    name="analytics_dashboard",
)
def analytics_dashboard(request: Request) -> HTMLResponse:
    incidents = fetch_incidents()

    return templates.TemplateResponse(
        request=request,
        name="analytics.html",
        context={
            **_base_context(request, "analytics"),
            "analytics": calculate_incident_analytics(incidents),
        },
    )
