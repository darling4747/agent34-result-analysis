"""Agent 34 - Result Analysis Agent - FastAPI Application."""
from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import get_settings
from .database import init_db
from .utils.helpers import ensure_dirs
from .api.routes import (
    results, analysis, correlation, historical,
    interventions, reports, dashboard, health, auth, config,
)
from .api.routes import admin as admin_routes

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    ensure_dirs([settings.UPLOAD_DIR, settings.REPORT_DIR])
    init_db()
    try:
        from .database import SessionLocal
        from .services.auth_service import AuthService
        db = SessionLocal()
        try:
            AuthService(db, settings).seed_roles_and_permissions()
        finally:
            db.close()
    except Exception as exc:
        logger.warning("Role seed warning: %s", exc)
    logger.info("Agent 34 started.")
    yield
    logger.info("Agent 34 shutting down.")


settings = get_settings()

app = FastAPI(
    title="Agent 34 - Result Analysis Agent",
    description=(
        "Academic Result Analysis Agent - Agentic AI Platform for Academic Institutions.\n\n"
        "**Authentication:** All analytics endpoints require a Bearer JWT.\n"
        "Obtain via POST /api/auth/login.\n\n"
        "**Upstream:** Agent 3 (course allocation), Agent 33 (internal marks)\n"
        "**Downstream:** Agent 8 (attainment), Agent 35 (backlogs)"
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_origin_regex=r"https?://.*\.ngrok-free\.(app|dev)|https?://.*\.ngrok\.io|http://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def _global_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception: %s", exc)
    origin = request.headers.get("origin") or "*"
    headers = {
        "Access-Control-Allow-Origin": origin,
        "Access-Control-Allow-Credentials": "true",
        "Access-Control-Allow-Methods": "*",
        "Access-Control-Allow-Headers": "*",
    }
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error_code": "INTERNAL_ERROR",
            "message": str(exc) if str(exc) else "An internal server error occurred during processing.",
            "details": [],
        },
        headers=headers,
    )


app.include_router(auth.router, prefix="/api/auth")
app.include_router(health.router, prefix="/api", tags=["Health"])
app.include_router(health.router, tags=["Health"])
app.include_router(config.router, prefix="/api", tags=["Configuration"])
app.include_router(results.router, prefix="/api/results", tags=["Results & Upload"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["Analysis"])
app.include_router(correlation.router, prefix="/api/analysis", tags=["Correlation"])
app.include_router(historical.router, prefix="/api/analysis", tags=["Historical"])
app.include_router(interventions.router, prefix="/api/analysis", tags=["Interventions"])
app.include_router(reports.router, prefix="/api/reports", tags=["Reports"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(admin_routes.router, prefix="/api/admin", tags=["Administration"])


@app.get("/", tags=["System"])
def root():
    return {
        "agent": "Result Analysis Agent",
        "agent_id": 34,
        "status": "running",
        "docs": "/docs",
        "health": "/health",
    }
