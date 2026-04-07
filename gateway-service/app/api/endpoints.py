from datetime import datetime, timezone
import logging
import os
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score

from app.api.schemas import (
    CreateClientRequest,
    CreateClientResponse,
    SMSLogResponse,
    SMSRequest,
    SMSResponse,
    UsageSummaryResponse,
)
from app.core.config import settings
from app.core.security import (
    AuthContext,
    count_monthly_usage,
    generate_api_key,
    get_auth_context,
    hash_api_key,
    record_usage_event,
    require_admin_key,
)
from app.db.models import APIClient, SMSLog
from app.db.session import get_db
from app.services.classification import classify_message, hybrid_classification, normalize_prediction

logger = logging.getLogger("gateway.api")
if not logger.handlers:
    level = os.getenv("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
logger.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())

router = APIRouter()


def _client_id(auth: AuthContext) -> int | None:
    return auth.client.id if auth.client else None


def _log_filters(auth: AuthContext) -> list:
    filters = []
    if auth.client is not None:
        filters.append(SMSLog.client_id == auth.client.id)
    return filters


def _normalize_ground_truth(value: str | None) -> str | None:
    if not value:
        return None
    normalized = normalize_prediction(value)
    return normalized if normalized in {"spam", "ham"} else None


def _safe_float(value: object, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


@router.post("/admin/clients", response_model=CreateClientResponse, dependencies=[Depends(require_admin_key)])
async def create_client(payload: CreateClientRequest, db: AsyncSession = Depends(get_db)):
    try:
        plain_key = generate_api_key()
        client = APIClient(
            name=payload.name.strip(),
            plan=payload.plan.strip().lower(),
            monthly_quota=max(1, payload.monthly_quota),
            api_key_hash=hash_api_key(plain_key),
            is_active=True,
        )
        db.add(client)
        await db.commit()
        await db.refresh(client)

        return CreateClientResponse(
            client_id=client.id,
            name=client.name,
            plan=client.plan,
            monthly_quota=client.monthly_quota,
            api_key=plain_key,
            created_at=client.created_at,
        )
    except Exception as exc:
        logger.exception("Error creating API client: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to create API client")


@router.get(
    "/admin/clients/{client_id}/usage",
    response_model=UsageSummaryResponse,
    dependencies=[Depends(require_admin_key)],
)
async def get_client_usage(client_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(APIClient).where(APIClient.id == client_id))
    client = result.scalar_one_or_none()
    if client is None:
        raise HTTPException(status_code=404, detail="Client not found")

    used = await count_monthly_usage(db, client.id)
    remaining = max(client.monthly_quota - used, 0)
    current_month = datetime.now(timezone.utc).strftime("%Y-%m")

    return UsageSummaryResponse(
        client_id=client.id,
        month=current_month,
        used=used,
        quota=client.monthly_quota,
        remaining=remaining,
    )


@router.post("/analyze", response_model=SMSResponse)
async def analyze_sms(
    request: SMSRequest,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    try:
        classification_data = await classify_message(request.message)
        prediction = normalize_prediction(classification_data.get("prediction"))
        confidence = _safe_float(classification_data.get("confidence"), 0.0)
        source = classification_data.get("source", "unknown")

        log_item = SMSLog(
            client_id=_client_id(auth),
            message=request.message,
            prediction=prediction,
            confidence=confidence,
            source=source,
            ground_truth=_normalize_ground_truth(request.ground_truth),
        )
        db.add(log_item)
        await record_usage_event(db, endpoint="/analyze", status="success", client=auth.client)
        await db.commit()

        return SMSResponse(
            message=request.message,
            prediction=prediction,
            confidence=confidence,
            source=source,
            status="success",
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Error in /analyze: %s", exc)
        raise HTTPException(status_code=500, detail="Analyze request failed")


@router.post("/analyze_llm", response_model=SMSResponse)
async def analyze_message_llm(
    payload: SMSRequest,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    try:
        baseline = await classify_message(payload.message)
        confidence = _safe_float(baseline.get("confidence"), 0.0)
        prediction = normalize_prediction(baseline.get("prediction"))

        hybrid_result = await hybrid_classification(payload.message, confidence, prediction)
        final_prediction = normalize_prediction(hybrid_result.get("prediction"))
        source = hybrid_result.get("source", "unknown")

        db.add(
            SMSLog(
                client_id=_client_id(auth),
                message=payload.message,
                prediction=final_prediction,
                confidence=confidence,
                source=source,
                ground_truth=_normalize_ground_truth(payload.ground_truth),
            )
        )
        await record_usage_event(db, endpoint="/analyze_llm", status="success", client=auth.client)
        await db.commit()

        return SMSResponse(
            message=payload.message,
            prediction=final_prediction,
            confidence=confidence,
            source=source,
            status="success",
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Error in /analyze_llm: %s", exc)
        raise HTTPException(status_code=500, detail="Analyze LLM request failed")


@router.post("/analyze_hybrid", response_model=SMSResponse)
async def analyze_message_hybrid(
    payload: SMSRequest,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    try:
        hybrid_result = await hybrid_classification(payload.message)
        prediction = normalize_prediction(hybrid_result.get("prediction"))
        confidence = _safe_float(hybrid_result.get("base_confidence"), 0.0)
        source = hybrid_result.get("source", "unknown")

        db.add(
            SMSLog(
                client_id=_client_id(auth),
                message=payload.message,
                prediction=prediction,
                confidence=confidence,
                source=source,
                ground_truth=_normalize_ground_truth(payload.ground_truth),
            )
        )
        await record_usage_event(db, endpoint="/analyze_hybrid", status="success", client=auth.client)
        await db.commit()

        return SMSResponse(
            message=payload.message,
            prediction=prediction,
            confidence=confidence,
            source=source,
            status="success",
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Error in /analyze_hybrid: %s", exc)
        raise HTTPException(status_code=500, detail="Hybrid analyze request failed")


@router.get("/health")
async def health_check():
    return {"status": "healthy"}


@router.get("/logs", response_model=List[SMSLogResponse])
async def get_logs(
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    if auth.client is None:
        raise HTTPException(status_code=401, detail="An API key is required to access logs")
    query = select(SMSLog).order_by(SMSLog.created_at.desc()).limit(500)
    if auth.client is not None:
        query = query.where(SMSLog.client_id == auth.client.id)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/metrics")
async def get_metrics(
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    if auth.client is None:
        raise HTTPException(status_code=401, detail="An API key is required to access metrics")
    filters = _log_filters(auth)
    summary_query = select(
        func.count(SMSLog.id),
        func.coalesce(func.sum(case((SMSLog.prediction == "spam", 1), else_=0)), 0),
        func.coalesce(func.sum(case((SMSLog.prediction == "ham", 1), else_=0)), 0),
        func.coalesce(
            func.sum(case((func.lower(func.coalesce(SMSLog.source, "")).like("%llm%"), 1), else_=0)),
            0,
        ),
        func.coalesce(func.avg(SMSLog.confidence), 0.0),
    ).where(*filters)
    total_messages, spam_count, ham_count, llm_count, avg_confidence = (await db.execute(summary_query)).one()

    if total_messages == 0:
        return {
            "accuracy": 0.0,
            "precision": 0.0,
            "recall": 0.0,
            "f1_score": 0.0,
            "train_size": 0,
            "test_size": 0,
            "total_messages": 0,
            "spam_count": 0,
            "ham_count": 0,
            "llm_count": 0,
            "avg_confidence": 0.0,
            "message": "No logs available for metrics",
        }

    labeled_filters = [
        *filters,
        SMSLog.prediction.in_(("spam", "ham")),
        SMSLog.ground_truth.in_(("spam", "ham")),
    ]
    labeled_count_query = select(func.count(SMSLog.id)).where(*labeled_filters)
    labeled_message_total = (await db.execute(labeled_count_query)).scalar_one()

    if labeled_message_total == 0:
        return {
            "accuracy": 0.0,
            "precision": 0.0,
            "recall": 0.0,
            "f1_score": 0.0,
            "train_size": 0,
            "test_size": 0,
            "total_messages": int(total_messages),
            "spam_count": spam_count,
            "ham_count": ham_count,
            "llm_count": llm_count,
            "avg_confidence": float(avg_confidence),
            "message": "No ground-truth labels found. Send ground_truth in analyze requests.",
        }

    labeled_logs_query = (
        select(SMSLog.prediction, SMSLog.ground_truth)
        .where(*labeled_filters)
        .order_by(SMSLog.created_at.desc())
        .limit(settings.METRICS_MAX_LABELED_MESSAGES)
    )
    labeled_logs = (await db.execute(labeled_logs_query)).all()
    y_true = [str(log.ground_truth) for log in labeled_logs]
    y_pred = [str(log.prediction) for log in labeled_logs]

    accuracy = accuracy_score(y_true, y_pred)
    precision = precision_score(y_true, y_pred, pos_label="spam", zero_division=0)
    recall = recall_score(y_true, y_pred, pos_label="spam", zero_division=0)
    f1 = f1_score(y_true, y_pred, pos_label="spam", zero_division=0)
    metrics_are_sampled = labeled_message_total > len(labeled_logs)
    metrics_message = "Metrics computed from labeled production logs"
    if metrics_are_sampled:
        metrics_message = (
            f"Metrics computed from the most recent {len(labeled_logs)} labeled production logs"
        )

    return {
        "accuracy": float(accuracy),
        "precision": float(precision),
        "recall": float(recall),
        "f1_score": float(f1),
        "train_size": len(labeled_logs),
        "test_size": len(labeled_logs),
        "total_messages": int(total_messages),
        "spam_count": spam_count,
        "ham_count": ham_count,
        "llm_count": llm_count,
        "avg_confidence": float(avg_confidence),
        "labeled_messages_total": int(labeled_message_total),
        "metrics_sample_limited": metrics_are_sampled,
        "message": metrics_message,
    }
