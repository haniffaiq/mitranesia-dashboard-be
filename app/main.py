from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes_admin_users import router as admin_users_router
from app.api.routes_auth import router as auth_router
from app.api.routes_carousels import router as carousels_router
from app.api.routes_client import router as client_router
from app.api.routes_client_auth import router as client_auth_router
from app.api.routes_client_leads import router as client_leads_router
from app.api.routes_dashboard import router as dashboard_router
from app.api.routes_insights import router as insights_router
from app.api.routes_merchants import router as merchants_router
from app.api.routes_sitemap import router as sitemap_router
from app.core.config import Settings, get_settings
from app.core.rate_limit import LoginRateLimiter
from app.db.base import Base
from app.db.session import create_engine_and_session
from app.services.bootstrap import seed_default_superadmin


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    engine, session_local = create_engine_and_session(settings)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        if settings.create_tables_on_start:
            Base.metadata.create_all(bind=engine)
        with session_local() as db:
            seed_default_superadmin(db, settings)
        yield

    app = FastAPI(title=settings.app_name, lifespan=lifespan)

    app.state.settings = settings
    app.state.engine = engine
    app.state.session_local = session_local
    app.state.login_rate_limiter = LoginRateLimiter()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(_: Request, exc: RequestValidationError):
        errors: dict[str, list[str]] = {}
        for error in exc.errors():
            field = ".".join(str(part) for part in error["loc"] if part != "body")
            errors.setdefault(field or "body", []).append(error["msg"])
        return JSONResponse(status_code=422, content={"message": "Validation error", "errors": errors})

    @app.exception_handler(ValueError)
    async def value_error_handler(_: Request, exc: ValueError):
        return JSONResponse(status_code=422, content={"message": "Validation error", "errors": {"body": [str(exc)]}})

    @app.get("/health")
    def health():
        return {"status": "ok"}

    app.include_router(auth_router, prefix="/api")
    app.include_router(client_router, prefix="/api")
    app.include_router(client_auth_router, prefix="/api")
    app.include_router(client_leads_router, prefix="/api")
    app.include_router(dashboard_router, prefix="/api")
    app.include_router(carousels_router, prefix="/api")
    app.include_router(merchants_router, prefix="/api")
    app.include_router(insights_router, prefix="/api")
    app.include_router(admin_users_router, prefix="/api")
    app.include_router(sitemap_router)  # no /api prefix — served at root
    return app


app = create_app()
