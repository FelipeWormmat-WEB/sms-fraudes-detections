from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
from threading import Lock
from typing import Deque

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.types import ASGIApp


@dataclass
class _Bucket:
    hits: Deque[datetime]


class InMemoryRateLimiter:
    def __init__(self, limit: int, window_seconds: int = 60) -> None:
        self.limit = max(1, limit)
        self.window = timedelta(seconds=window_seconds)
        self._buckets: dict[str, _Bucket] = {}
        self._lock = Lock()

    def allow(self, key: str) -> bool:
        now = datetime.now(timezone.utc)
        cutoff = now - self.window

        with self._lock:
            bucket = self._buckets.setdefault(key, _Bucket(hits=deque()))
            while bucket.hits and bucket.hits[0] < cutoff:
                bucket.hits.popleft()

            if len(bucket.hits) >= self.limit:
                return False

            bucket.hits.append(now)
            return True


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: ASGIApp,
        default_limit: int,
        admin_limit: int,
    ) -> None:
        super().__init__(app)
        self.default_limiter = InMemoryRateLimiter(limit=default_limit)
        self.admin_limiter = InMemoryRateLimiter(limit=admin_limit)

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if path in {"/", "/health"}:
            return await call_next(request)

        limiter = self.admin_limiter if path.startswith("/admin/") else self.default_limiter
        identity = self._identity_from_request(request)
        key = f"{path}:{identity}"

        if not limiter.allow(key):
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Try again later."},
            )

        return await call_next(request)

    @staticmethod
    def _identity_from_request(request: Request) -> str:
        api_key = request.headers.get("X-API-Key")
        admin_key = request.headers.get("X-Admin-Key")
        if api_key:
            digest = hashlib.sha256(api_key.encode("utf-8")).hexdigest()
            return f"api:{digest}"
        if admin_key:
            digest = hashlib.sha256(admin_key.encode("utf-8")).hexdigest()
            return f"admin:{digest}"
        client_host = request.client.host if request.client else "unknown"
        return f"ip:{client_host}"
