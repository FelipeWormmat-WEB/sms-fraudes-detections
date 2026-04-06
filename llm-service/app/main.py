import logging
import os
import secrets

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from app.llm_model import generate_response

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("llm_service")

is_production = os.getenv("ENVIRONMENT", "development").strip().lower() in {"prod", "production"}

app = FastAPI(
    title="LLM Service",
    version="1.1.0",
    docs_url=None if is_production else "/docs",
    redoc_url=None if is_production else "/redoc",
    openapi_url=None if is_production else "/openapi.json",
)
INTERNAL_SERVICE_TOKEN = os.getenv("INTERNAL_SERVICE_TOKEN", "").strip()


class AnalysisRequest(BaseModel):
    text: str = Field(min_length=1, max_length=512)
    max_length: int = Field(default=16, ge=4, le=64)


class AnalysisResponse(BaseModel):
    analysis: str
    status: str


def verify_internal_service_token(x_internal_service_token: str | None) -> None:
    if not INTERNAL_SERVICE_TOKEN:
        raise HTTPException(status_code=503, detail="Internal service token not configured")
    if not x_internal_service_token or not secrets.compare_digest(
        x_internal_service_token, INTERNAL_SERVICE_TOKEN
    ):
        raise HTTPException(status_code=401, detail="Unauthorized internal request")


@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Cache-Control"] = "no-store"
    response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'; base-uri 'none'"
    return response


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_text(
    request: AnalysisRequest,
    x_internal_service_token: str | None = Header(default=None, alias="X-Internal-Service-Token"),
):
    verify_internal_service_token(x_internal_service_token)
    logger.info("Analyzing text len=%d", len(request.text))
    analysis = generate_response(request.text, request.max_length)
    status = "success" if analysis in {"spam", "ham"} else "error"
    return AnalysisResponse(analysis=analysis, status=status)


@app.get("/")
async def root():
    return {"message": "LLM service is running"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
