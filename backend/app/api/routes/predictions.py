from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_optional_user
from app.db.session import get_db
from app.models.prediction import Prediction, PredictionEvaluation
from app.models.sport import Competition, Fixture
from app.schemas.fixtures import MarketOut, PredictionOut

router = APIRouter(prefix="/predictions", tags=["predictions"])


@router.get("/performance")
async def performance(db: AsyncSession = Depends(get_db)):
    """Public AI performance — includes incorrect predictions (no selective deletion)."""
    evals = (
        await db.execute(
            select(PredictionEvaluation)
            .options(selectinload(PredictionEvaluation.prediction).selectinload(Prediction.fixture).selectinload(Fixture.competition))
        )
    ).scalars().all()
    if not evals:
        return {
            "sample_size": 0,
            "hit_rate_1x2": None,
            "avg_brier": None,
            "avg_log_loss": None,
            "by_competition": {},
            "notice": "No evaluated predictions yet. Incorrect predictions cannot be removed from public stats.",
        }
    hits = sum(1 for e in evals if e.result_1x2_correct)
    by_comp: dict = {}
    for e in evals:
        comp = e.prediction.fixture.competition.name if e.prediction and e.prediction.fixture else "Unknown"
        bucket = by_comp.setdefault(comp, {"n": 0, "hits": 0, "brier": 0.0})
        bucket["n"] += 1
        bucket["hits"] += int(e.result_1x2_correct)
        bucket["brier"] += e.brier_score_1x2
    for v in by_comp.values():
        v["hit_rate"] = v["hits"] / v["n"] if v["n"] else None
        v["avg_brier"] = v["brier"] / v["n"] if v["n"] else None
        del v["brier"]
    return {
        "sample_size": len(evals),
        "hit_rate_1x2": hits / len(evals),
        "avg_brier": sum(e.brier_score_1x2 for e in evals) / len(evals),
        "avg_log_loss": sum(e.log_loss_1x2 for e in evals) / len(evals),
        "by_competition": by_comp,
        "locked_evaluations": all(e.locked for e in evals),
        "notice_fr": "Les statistiques publiques incluent toutes les prédictions, correctes et incorrectes.",
        "notice_en": "Public statistics include all predictions, correct and incorrect.",
    }


@router.get("/history")
async def history(limit: int = 50, db: AsyncSession = Depends(get_db), user=Depends(get_optional_user)):
    preds = (
        await db.execute(
            select(Prediction)
            .options(
                selectinload(Prediction.markets),
                selectinload(Prediction.evaluation),
                selectinload(Prediction.fixture).selectinload(Fixture.home_team),
                selectinload(Prediction.fixture).selectinload(Fixture.away_team),
                selectinload(Prediction.fixture).selectinload(Fixture.competition),
            )
            .order_by(Prediction.published_at.desc())
            .limit(min(limit, 200))
        )
    ).scalars().all()
    out = []
    for p in preds:
        f = p.fixture
        out.append(
            {
                "prediction": PredictionOut(
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
                        for m in p.markets
                    ],
                ).model_dump(),
                "fixture": {
                    "id": str(f.id),
                    "kickoff_at": f.kickoff_at.isoformat(),
                    "home": f.home_team.name,
                    "away": f.away_team.name,
                    "competition": f.competition.name,
                    "score": f"{f.home_score}-{f.away_score}" if f.home_score is not None else None,
                    "is_demo": f.is_demo,
                },
                "evaluation": None
                if not p.evaluation
                else {
                    "result_1x2_correct": p.evaluation.result_1x2_correct,
                    "brier_score_1x2": p.evaluation.brier_score_1x2,
                    "log_loss_1x2": p.evaluation.log_loss_1x2,
                    "locked": p.evaluation.locked,
                },
            }
        )
    return out


@router.delete("/{prediction_id}/evaluation")
async def forbid_selective_delete(prediction_id: UUID):
    raise HTTPException(
        status_code=403,
        detail="Selective deletion of incorrect predictions from public statistics is forbidden.",
    )
