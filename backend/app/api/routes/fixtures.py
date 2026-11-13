from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import enforce_analysis_quota, get_current_user, get_optional_user
from app.core.config import get_settings
from app.db.session import get_db
from app.models.odds import OddsSnapshot, ValueBet
from app.models.sport import Competition, Fixture, FixtureStatus, Injury, Team, TeamStats
from app.models.user import User
from app.schemas.fixtures import (
    CompetitionOut,
    DashboardOut,
    FixtureDetailOut,
    FixtureOut,
    MarketOut,
    PredictionOut,
    TeamBrief,
)
from app.services.odds.value import detect_value_bets

router = APIRouter(prefix="/fixtures", tags=["fixtures"])


def _team_brief(t: Team) -> TeamBrief:
    return TeamBrief(
        id=t.id,
        name=t.name,
        short_name=t.short_name,
        elo_rating=t.elo_rating,
        country=t.country,
    )


def _comp_out(c: Competition) -> CompetitionOut:
    return CompetitionOut(id=c.id, name=c.name, country=c.country, code=c.code, season=c.season)


def _pred_out(p) -> PredictionOut:
    return PredictionOut(
        id=p.id,
        model_version=p.model_version,
        published_at=p.published_at,
        is_demo=p.is_demo,
        home_win_prob=p.home_win_prob,
        draw_prob=p.draw_prob,
        away_win_prob=p.away_win_prob,
        confidence=p.confidence,
        expected_home_goals=p.expected_home_goals,
        expected_away_goals=p.expected_away_goals,
        most_likely_score=p.most_likely_score,
        most_likely_score_prob=p.most_likely_score_prob,
        explanation_fr=p.explanation_fr,
        explanation_en=p.explanation_en,
        key_factors=p.key_factors,
        uncertainties=p.uncertainties,
        model_breakdown=p.model_breakdown,
        markets=[
            MarketOut(
                market=m.market.value,
                selection=m.selection,
                probability=m.probability,
                confidence=m.confidence,
                recommended=m.recommended,
                odds_decimal=m.odds_decimal,
                expected_value=m.expected_value,
                rationale=m.rationale,
            )
            for m in (p.markets or [])
        ],
    )


def _fixture_out(f: Fixture) -> FixtureOut:
    pred = None
    if f.predictions:
        latest = sorted(f.predictions, key=lambda x: x.published_at, reverse=True)[0]
        pred = _pred_out(latest)
    return FixtureOut(
        id=f.id,
        kickoff_at=f.kickoff_at,
        status=f.status.value,
        venue=f.venue,
        matchday=f.matchday,
        is_demo=f.is_demo,
        home_score=f.home_score,
        away_score=f.away_score,
        home_xg=f.home_xg,
        away_xg=f.away_xg,
        competition=_comp_out(f.competition),
        home_team=_team_brief(f.home_team),
        away_team=_team_brief(f.away_team),
        prediction=pred,
    )


def _load_options():
    from app.models.prediction import Prediction

    return [
        selectinload(Fixture.competition),
        selectinload(Fixture.home_team),
        selectinload(Fixture.away_team),
        selectinload(Fixture.predictions).selectinload(Prediction.markets),
    ]


@router.get("/competitions/list", response_model=list[CompetitionOut])
async def list_competitions(db: AsyncSession = Depends(get_db)):
    comps = (await db.execute(select(Competition).where(Competition.is_active.is_(True)))).scalars().all()
    return [_comp_out(c) for c in comps]


@router.get("/dashboard", response_model=DashboardOut)
async def dashboard(
    competition_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
    user: Optional[User] = Depends(get_optional_user),
):
    settings = get_settings()
    now = datetime.now(timezone.utc)
    start_today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_today = start_today + timedelta(days=1)
    end_tomorrow = start_today + timedelta(days=2)
    end_week = start_today + timedelta(days=7)

    q = select(Fixture).options(*_load_options()).order_by(Fixture.kickoff_at.asc())
    if competition_id:
        q = q.where(Fixture.competition_id == competition_id)
    fixtures = (await db.execute(q)).scalars().unique().all()

    today, tomorrow, week, finished = [], [], [], []
    for f in fixtures:
        item = _fixture_out(f)
        if f.status == FixtureStatus.FINISHED and f.kickoff_at >= start_today - timedelta(days=3):
            finished.append(item)
        elif start_today <= f.kickoff_at < end_today:
            today.append(item)
        elif end_today <= f.kickoff_at < end_tomorrow:
            tomorrow.append(item)
        elif end_tomorrow <= f.kickoff_at < end_week:
            week.append(item)

    comps = (await db.execute(select(Competition).where(Competition.is_active.is_(True)))).scalars().all()
    return DashboardOut(
        demo_mode=settings.is_demo,
        disclaimer_fr=(
            "BETPREDICT AI fournit des analyses statistiques estimées. "
            "Aucune prédiction n'est certaine. Service d'information uniquement — aucune mise n'est acceptée."
            + (" MODE DÉMONSTRATION : données synthétiques clairement identifiées." if settings.is_demo else "")
        ),
        disclaimer_en=(
            "BETPREDICT AI provides estimated statistical analysis. "
            "No prediction is certain. Information-only service — no stakes are accepted."
            + (" DEMO MODE: synthetic data clearly labeled." if settings.is_demo else "")
        ),
        today=today,
        tomorrow=tomorrow,
        next_7_days=week,
        finished=finished,
        competitions=[_comp_out(c) for c in comps],
    )


