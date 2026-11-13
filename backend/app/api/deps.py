"""FastAPI dependencies: auth, RBAC, rate-ish limits, analysis quotas."""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.core.security import safe_decode_token
from app.db.session import get_db
from app.models.user import SubscriptionPlan, User, UserRole

bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    if not creds:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    payload = safe_decode_token(creds.credentials)
    if not payload or payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user_id = payload.get("sub")
    try:
        uid = UUID(user_id)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid subject") from exc
    result = await db.execute(
        select(User).options(selectinload(User.subscription)).where(User.id == uid)
    )
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User inactive or missing")
    if user.self_excluded_until and user.self_excluded_until > datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account self-excluded")
    if user.pause_until and user.pause_until > datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account paused")
    return user


async def get_optional_user(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(bearer),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    if not creds:
        return None
    try:
        return await get_current_user(creds, db)
    except HTTPException:
        return None


def require_roles(*roles: UserRole):
    async def _checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles and user.role != UserRole.ADMIN:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
        return user

    return _checker


def user_plan(user: User) -> SubscriptionPlan:
    if user.subscription and user.subscription.status == "active":
        return user.subscription.plan
    if user.role == UserRole.PRO:
        return SubscriptionPlan.PRO
    if user.role == UserRole.PREMIUM:
        return SubscriptionPlan.PREMIUM
    return SubscriptionPlan.FREE


async def enforce_analysis_quota(user: User, db: AsyncSession) -> None:
    settings = get_settings()
    plan = user_plan(user)
    limits = {
        SubscriptionPlan.FREE: settings.free_daily_analyses,
        SubscriptionPlan.PREMIUM: settings.premium_daily_analyses,
        SubscriptionPlan.PRO: settings.pro_daily_analyses,
    }
    limit = limits.get(plan, settings.free_daily_analyses)
    today = date.today()
    if user.daily_analysis_reset != today:
        user.daily_analysis_count = 0
        user.daily_analysis_reset = today
    if user.daily_analysis_count >= limit:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Daily analysis limit reached for plan {plan.value}",
        )
    user.daily_analysis_count += 1
    db.add(user)


class RateLimitMiddleware:
    """Simple in-memory IP rate limiter for MVP."""

    def __init__(self, app, limit: int = 120, window: int = 60):
        self.app = app
        self.limit = limit
        self.window = window
        self.hits: dict[str, list[float]] = {}

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        request = Request(scope, receive)
        ip = request.client.host if request.client else "unknown"
        now = datetime.now(timezone.utc).timestamp()
        bucket = [t for t in self.hits.get(ip, []) if now - t < self.window]
        if len(bucket) >= self.limit:
            await send(
                {
                    "type": "http.response.start",
                    "status": 429,
                    "headers": [(b"content-type", b"application/json")],
                }
            )
            await send({"type": "http.response.body", "body": b'{"detail":"Rate limit exceeded"}'})
            return
        bucket.append(now)
        self.hits[ip] = bucket
        await self.app(scope, receive, send)
