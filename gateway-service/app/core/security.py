from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import secrets
from typing import Optional

from fastapi import Depends, Header, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.models import APIClient, APIUsageEvent
from app.db.session import get_db


def hash_api_key(api_key: str) -> str:
    return hashlib.sha256(api_key.encode("utf-8")).hexdigest()


def generate_api_key() -> str:
    return f"sms_{secrets.token_urlsafe(32)}"


def get_current_month_window() -> tuple[datetime, datetime]:
    now = datetime.now(timezone.utc)
    start = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
    if now.month == 12:
        end = datetime(now.year + 1, 1, 1, tzinfo=timezone.utc)
    else:
        end = datetime(now.year, now.month + 1, 1, tzinfo=timezone.utc)
    return start, end


async def count_monthly_usage(db: AsyncSession, client_id: int) -> int:
    start, end = get_current_month_window()
    result = await db.execute(
        select(func.count(APIUsageEvent.id)).where(
            APIUsageEvent.client_id == client_id,
            APIUsageEvent.created_at >= start,
            APIUsageEvent.created_at < end,
            APIUsageEvent.status == "success",
        )
    )
    return int(result.scalar() or 0)


@dataclass
class AuthContext:
    client: Optional[APIClient]
    enforce: bool


async def get_auth_context(
    x_api_key: Optional[str] = Header(default=None, alias="X-API-Key"),
    db: AsyncSession = Depends(get_db),
) -> AuthContext:
    if not x_api_key:
        if settings.ENFORCE_API_KEY:
            raise HTTPException(status_code=401, detail="X-API-Key header is required")
        return AuthContext(client=None, enforce=settings.ENFORCE_API_KEY)

    key_hash = hash_api_key(x_api_key)
    result = await db.execute(select(APIClient).where(APIClient.api_key_hash == key_hash))
    client = result.scalar_one_or_none()

    if client is None or not client.is_active:
        raise HTTPException(status_code=401, detail="Invalid or inactive API key")

    usage = await count_monthly_usage(db, client.id)
    if usage >= client.monthly_quota:
        raise HTTPException(
            status_code=429,
            detail=(
                f"Monthly quota exceeded ({usage}/{client.monthly_quota}). "
                "Upgrade your plan or wait until next month."
            ),
        )

    return AuthContext(client=client, enforce=settings.ENFORCE_API_KEY)


async def require_admin_key(
    x_admin_key: Optional[str] = Header(default=None, alias="X-Admin-Key"),
) -> None:
    if not settings.ADMIN_API_KEY:
        raise HTTPException(status_code=500, detail="ADMIN_API_KEY is not configured")
    if not x_admin_key or not secrets.compare_digest(x_admin_key, settings.ADMIN_API_KEY):
        raise HTTPException(status_code=403, detail="Invalid admin key")


async def record_usage_event(
    db: AsyncSession,
    endpoint: str,
    status: str = "success",
    client: Optional[APIClient] = None,
) -> None:
    if client is None:
        return

    db.add(
        APIUsageEvent(
            client_id=client.id,
            endpoint=endpoint,
            status=status,
        )
    )
