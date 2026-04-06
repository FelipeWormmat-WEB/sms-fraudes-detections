import logging
import os
import re

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.api.endpoints import router
from app.core.config import settings
from app.core.rate_limit import RateLimitMiddleware
from app.db.session import Base, engine

logger = logging.getLogger("gateway.app")
if not logger.handlers:
    level = os.getenv("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
logger.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())


def _mask_db_url(url: str) -> str:
    if not url:
        return "undefined"
    return re.sub(r":([^:@/]+)@", r":***@", url)


app = FastAPI(
    title="SMS Fraud Detection API",
    description="Corporate API for SMS fraud detection",
    version="1.0.0",
    docs_url=None if settings.is_production else "/docs",
    redoc_url=None if settings.is_production else "/redoc",
    openapi_url=None if settings.is_production else "/openapi.json",
)

origins = settings.cors_origin_list

logger.info("CORS configured for %s", origins)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-API-Key", "X-Admin-Key"],
)
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.allowed_host_list,
)
app.add_middleware(
    RateLimitMiddleware,
    default_limit=settings.GATEWAY_RATE_LIMIT_PER_MINUTE,
    admin_limit=settings.GATEWAY_ADMIN_RATE_LIMIT_PER_MINUTE,
)


@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'; base-uri 'none'"
    response.headers["Cache-Control"] = "no-store"
    if settings.is_production:
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"
    return response


@app.on_event("startup")
async def on_startup():
    security_issues = settings.validate_runtime_security()
    if security_issues:
        for issue in security_issues:
            logger.error("Security configuration error: %s", issue)
        raise RuntimeError("Unsafe runtime configuration detected. Refusing to start.")

    logger.info("Starting up application")
    logger.info("Config: ENVIRONMENT=%s", settings.ENVIRONMENT)
    logger.info("Config: CLASSIFICATION_URL=%s", settings.CLASSIFICATION_URL)
    logger.info("Config: DATABASE_URL=%s", _mask_db_url(settings.DATABASE_URL))
    logger.info("Config: ENFORCE_API_KEY=%s", settings.ENFORCE_API_KEY)
    async with engine.begin() as conn:
        logger.info("Ensuring database tables exist")
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables ensured")


logger.info("Including API router")
app.include_router(router)
logger.info("Application ready to serve requests")


@app.get("/")
async def root():
    return {
        "message": "SMS Fraud Detection API",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "services": {
            "database": "connected",
            "classification_service": "available",
        },
    }
