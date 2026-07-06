"""FastAPI application entry point for ContainerDoctor AI."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routes import router as api_router
from app.api.web_routes import router as web_router
from app.services.database_service import initialize_database


APP_DIRECTORY = Path(__file__).resolve().parents[1]


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Initialize API resources before accepting requests."""
    initialize_database()
    yield


def create_app() -> FastAPI:
    """Create and configure the ContainerDoctor API application."""
    application = FastAPI(
        title="ContainerDoctor AI",
        lifespan=lifespan,
    )
    application.mount(
        "/static",
        StaticFiles(directory=str(APP_DIRECTORY / "static")),
        name="static",
    )
    application.include_router(web_router)
    application.include_router(api_router)
    return application


app = create_app()
