import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from redis import Redis
from redis.exceptions import RedisError
from slowapi.errors import RateLimitExceeded
from slowapi.extension import _rate_limit_exceeded_handler
from slowapi.middleware import SlowAPIMiddleware
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.api import router
from app.billing_api import router as billing_router
from app.config import get_settings
from app.database import engine
from app.documents_contracts_api import router as documents_contracts_router
from app.identity_api import router as identity_router
from app.owks_api import router as owks_router
from app.owks_scheduler import run_monitoring_scheduler
from app.personnel_api import router as personnel_router
from app.rate_limit import limiter
from app.scheduling_api import router as scheduling_router
from app.time_tracking_api import router as time_tracking_router
from app.time_tracking_surcharges import router as time_tracking_surcharges_router

settings = get_settings()
logger = logging.getLogger(__name__)
rate_limit_store = (
    Redis.from_url(settings.rate_limit_storage_uri)
    if settings.rate_limit_storage_uri.startswith(("redis://", "rediss://"))
    else None
)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    stop_monitor = asyncio.Event()
    monitor_task = asyncio.create_task(run_monitoring_scheduler(stop_monitor))
    try:
        yield
    finally:
        stop_monitor.set()
        await monitor_task


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-CSRF-Token"],
)
app.include_router(router, prefix=settings.api_prefix)
app.include_router(personnel_router, prefix=settings.api_prefix)
app.include_router(scheduling_router, prefix=settings.api_prefix)
app.include_router(time_tracking_router, prefix=settings.api_prefix)
app.include_router(time_tracking_surcharges_router, prefix=settings.api_prefix)
app.include_router(documents_contracts_router, prefix=settings.api_prefix)
app.include_router(billing_router, prefix=settings.api_prefix)
app.include_router(identity_router, prefix=settings.api_prefix)
app.include_router(owks_router, prefix=settings.api_prefix)


@app.get("/health/live", tags=["System"])
def liveness() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/ready", tags=["System"])
def readiness() -> dict[str, str]:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        logger.exception("Datenbankverbindung für Readiness-Prüfung fehlgeschlagen")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Datenbankverbindung nicht verfügbar",
        ) from exc
    if rate_limit_store is not None:
        try:
            rate_limit_store.ping()
        except RedisError as exc:
            logger.exception("Rate-Limit-Speicher für Readiness-Prüfung fehlgeschlagen")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Rate-Limit-Speicher nicht verfügbar",
            ) from exc
    return {"status": "ready"}
