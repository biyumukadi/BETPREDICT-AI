"""Sync fixtures/teams from the configured provider into PostgreSQL."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.prediction import MarketType, Prediction, PredictionMarket
from app.models.sport import Competition, Fixture, FixtureStatus, Injury, Team, TeamStats
from app.models.odds import OddsSnapshot
from app.services.data_providers.factory import get_provider
from app.services.prediction.engine import PredictionEngine, TeamInput


STATUS_MAP = {
    "scheduled": FixtureStatus.SCHEDULED,
    "live": FixtureStatus.LIVE,
    "finished": FixtureStatus.FINISHED,
    "postponed": FixtureStatus.POSTPONED,
    "cancelled": FixtureStatus.CANCELLED,
}


async def sync_catalog(session: AsyncSession) -> dict:
    provider = get_provider()
    competitions = await provider.fetch_competitions()
    created_c = created_t = 0
    for pc in competitions:
        existing = (
            await session.execute(
                select(Competition).where(
                    Competition.provider == provider.name,
                    Competition.external_id == pc.external_id,
                )
            )
        ).scalar_one_or_none()
        if existing:
            competition = existing
        else:
            competition = Competition(
                external_id=pc.external_id,
                provider=provider.name,
                name=pc.name,
                country=pc.country,
                code=pc.code,
                season=pc.season,
                logo_url=pc.logo_url,
            )
            session.add(competition)
            await session.flush()
            created_c += 1

        teams = await provider.fetch_teams(pc.external_id)
        for pt in teams:
            t_existing = (
                await session.execute(
                    select(Team).where(Team.provider == provider.name, Team.external_id == pt.external_id)
                )
            ).scalar_one_or_none()
            if t_existing:
                t_existing.elo_rating = pt.elo_rating
                continue
            session.add(
                Team(
                    external_id=pt.external_id,
                    provider=provider.name,
                    name=pt.name,
                    short_name=pt.short_name,
                    country=pt.country,
                    competition_id=competition.id,
                    elo_rating=pt.elo_rating,
                    logo_url=pt.logo_url,
                )
            )
            created_t += 1
    await session.flush()
    return {"provider": provider.name, "competitions_created": created_c, "teams_created": created_t}


async def sync_fixtures(session: AsyncSession, days_back: int = 3, days_forward: int = 7) -> dict:
    provider = get_provider()
    now = datetime.now(timezone.utc)
    fixtures = await provider.fetch_fixtures(now - timedelta(days=days_back), now + timedelta(days=days_forward))
    upserted = 0
    for pf in fixtures:
        competition = (
            await session.execute(
                select(Competition).where(
                    Competition.provider == provider.name,
                    Competition.external_id == pf.competition_external_id,
                )
            )
        ).scalar_one_or_none()
        home = (
            await session.execute(
                select(Team).where(Team.provider == provider.name, Team.external_id == pf.home_team_external_id)
            )
        ).scalar_one_or_none()
        away = (
            await session.execute(
                select(Team).where(Team.provider == provider.name, Team.external_id == pf.away_team_external_id)
            )
        ).scalar_one_or_none()
        if not competition or not home or not away:
            continue
        existing = (
            await session.execute(
                select(Fixture).where(Fixture.provider == provider.name, Fixture.external_id == pf.external_id)
            )
        ).scalar_one_or_none()
        status = STATUS_MAP.get(pf.status, FixtureStatus.SCHEDULED)
        if existing:
            existing.status = status
            existing.home_score = pf.home_score
            existing.away_score = pf.away_score
            existing.home_score_ht = pf.home_score_ht
            existing.away_score_ht = pf.away_score_ht
            existing.home_xg = pf.home_xg
            existing.away_xg = pf.away_xg
            fixture = existing
        else:
            fixture = Fixture(
                external_id=pf.external_id,
                provider=provider.name,
                competition_id=competition.id,
                home_team_id=home.id,
                away_team_id=away.id,
                kickoff_at=pf.kickoff_at,
                status=status,
                matchday=pf.matchday if isinstance(pf.matchday, int) else None,
                venue=pf.venue,
                home_score=pf.home_score,
                away_score=pf.away_score,
                home_score_ht=pf.home_score_ht,
                away_score_ht=pf.away_score_ht,
                home_xg=pf.home_xg,
                away_xg=pf.away_xg,
                is_demo=provider.name == "demo",
                raw_payload=pf.raw,
            )
            session.add(fixture)
            await session.flush()
        upserted += 1

        # Odds snapshots (demo or licensed)
        odds = await provider.fetch_odds(pf.external_id)
        for o in odds:
            session.add(
                OddsSnapshot(
                    fixture_id=fixture.id,
                    bookmaker=o.bookmaker,
                    market=o.market,
                    selection=o.selection,
                    odds_decimal=o.odds_decimal,
                    implied_probability=1.0 / o.odds_decimal,
                    captured_at=o.captured_at,
                    is_demo=provider.name == "demo",
                    source_licensed=o.source_licensed,
                    notes="DEMO odds" if provider.name == "demo" else None,
                )
            )
    await session.flush()
    return {"provider": provider.name, "fixtures_upserted": upserted}


def _stats_for_team(team: Team, as_of: datetime) -> TeamInput:
    stats = sorted(team.stats, key=lambda s: s.as_of_date, reverse=True)
    s: Optional[TeamStats] = stats[0] if stats else None
    injuries = [
        {"player_name": i.player_name, "status": i.status, "confirmed": i.confirmed, "reason": i.reason}
        for i in team.injuries
        if i.confirmed
    ]
    if s:
        return TeamInput(
            name=team.name,
            elo=team.elo_rating,
            goals_for_avg=s.goals_for_avg,
            goals_against_avg=s.goals_against_avg,
            home_gf_avg=s.home_goals_for_avg,
            home_ga_avg=s.home_goals_against_avg,
            away_gf_avg=s.away_goals_for_avg,
            away_ga_avg=s.away_goals_against_avg,
            xg_for_avg=s.xg_for_avg,
            xg_against_avg=s.xg_against_avg,
            form_last5=s.form_last5 or "",
            days_rest=s.days_rest or 7,
            corners_avg=s.corners_avg,
            cards_avg=s.cards_avg,
            injuries=injuries,
        )
    # Fallback from Elo only when stats missing
    return TeamInput(
        name=team.name,
        elo=team.elo_rating,
        goals_for_avg=1.25,
        goals_against_avg=1.15,
        home_gf_avg=1.4,
        home_ga_avg=1.05,
        away_gf_avg=1.1,
        away_ga_avg=1.25,
        form_last5="DWDWL",
        days_rest=6,
        injuries=injuries,
    )


MARKET_ENUM = {
    "1x2": MarketType.MATCH_RESULT,
    "double_chance": MarketType.DOUBLE_CHANCE,
    "ou_1_5": MarketType.OVER_UNDER_15,
    "ou_2_5": MarketType.OVER_UNDER_25,
    "ou_3_5": MarketType.OVER_UNDER_35,
    "btts": MarketType.BTTS,
    "exact_score": MarketType.EXACT_SCORE,
    "ht_result": MarketType.HT_RESULT,
    "corners": MarketType.CORNERS,
    "cards": MarketType.CARDS,
    "asian_handicap": MarketType.ASIAN_HANDICAP,
}


async def generate_predictions_for_upcoming(session: AsyncSession) -> dict:
    engine = PredictionEngine()
    now = datetime.now(timezone.utc)
    q = (
        select(Fixture)
        .where(Fixture.status == FixtureStatus.SCHEDULED, Fixture.kickoff_at >= now)
        .options(
            selectinload(Fixture.home_team).selectinload(Team.stats),
            selectinload(Fixture.home_team).selectinload(Team.injuries),
            selectinload(Fixture.away_team).selectinload(Team.stats),
            selectinload(Fixture.away_team).selectinload(Team.injuries),
            selectinload(Fixture.predictions),
        )
    )
    fixtures = (await session.execute(q)).scalars().all()
    created = 0
    for fixture in fixtures:
        if fixture.predictions:
            continue  # keep published predictions immutable until refresh job replaces carefully
        home_in = _stats_for_team(fixture.home_team, fixture.kickoff_at)
        away_in = _stats_for_team(fixture.away_team, fixture.kickoff_at)
        result = engine.predict(home_in, away_in)
        pred = Prediction(
            fixture_id=fixture.id,
            model_version=result.model_version,
            published_at=result.published_at,
            is_demo=fixture.is_demo,
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
                    market=MARKET_ENUM.get(m["market"], MarketType.MATCH_RESULT),
                    selection=m["selection"],
                    probability=m["probability"],
                    confidence=m["confidence"],
                    recommended=m["recommended"],
                    rationale=m.get("rationale"),
                )
            )
        created += 1
    await session.flush()
    return {"predictions_created": created}
