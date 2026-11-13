from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.notification import NotificationLog, NotificationPreference
from app.models.user import User

router = APIRouter(prefix="/notifications", tags=["notifications"])


class PrefUpdate(BaseModel):
    push_enabled: bool | None = None
    email_enabled: bool | None = None
    telegram_enabled: bool | None = None
    whatsapp_enabled: bool | None = None
    telegram_chat_id: str | None = None
    whatsapp_number: str | None = None
    new_analysis: bool | None = None
    lineup_changes: bool | None = None
    injuries: bool | None = None
    probability_shifts: bool | None = None
    match_results: bool | None = None
    consent_telegram: bool | None = None
    consent_whatsapp: bool | None = None


@router.get("/preferences")
async def get_prefs(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    pref = (
        await db.execute(select(NotificationPreference).where(NotificationPreference.user_id == user.id))
    ).scalar_one_or_none()
    if not pref:
        pref = NotificationPreference(user_id=user.id)
        db.add(pref)
        await db.flush()
    return {
        "push_enabled": pref.push_enabled,
        "email_enabled": pref.email_enabled,
        "telegram_enabled": pref.telegram_enabled and pref.consent_telegram,
        "whatsapp_enabled": pref.whatsapp_enabled and pref.consent_whatsapp,
        "new_analysis": pref.new_analysis,
        "lineup_changes": pref.lineup_changes,
        "injuries": pref.injuries,
        "probability_shifts": pref.probability_shifts,
        "match_results": pref.match_results,
        "consent_telegram": pref.consent_telegram,
        "consent_whatsapp": pref.consent_whatsapp,
        "notice": "WhatsApp Business and Telegram require explicit consent.",
    }


@router.put("/preferences")
async def update_prefs(
    payload: PrefUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    pref = (
        await db.execute(select(NotificationPreference).where(NotificationPreference.user_id == user.id))
    ).scalar_one_or_none()
    if not pref:
        pref = NotificationPreference(user_id=user.id)
        db.add(pref)
    data = payload.model_dump(exclude_unset=True)
    if data.get("telegram_enabled") and not data.get("consent_telegram", pref.consent_telegram):
        data["telegram_enabled"] = False
    if data.get("whatsapp_enabled") and not data.get("consent_whatsapp", pref.consent_whatsapp):
        data["whatsapp_enabled"] = False
    for k, v in data.items():
        setattr(pref, k, v)
    db.add(pref)
    await db.flush()
    return {"status": "updated"}


@router.get("/logs")
async def logs(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    rows = (
        await db.execute(
            select(NotificationLog)
            .where(NotificationLog.user_id == user.id)
            .order_by(NotificationLog.created_at.desc())
            .limit(50)
        )
    ).scalars().all()
    return [
        {
            "channel": r.channel,
            "event_type": r.event_type,
            "title": r.title,
            "body": r.body,
            "status": r.status,
            "sent_at": r.sent_at,
        }
        for r in rows
    ]
