"""BETPREDICT AI — FastAPI application entrypoint."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api.deps import RateLimitMiddleware
from app.api.routes import api_router
from app.core.config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    app.state.settings = settings
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        description=(
            "Statistical football prediction platform. "
            "Probabilities are estimates — never certainties. "
            "Information-only service; no stakes accepted."
        ),
        openapi_url=f"{settings.api_v1_prefix}/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RateLimitMiddleware, limit=180, window=60)
    app.include_router(api_router, prefix=settings.api_v1_prefix)

    @app.get("/health")
    async def health():
        return {
            "status": "ok",
            "app": settings.app_name,
            "version": __version__,
            "demo_mode": settings.is_demo,
        }

    return app


app = create_app()