@router.get("/search", response_model=list[FixtureOut])
async def search(
    q: str = Query(min_length=1),
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(Fixture)
        .join(Fixture.home_team)
        .join(Fixture.away_team, Fixture.away_team_id == Team.id)
        .join(Fixture.competition)
        .options(*_load_options())
        .where(
            or_(
                Team.name.ilike(f"%{q}%"),
                Competition.name.ilike(f"%{q}%"),
                Competition.country.ilike(f"%{q}%"),
            )
        )
        .order_by(Fixture.kickoff_at.asc())
        .limit(50)
    )
    # Note: join alias for away team name — simplified search via competition/home
    if date_from:
        query = query.where(Fixture.kickoff_at >= date_from)
    if date_to:
        query = query.where(Fixture.kickoff_at <= date_to)
    fixtures = (await db.execute(query)).scalars().unique().all()
    # Also search away team names
    away_q = (
        select(Fixture)
        .join(Team, Fixture.away_team_id == Team.id)
        .options(*_load_options())
        .where(Team.name.ilike(f"%{q}%"))
        .limit(50)
    )
    away_fixtures = (await db.execute(away_q)).scalars().unique().all()
    merged = {f.id: f for f in list(fixtures) + list(away_fixtures)}
    return [_fixture_out(f) for f in sorted(merged.values(), key=lambda x: x.kickoff_at)]


@router.get("/{fixture_id}", response_model=FixtureDetailOut)
async def fixture_detail(
    fixture_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: Optional[User] = Depends(get_optional_user),
):
    settings = get_settings()
    result = await db.execute(
        select(Fixture)
        .where(Fixture.id == fixture_id)
        .options(
            *_load_options(),
            selectinload(Fixture.home_team).selectinload(Team.stats),
            selectinload(Fixture.away_team).selectinload(Team.stats),
            selectinload(Fixture.home_team).selectinload(Team.injuries),
            selectinload(Fixture.away_team).selectinload(Team.injuries),
        )
    )
    fixture = result.scalar_one_or_none()
    if not fixture:
        raise HTTPException(status_code=404, detail="Fixture not found")

    if user:
        await enforce_analysis_quota(user, db)

    base = _fixture_out(fixture)
    odds_rows = (
        await db.execute(select(OddsSnapshot).where(OddsSnapshot.fixture_id == fixture.id).limit(50))
    ).scalars().all()
    odds = [
        {
            "bookmaker": o.bookmaker,
            "market": o.market,
            "selection": o.selection,
            "odds_decimal": o.odds_decimal,
            "implied_probability": o.implied_probability,
            "is_demo": o.is_demo,
            "source_licensed": o.source_licensed,
            "captured_at": o.captured_at.isoformat(),
        }
        for o in odds_rows
    ]

    value_bets = []
    if fixture.predictions:
        pred = sorted(fixture.predictions, key=lambda x: x.published_at, reverse=True)[0]
        model_probs = {"1": pred.home_win_prob, "X": pred.draw_prob, "2": pred.away_win_prob}
        by_book: dict[str, dict[str, float]] = {}
        for o in odds_rows:
            if o.market == "1x2":
                by_book.setdefault(o.bookmaker, {})[o.selection] = o.odds_decimal
        for bookmaker, book_odds in by_book.items():
            value_bets.extend(detect_value_bets(model_probs, book_odds, bookmaker, "1x2"))

    def latest_stats(team: Team) -> dict:
        if not team.stats:
            return {}
        s = sorted(team.stats, key=lambda x: x.as_of_date, reverse=True)[0]
        return {
            "goals_for_avg": s.goals_for_avg,
            "goals_against_avg": s.goals_against_avg,
            "xg_for_avg": s.xg_for_avg,
            "xg_against_avg": s.xg_against_avg,
            "form_last5": s.form_last5,
            "days_rest": s.days_rest,
        }

    return FixtureDetailOut(
        **base.model_dump(),
        home_score_ht=fixture.home_score_ht,
        away_score_ht=fixture.away_score_ht,
        odds=odds,
        value_bets=value_bets,
        injuries={
            "home": [
                {"player": i.player_name, "status": i.status, "reason": i.reason, "confirmed": i.confirmed, "is_demo": i.is_demo}
                for i in fixture.home_team.injuries
            ],
            "away": [
                {"player": i.player_name, "status": i.status, "reason": i.reason, "confirmed": i.confirmed, "is_demo": i.is_demo}
                for i in fixture.away_team.injuries
            ],
        },
        team_comparison={
            "home": latest_stats(fixture.home_team),
            "away": latest_stats(fixture.away_team),
            "elo": {"home": fixture.home_team.elo_rating, "away": fixture.away_team.elo_rating},
            "demo_mode": settings.is_demo,
        },
    )
