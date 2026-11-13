"""Elo rating utilities for football match outcomes."""

from __future__ import annotations

from math import exp
from typing import Tuple


def expected_score(rating_a: float, rating_b: float, home_advantage: float = 65.0) -> float:
    """Expected score for team A (home) vs team B."""
    diff = rating_a + home_advantage - rating_b
    return 1.0 / (1.0 + 10 ** (-diff / 400.0))


def elo_outcome_probs(
    home_elo: float,
    away_elo: float,
    home_advantage: float = 65.0,
    draw_base: float = 0.27,
) -> Tuple[float, float, float]:
    """
    Convert Elo expected score into 1X2 probabilities.
    Draw probability shrinks when Elo gap is large.
    """
    p_home_or_drawish = expected_score(home_elo, away_elo, home_advantage)
    gap = abs(home_elo - away_elo) / 400.0
    draw = max(0.12, draw_base * exp(-0.55 * gap))
    remaining = 1.0 - draw
    # Split remaining mass proportional to Elo expectation vs complement
    home = remaining * p_home_or_drawish
    away = remaining * (1.0 - p_home_or_drawish)
    total = home + draw + away
    return home / total, draw / total, away / total


def update_elo(
    home_elo: float,
    away_elo: float,
    home_goals: int,
    away_goals: int,
    k: float = 20.0,
    home_advantage: float = 65.0,
) -> Tuple[float, float]:
    """Update Elo after a finished match. Call only with past results."""
    if home_goals > away_goals:
        score_home = 1.0
    elif home_goals == away_goals:
        score_home = 0.5
    else:
        score_home = 0.0
    expected = expected_score(home_elo, away_elo, home_advantage)
    goal_diff = abs(home_goals - away_goals)
    margin = 1.0 if goal_diff <= 1 else (1.5 if goal_diff == 2 else 1.75 + (goal_diff - 3) * 0.125)
    delta = k * margin * (score_home - expected)
    return home_elo + delta, away_elo - delta
