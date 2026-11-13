"""Independent Poisson scoreline model."""

from __future__ import annotations

from math import exp, factorial
from typing import Dict, Tuple

import numpy as np


def poisson_pmf(k: int, lam: float) -> float:
    if lam <= 0:
        return 1.0 if k == 0 else 0.0
    return exp(-lam) * (lam**k) / factorial(k)


def score_matrix(lambda_home: float, lambda_away: float, max_goals: int = 8) -> np.ndarray:
    """Return P(home_goals=i, away_goals=j) for i,j in 0..max_goals."""
    home = np.array([poisson_pmf(i, lambda_home) for i in range(max_goals + 1)])
    away = np.array([poisson_pmf(j, lambda_away) for j in range(max_goals + 1)])
    return np.outer(home, away)


def match_outcome_probs(matrix: np.ndarray) -> Tuple[float, float, float]:
    home_win = float(np.tril(matrix, -1).sum())
    draw = float(np.trace(matrix))
    away_win = float(np.triu(matrix, 1).sum())
    total = home_win + draw + away_win
    if total <= 0:
        return 1 / 3, 1 / 3, 1 / 3
    return home_win / total, draw / total, away_win / total


def over_under_prob(matrix: np.ndarray, line: float) -> Tuple[float, float]:
    goals = np.add.outer(np.arange(matrix.shape[0]), np.arange(matrix.shape[1]))
    over = float(matrix[goals > line].sum())
    under = float(matrix[goals < line].sum())
    # Push probability for .5 lines is ~0; renormalize over/under
    mass = over + under
    if mass <= 0:
        return 0.5, 0.5
    return over / mass, under / mass


def btts_prob(matrix: np.ndarray) -> float:
    both = matrix.copy()
    both[0, :] = 0
    both[:, 0] = 0
    return float(both.sum())


def most_likely_score(matrix: np.ndarray) -> Tuple[str, float]:
    i, j = np.unravel_index(int(np.argmax(matrix)), matrix.shape)
    return f"{i}-{j}", float(matrix[i, j])


def estimate_lambdas(
    home_attack: float,
    home_defense: float,
    away_attack: float,
    away_defense: float,
    league_avg_home: float = 1.35,
    league_avg_away: float = 1.15,
) -> Tuple[float, float]:
    """Dixon-Coles style attack/defense strengths relative to league average."""
    lambda_home = max(0.05, home_attack * away_defense * league_avg_home)
    lambda_away = max(0.05, away_attack * home_defense * league_avg_away)
    return lambda_home, lambda_away


def poisson_market_bundle(lambda_home: float, lambda_away: float) -> Dict[str, float]:
    matrix = score_matrix(lambda_home, lambda_away)
    h, d, a = match_outcome_probs(matrix)
    o15, u15 = over_under_prob(matrix, 1.5)
    o25, u25 = over_under_prob(matrix, 2.5)
    o35, u35 = over_under_prob(matrix, 3.5)
    score, score_p = most_likely_score(matrix)
    return {
        "home": h,
        "draw": d,
        "away": a,
        "over_1_5": o15,
        "under_1_5": u15,
        "over_2_5": o25,
        "under_2_5": u25,
        "over_3_5": o35,
        "under_3_5": u35,
        "btts_yes": btts_prob(matrix),
        "btts_no": 1.0 - btts_prob(matrix),
        "dc_1x": h + d,
        "dc_x2": d + a,
        "dc_12": h + a,
        "most_likely_score": score,
        "most_likely_score_prob": score_p,
        "lambda_home": lambda_home,
        "lambda_away": lambda_away,
    }
