"""Unit tests for the ensemble prediction engine — no invented live stats."""

from app.services.prediction.engine import PredictionEngine, TeamInput
from app.services.prediction.poisson import poisson_market_bundle, score_matrix
from app.services.prediction.elo import elo_outcome_probs, update_elo
from app.services.odds.value import expected_value, implied_probability, bookmaker_margin
from app.services.prediction.calibration import brier_score_multiclass, normalize_triplet


def _team(name: str, elo: float, gf: float, ga: float) -> TeamInput:
    return TeamInput(
        name=name,
        elo=elo,
        goals_for_avg=gf,
        goals_against_avg=ga,
        home_gf_avg=gf + 0.2,
        home_ga_avg=ga - 0.1,
        away_gf_avg=gf - 0.2,
        away_ga_avg=ga + 0.1,
        xg_for_avg=gf,
        xg_against_avg=ga,
        form_last5="WWDWL",
        days_rest=6,
        corners_avg=5.0,
        cards_avg=2.2,
        injuries=[],
    )


def test_poisson_probabilities_sum_to_one():
    bundle = poisson_market_bundle(1.4, 1.1)
    assert abs(bundle["home"] + bundle["draw"] + bundle["away"] - 1.0) < 1e-6
    assert 0 < bundle["most_likely_score_prob"] <= 1


def test_score_matrix_normalized():
    m = score_matrix(1.2, 0.9)
    # Truncation at max_goals leaves a tiny residual mass
    assert abs(m.sum() - 1.0) < 1e-4


def test_elo_stronger_home_favoured():
    h, d, a = elo_outcome_probs(1800, 1500)
    assert h > a
    assert abs(h + d + a - 1.0) < 1e-6


def test_elo_update_changes_ratings():
    h2, a2 = update_elo(1600, 1600, 2, 0)
    assert h2 > 1600
    assert a2 < 1600


def test_ensemble_output_shape():
    engine = PredictionEngine()
    result = engine.predict(_team("A", 1750, 1.8, 0.9), _team("B", 1550, 1.1, 1.4))
    assert abs(result.home_win_prob + result.draw_prob + result.away_win_prob - 1.0) < 1e-3
    assert 0.35 <= result.confidence <= 0.92
    assert result.most_likely_score.count("-") == 1
    assert any(m["market"] == "1x2" for m in result.markets)
    assert "ne garantissent" in result.explanation_fr.lower() or "estimation" in result.explanation_fr.lower()


def test_expected_value_formula():
    assert abs(expected_value(0.5, 2.2) - 0.1) < 1e-9
    assert abs(implied_probability(2.0) - 0.5) < 1e-9
    assert bookmaker_margin([2.0, 3.5, 3.5]) > 0


def test_normalize_and_brier():
    h, d, a = normalize_triplet(0.5, 0.3, 0.2)
    assert abs(h + d + a - 1) < 1e-9
    score = brier_score_multiclass((0.7, 0.2, 0.1), 0)
    assert 0 <= score < 0.2
