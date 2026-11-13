"""
Seed DEMO data and bootstrap users.

All sporting statistics here are synthetic demo parameters, explicitly labeled.
They are not live match statistics.
"""

from __future__ import annotations

import asyncio
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select

from app.core.config import get_settings
from app.core.security import hash_password
from app.db.base import Base
from app.db.session import AsyncSessionLocal, async_engine
from app.models.admin import DataSourceConfig
from app.models.budget import BudgetProfile
from app.models.notification import NotificationPreference
from app.models.sport import Injury, Team, TeamStats
from app.models.user import Subscription, SubscriptionPlan, User, UserRole
from app.services.evaluation import evaluate_finished
from app.services.sync import generate_predictions_for_upcoming, sync_catalog, sync_fixtures


async def seed_users(session) -> None:
    demos = [
        ("admin@betpredict.ai", "Admin Demo", UserRole.ADMIN, SubscriptionPlan.PRO, "Admin123!"),
        ("premium@betpredict.ai", "Premium Demo", UserRole.PREMIUM, SubscriptionPlan.PREMIUM, "Premium123!"),
        ("user@betpredict.ai", "Free Demo", UserRole.USER, SubscriptionPlan.FREE, "User123!"),
    ]
    for email, name, role, plan, password in demos:
        existing = (await session.execute(select(User).where(User.email == email))).scalar_one_or_none()
        if existing:
            continue
        user = User(
            email=email,
            hashed_password=hash_password(password),
            full_name=name,
            role=role,
            date_of_birth=date(1990, 1, 1),
            age_verified=True,
            is_verified=True,
            mfa_enabled=(role == UserRole.ADMIN),
            mfa_secret="000000" if role == UserRole.ADMIN else None,
            locale="fr",
        )
        session.add(user)
        await session.flush()
        session.add(
            Subscription(
                user_id=user.id,
                plan=plan,
                status="active",
                payment_provider="demo",
                notes="DEMO account",
            )
        )
        session.add(BudgetProfile(user_id=user.id, max_budget=200, daily_loss_limit=25))
        session.add(NotificationPreference(user_id=user.id))


async def seed_stats_and_injuries(session) -> None:
    teams = (await session.execute(select(Team))).scalars().all()
    today = date.today()
    forms = ["WWDLW", "DWDWL", "LLWWD", "WDLWD", "WDWDL", "LWDLW"]
    for i, team in enumerate(teams):
        exists = (
            await session.execute(select(TeamStats).where(TeamStats.team_id == team.id, TeamStats.as_of_date == today))
        ).scalar_one_or_none()
        if not exists:
            # Strength correlates loosely with Elo for demo realism of the model inputs
            strength = (team.elo_rating - 1500) / 400.0
            gf = round(1.15 + max(-0.4, min(0.9, strength)) + (i % 3) * 0.05, 2)
            ga = round(1.25 - max(-0.3, min(0.6, strength)) + (i % 2) * 0.04, 2)
            session.add(
                TeamStats(
                    team_id=team.id,
                    as_of_date=today,
                    matches_played=10,
                    wins=4 + (i % 3),
                    draws=2,
                    losses=4 - (i % 2),
                    goals_for=int(gf * 10),
                    goals_against=int(ga * 10),
                    goals_for_avg=gf,
                    goals_against_avg=ga,
                    xg_for_avg=round(gf - 0.05, 2),
                    xg_against_avg=round(ga + 0.05, 2),
                    home_goals_for_avg=round(gf + 0.2, 2),
                    home_goals_against_avg=round(ga - 0.15, 2),
                    away_goals_for_avg=round(gf - 0.15, 2),
                    away_goals_against_avg=round(ga + 0.15, 2),
                    form_last5=forms[i % len(forms)],
                    corners_avg=round(4.5 + (i % 4) * 0.3, 2),
                    cards_avg=round(2.1 + (i % 3) * 0.2, 2),
                    days_rest=4 + (i % 5),
                    is_demo=True,
                )
            )
        # One demo injury every other team
        if i % 2 == 0:
            inj_exists = (
                await session.execute(select(Injury).where(Injury.team_id == team.id))
            ).scalar_one_or_none()
            if not inj_exists:
                session.add(
                    Injury(
                        team_id=team.id,
                        player_name=f"Demo Player {i}",
                        reason="Muscle injury (DEMO)",
                        status="out",
                        confirmed=True,
                        expected_return=today + timedelta(days=14),
                        is_demo=True,
                        notes="DEMO injury record",
                    )
                )


