"""Evaluate published predictions against finished fixtures."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.prediction import Prediction, PredictionEvaluation
from app.models.sport import Fixture, FixtureStatus
from app.services.prediction.calibration import brier_score_multiclass, log_loss_multiclass


def _outcome_idx(home: int, away: int) -> int:
    if home > away:
        return 0
    if home == away:
        return 1
    return 2


def _market_results(pred: Prediction, home: int, away: int) -> dict:
    total = home + away
    actual_1x2 = "1" if home > away else ("X" if home == away else "2")
    results = {"1x2": actual_1x2}
    for m in pred.markets:
        key = f"{m.market.value}:{m.selection}"
        correct = None
        if m.market.value == "1x2":
            correct = m.selection == actual_1x2
        elif m.market.value == "btts":
            both = home > 0 and away > 0
            correct = (m.selection == "Yes" and both) or (m.selection == "No" and not both)
        elif m.market.value.startswith("ou_"):
            line = {"ou_1_5": 1.5, "ou_2_5": 2.5, "ou_3_5": 3.5}[m.market.value]
            is_over = total > line
            correct = (m.selection == "Over" and is_over) or (m.selection == "Under" and not is_over)
        elif m.market.value == "exact_score":
            correct = m.selection == f"{home}-{away}"
        results[key] = correct
    return results


async def evaluate_finished(session: AsyncSession) -> dict:
    q = (
        select(Fixture)
        .where(Fixture.status == FixtureStatus.FINISHED, Fixture.home_score.is_not(None))
        .options(
            selectinload(Fixture.predictions).selectinload(Prediction.markets),
            selectinload(Fixture.predictions).selectinload(Prediction.evaluation),
        )
    )
    fixtures = (await session.execute(q)).scalars().unique().all()
    created = 0
    for fixture in fixtures:
        for pred in fixture.predictions:
            if pred.evaluation:
                continue
            # Only evaluate predictions published before kickoff (no leakage)
            if pred.published_at >= fixture.kickoff_at:
                continue
            idx = _outcome_idx(fixture.home_score, fixture.away_score)
            probs = (pred.home_win_prob, pred.draw_prob, pred.away_win_prob)
            session.add(
                PredictionEvaluation(
                    prediction_id=pred.id,
                    evaluated_at=datetime.now(timezone.utc),
                    actual_home_score=fixture.home_score,
                    actual_away_score=fixture.away_score,
                    result_1x2_correct=(
                        (idx == 0 and pred.home_win_prob >= max(pred.draw_prob, pred.away_win_prob))
                        or (idx == 1 and pred.draw_prob >= max(pred.home_win_prob, pred.away_win_prob))
                        or (idx == 2 and pred.away_win_prob >= max(pred.home_win_prob, pred.draw_prob))
                    ),
                    brier_score_1x2=brier_score_multiclass(probs, idx),
                    log_loss_1x2=log_loss_multiclass(probs, idx),
                    market_results=_market_results(pred, fixture.home_score, fixture.away_score),
                    locked=True,
                )
            )
            created += 1
    await session.flush()
    return {"evaluations_created": created}
