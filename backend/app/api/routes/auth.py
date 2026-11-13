from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user, user_plan
from app.core.config import get_settings
from app.core.security import create_access_token, create_refresh_token, hash_password, safe_decode_token, verify_password
from app.db.session import get_db
from app.models.budget import BudgetProfile
from app.models.notification import NotificationPreference
from app.models.user import Subscription, SubscriptionPlan, User, UserRole
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse)
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)):
    settings = get_settings()
    existing = (await db.execute(select(User).where(User.email == payload.email.lower()))).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    today = date.today()
    age = today.year - payload.date_of_birth.year - (
        (today.month, today.day) < (payload.date_of_birth.month, payload.date_of_birth.day)
    )
    if age < settings.legal_age_minimum:
        raise HTTPException(status_code=403, detail="Legal age verification failed")

    user = User(
        email=payload.email.lower(),
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        date_of_birth=payload.date_of_birth,
        age_verified=True,
        locale=payload.locale,
        role=UserRole.USER,
        is_verified=True,
    )
    db.add(user)
    await db.flush()
    db.add(Subscription(user_id=user.id, plan=SubscriptionPlan.FREE, status="active"))
    db.add(BudgetProfile(user_id=user.id))
    db.add(NotificationPreference(user_id=user.id))
    await db.flush()
    return TokenResponse(
        access_token=create_access_token(str(user.id), {"role": user.role.value}),
        refresh_token=create_refresh_token(str(user.id)),
    )


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = (await db.execute(select(User).where(User.email == payload.email.lower()))).scalar_one_or_none()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if user.mfa_enabled and user.role == UserRole.ADMIN:
        if not payload.mfa_code or payload.mfa_code != (user.mfa_secret or "000000"):
            # MVP: static MFA secret comparison; replace with TOTP in production
            raise HTTPException(status_code=401, detail="MFA code required for administrators")
    return TokenResponse(
        access_token=create_access_token(str(user.id), {"role": user.role.value}),
        refresh_token=create_refresh_token(str(user.id)),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(refresh_token: str, db: AsyncSession = Depends(get_db)):
    payload = safe_decode_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    user = (await db.execute(select(User).where(User.id == payload["sub"]))).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return TokenResponse(
        access_token=create_access_token(str(user.id), {"role": user.role.value}),
        refresh_token=create_refresh_token(str(user.id)),
    )


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user)):
    settings = get_settings()
    return UserOut(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role.value,
        locale=user.locale,
        plan=user_plan(user).value,
        age_verified=user.age_verified,
        mfa_enabled=user.mfa_enabled,
        is_demo_banner=settings.is_demo,
    )


@router.post("/pause")
async def pause_account(days: int = 7, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if days < 1 or days > 365:
        raise HTTPException(status_code=400, detail="Pause period must be 1-365 days")
    user.pause_until = datetime.now(timezone.utc) + timedelta(days=days)
    db.add(user)
    return {"status": "paused", "until": user.pause_until}


@router.post("/self-exclude")
async def self_exclude(days: int = 180, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if days < 30:
        raise HTTPException(status_code=400, detail="Self-exclusion minimum is 30 days")
    user.self_excluded_until = datetime.now(timezone.utc) + timedelta(days=days)
    db.add(user)
    return {"status": "self_excluded", "until": user.self_excluded_until, "notice": "No loss-recovery tools are offered."}