async def seed_data_sources(session) -> None:
    sources = [
        ("demo", "demo", True, False),
        ("api_football", "api_football", False, True),
        ("sportmonks", "sportmonks", False, True),
        ("football_data_org", "football_data_org", False, True),
    ]
    for name, key, enabled, licensed in sources:
        exists = (
            await session.execute(select(DataSourceConfig).where(DataSourceConfig.name == name))
        ).scalar_one_or_none()
        if exists:
            continue
        session.add(
            DataSourceConfig(
                name=name,
                provider_key=key,
                is_enabled=enabled,
                is_licensed=licensed,
                meta={"note": "Enable only with valid license/credentials"},
            )
        )


async def run_seed() -> None:
    settings = get_settings()
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        await seed_users(session)
        await seed_data_sources(session)
        await sync_catalog(session)
        await sync_fixtures(session)
        await seed_stats_and_injuries(session)
        await generate_predictions_for_upcoming(session)
        # Generate predictions also for recently finished demo fixtures (published before kickoff)
        from app.models.sport import Fixture, FixtureStatus
        from app.services.prediction.engine import PredictionEngine
        from app.services.sync import MARKET_ENUM, _stats_for_team
        from app.models.prediction import Prediction, PredictionMarket
        from sqlalchemy.orm import selectinload

        engine = PredictionEngine()
        finished = (
            await session.execute(
                select(Fixture)
                .where(Fixture.status == FixtureStatus.FINISHED)
                .options(
                    selectinload(Fixture.home_team).selectinload(Team.stats),
                    selectinload(Fixture.home_team).selectinload(Team.injuries),
                    selectinload(Fixture.away_team).selectinload(Team.stats),
                    selectinload(Fixture.away_team).selectinload(Team.injuries),
                    selectinload(Fixture.predictions),
                )
            )
        ).scalars().unique().all()
        for fixture in finished:
            if fixture.predictions:
                continue
            home_in = _stats_for_team(fixture.home_team, fixture.kickoff_at)
            away_in = _stats_for_team(fixture.away_team, fixture.kickoff_at)
            result = engine.predict(home_in, away_in)
            # Ensure no future leakage: publish before kickoff
            published = fixture.kickoff_at - timedelta(hours=6)
            pred = Prediction(
                fixture_id=fixture.id,
                model_version=result.model_version,
                published_at=published,
                is_demo=True,
                home_win_prob=result.home_win_prob,
                draw_prob=result.draw_prob,
                away_win_prob=result.away_win_prob,
                confidence=result.confidence,
                expected_home_goals=result.expected_home_goals,
                expected_away_goals=result.expected_away_goals,
                most_likely_score=result.most_likely_score,
                most_likely_score_prob=result.most_likely_score_prob,
                explanation_fr=result.explanation_fr,
                explanation_en=result.explanation_en,
                key_factors=result.key_factors,
                uncertainties=result.uncertainties,
                model_breakdown=result.model_breakdown,
                features_snapshot=result.features_snapshot,
            )
            session.add(pred)
            await session.flush()
            for m in result.markets:
                session.add(
                    PredictionMarket(
                        prediction_id=pred.id,
                        market=MARKET_ENUM.get(m["market"], list(MARKET_ENUM.values())[0]),
                        selection=m["selection"],
                        probability=m["probability"],
                        confidence=m["confidence"],
                        recommended=m["recommended"],
                        rationale=m.get("rationale"),
                    )
                )
        # Clear identity-map caches so newly added finished predictions are visible
        session.expire_all()
        await evaluate_finished(session)
        await session.commit()
    print(f"Seed complete. demo_mode={settings.is_demo}")


if __name__ == "__main__":
    asyncio.run(run_seed())
