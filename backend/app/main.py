"""
Rotax 914-inspired Aero-Piston Engine Digital Twin Backend.
FastAPI Application Entry Point.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.settings import settings
from app.config.constants import SYSTEM_DISCLAIMER
from app.utils.logging import logger
from app.api.health_routes import router as health_router
from app.api.inference_routes import router as inference_router
from app.api.prediction_routes import router as prediction_router
from app.api.telemetry_routes import router as telemetry_router
from app.api.websocket_routes import router as websocket_router
from app.models.database import init_db
from app.services.live_inference_service import live_inference_service

# Ensure the SQLite fallback and all required tables exist before requests are handled,
# even when tests create the app without entering an async lifespan context.
init_db()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle events for FastAPI application."""
    logger.info("=" * 70)
    logger.info("Starting %s v%s", settings.APP_NAME, settings.APP_VERSION)
    logger.info("Environment: %s | Debug: %s", settings.ENVIRONMENT, settings.DEBUG)
    logger.info("Disclaimer: %s", SYSTEM_DISCLAIMER)
    logger.info("Swagger Docs available at http://%s:%s/docs", settings.HOST, settings.PORT)
    logger.info("=" * 70)
    # Initialize database tables
    try:
        init_db()
    except Exception as e:
        logger.warning("Database initialization error: %s", e)
    yield
    logger.info("Shutting down %s...", settings.APP_NAME)


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "AI-Enabled Physics-Informed Digital Twin for MALE UAV Aero-Piston Engine "
        "(Rotax 914-inspired Turbocharged Engine). Research & Engineering Prototype."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(health_router, prefix="/api")
app.include_router(inference_router, prefix="/api")
app.include_router(prediction_router, prefix="/api")
app.include_router(telemetry_router, prefix="/api")
app.include_router(websocket_router)


@app.get("/", summary="Root API Index", tags=["Root"])
async def root():
    """Root redirect / welcome information."""
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "docs_url": "/docs",
        "health_endpoint": "/api/health",
        "system_info": "/api/system/info",
        "disclaimer": SYSTEM_DISCLAIMER
    }
