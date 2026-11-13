from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.budget import BudgetProfile, StakeDecision
from app.models.user import User
from app.schemas.budget import BudgetDashboard, BudgetProfileOut, BudgetUpdate, StakeCreate, StakeOut

router = APIRouter(prefix="/budget", tags=["budget"])

NOTICE_FR = (
    "Outil de suivi responsable uniquement. BETPREDICT AI n'accepte aucune mise et ne conserve aucun fonds. "
    "Aucune stratégie de récupération automatique des pertes n'est proposée."
)
NOTICE_EN = (
    "Responsible tracking tool only. BETPREDICT AI never accepts stakes or holds player funds. "
    "No automatic loss-recovery strategy is offered."
)


async def _get_profile(user: User, db: AsyncSession) -> BudgetProfile:
    result = await db.execute(
        select(BudgetProfile)
        .options(selectinload(BudgetProfile.decisions))
        .where(BudgetProfile.user_id == user.id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        profile = BudgetProfile(user_id=user.id)
        db.add(profile)
        await db.flush()
    return profile


def _profile_out(p: BudgetProfile) -> BudgetProfileOut:
    roi = 0.0 if p.total_staked <= 0 else (p.total_returned - p.total_staked) / p.total_staked
    return BudgetProfileOut(
        id=p.id,
        currency=p.currency,
        max_budget=p.max_budget,
        daily_loss_limit=p.daily_loss_limit,
        weekly_loss_limit=p.weekly_loss_limit,
        monthly_loss_limit=p.monthly_loss_limit,
        total_staked=p.total_staked,
        total_returned=p.total_returned,
        roi=roi,
        notifications_enabled=p.notifications_enabled,
        alerts_muted=p.alerts_muted,
    )


def _loss_in_period(decisions: list[StakeDecision], start: date) -> float:
    loss = 0.0
    for d in decisions:
        if d.decision_date < start or d.result != "lost":
            continue
        loss += d.stake_amount
    return loss


@router.get("", response_model=BudgetDashboard)
async def get_budget(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    profile = await _get_profile(user, db)
    today = date.today()
    alerts = []
    daily_loss = _loss_in_period(profile.decisions, today)
    weekly_loss = _loss_in_period(profile.decisions, today - timedelta(days=7))
    monthly_loss = _loss_in_period(profile.decisions, today - timedelta(days=30))
    if daily_loss >= profile.daily_loss_limit:
        alerts.append("Daily loss limit reached")
    if weekly_loss >= profile.weekly_loss_limit:
        alerts.append("Weekly loss limit reached")
    if monthly_loss >= profile.monthly_loss_limit:
        alerts.append("Monthly loss limit reached")
    if profile.total_staked >= profile.max_budget:
        alerts.append("Maximum budget reached")
    return BudgetDashboard(
        profile=_profile_out(profile),
        decisions=[
            StakeOut(
                id=d.id,
                decision_date=d.decision_date,
                market=d.market,
                selection=d.selection,
                stake_amount=d.stake_amount,
                odds_decimal=d.odds_decimal,
                returned_amount=d.returned_amount,
                result=d.result,
                notes=d.notes,
            )
            for d in sorted(profile.decisions, key=lambda x: x.created_at, reverse=True)[:100]
        ],
        alerts=alerts if not profile.alerts_muted else [],
        responsible_gaming_notice_fr=NOTICE_FR,
        responsible_gaming_notice_en=NOTICE_EN,
    )


@router.put("", response_model=BudgetProfileOut)
async def update_budget(
    payload: BudgetUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    profile = await _get_profile(user, db)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)
    db.add(profile)
    await db.flush()
    return _profile_out(profile)


@router.post("/decisions", response_model=StakeOut)
async def add_decision(
    payload: StakeCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    profile = await _get_profile(user, db)
    today = date.today()
    daily_loss = _loss_in_period(profile.decisions, today)
    if profile.total_staked + payload.stake_amount > profile.max_budget:
        raise HTTPException(status_code=400, detail="Would exceed maximum budget")
    if daily_loss >= profile.daily_loss_limit:
        raise HTTPException(status_code=400, detail="Daily loss limit already reached")

    decision = StakeDecision(
        budget_profile_id=profile.id,
        fixture_id=payload.fixture_id,
        decision_date=today,
        market=payload.market,
        selection=payload.selection,
        stake_amount=payload.stake_amount,
        odds_decimal=payload.odds_decimal,
        notes=payload.notes,
        result="pending",
    )
    profile.total_staked += payload.stake_amount
    db.add(decision)
    db.add(profile)
    await db.flush()
    return StakeOut(
        id=decision.id,
        decision_date=decision.decision_date,
        market=decision.market,
        selection=decision.selection,
        stake_amount=decision.stake_amount,
        odds_decimal=decision.odds_decimal,
        returned_amount=decision.returned_amount,
        result=decision.result,
        notes=decision.notes,
    )


@router.post("/decisions/{decision_id}/settle", response_model=StakeOut)
async def settle_decision(
    decision_id: str,
    result: str,
    returned_amount: float = 0.0,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if result not in {"won", "lost", "void"}:
        raise HTTPException(status_code=400, detail="Invalid result")
    profile = await _get_profile(user, db)
    decision = next((d for d in profile.decisions if str(d.id) == decision_id), None)
    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")
    decision.result = result
    decision.returned_amount = returned_amount if result == "won" else (decision.stake_amount if result == "void" else 0.0)
    decision.settled_at = datetime.now(timezone.utc)
    profile.total_returned += decision.returned_amount or 0.0
    db.add(decision)
    db.add(profile)
    await db.flush()
    return StakeOut(
        id=decision.id,
        decision_date=decision.decision_date,
        market=decision.market,
        selection=decision.selection,
        stake_amount=decision.stake_amount,
        odds_decimal=decision.odds_decimal,
        returned_amount=decision.returned_amount,
        result=decision.result,
        notes=decision.notes,
    )
