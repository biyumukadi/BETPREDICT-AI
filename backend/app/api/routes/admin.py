from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_roles
from app.core.config import get_settings
from app.db.session import get_db
from app.models.admin import Announcement, AuditLog, DataSourceConfig
from app.models.prediction import Prediction, PredictionEvaluation
from app.models.sport import Fixture
from app.models.user import User, UserRole
from app.services.sync import generate_predictions_for_upcoming, sync_catalog, sync_fixtures

router = APIRouter(prefix="/admin", tags=["admin"])


class AnnouncementIn(BaseModel):
    title_fr: str
    title_en: str
    body_fr: str
    body_en: str
    publish: bool = False


@router.get("/overview")
async def overview(
    admin: User = Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    settings = get_settings()
    users = (await db.execute(select(func.count()).select_from(User))).scalar() or 0
    fixtures = (await db.execute(select(func.count()).select_from(Fixture))).scalar() or 0
    preds = (await db.execute(select(func.count()).select_from(Prediction))).scalar() or 0
    evals = (await db.execute(select(func.count()).select_from(PredictionEvaluation))).scalar() or 0
    return {
        "demo_mode": settings.is_demo,
        "users": users,
        "fixtures": fixtures,
        "predictions": preds,
        "evaluations": evals,
        "model_version": "ensemble-v1.0.0",
        "primary_provider": settings.primary_data_provider,
    }


@router.get("/users")
async def list_users(
    admin: User = Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    users = (await db.execute(select(User).order_by(User.created_at.desc()).limit(200))).scalars().all()
    return [
        {
            "id": str(u.id),
            "email": u.email,
            "full_name": u.full_name,
            "role": u.role.value,
            "is_active": u.is_active,
            "mfa_enabled": u.mfa_enabled,
        }
        for u in users
    ]


class RoleUpdate(BaseModel):
    email: EmailStr
    role: UserRole


@router.post("/users/role")
async def set_role(
    payload: RoleUpdate,
    admin: User = Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    user = (await db.execute(select(User).where(User.email == payload.email.lower()))).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.role = payload.role
    if payload.role == UserRole.ADMIN:
        user.mfa_enabled = True
        if not user.mfa_secret:
            user.mfa_secret = "000000"  # replace with TOTP secret provisioning
    db.add(user)
    db.add(
        AuditLog(
            actor_id=admin.id,
            action="set_role",
            resource="user",
            detail={"email": payload.email, "role": payload.role.value},
        )
    )
    await db.flush()
    return {"status": "updated"}


@router.post("/sync")
async def run_sync(
    admin: User = Depends(require_roles(UserRole.ADMIN, UserRole.ANALYST)),
    db: AsyncSession = Depends(get_db),
):
    catalog = await sync_catalog(db)
    fixtures = await sync_fixtures(db)
    preds = await generate_predictions_for_upcoming(db)
    db.add(
        AuditLog(
            actor_id=admin.id,
            action="sync",
            resource="data",
            detail={**catalog, **fixtures, **preds},
        )
    )
    return {**catalog, **fixtures, **preds}


@router.get("/data-sources")
async def data_sources(
    admin: User = Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    rows = (await db.execute(select(DataSourceConfig))).scalars().all()
    return [
        {
            "name": r.name,
            "provider_key": r.provider_key,
            "is_enabled": r.is_enabled,
            "is_licensed": r.is_licensed,
            "last_sync_at": r.last_sync_at,
            "last_error": r.last_error,
        }
        for r in rows
    ]


@router.post("/announcements")
async def create_announcement(
    payload: AnnouncementIn,
    admin: User = Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    row = Announcement(
        title_fr=payload.title_fr,
        title_en=payload.title_en,
        body_fr=payload.body_fr,
        body_en=payload.body_en,
        is_published=payload.publish,
        published_at=datetime.now(timezone.utc) if payload.publish else None,
        author_id=admin.id,
    )
    db.add(row)
    await db.flush()
    return {"id": str(row.id), "published": row.is_published}


@router.get("/audit-logs")
async def audit_logs(
    admin: User = Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    rows = (await db.execute(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(100))).scalars().all()
    return [
        {
            "action": r.action,
            "resource": r.resource,
            "detail": r.detail,
            "created_at": r.created_at,
            "actor_id": str(r.actor_id) if r.actor_id else None,
        }
        for r in rows
    ]
