from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints import router
from app.db.session import engine, Base
from app.core.config import settings
import logging
import os
import re

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
    description="API corporativa para detecção de fraudes em mensagens SMS",
    version="1.0.0"
)

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
logger.info("CORS configured for %s", origins)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def on_startup():
    logger.info("Starting up application")
    logger.info("Config: CLASSIFICATION_URL=%s", settings.CLASSIFICATION_URL)
    logger.info("Config: DATABASE_URL=%s", _mask_db_url(settings.DATABASE_URL))
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
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "services": {
            "database": "connected",
            "classification_service": "available"
        }
    }
