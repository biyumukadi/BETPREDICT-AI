"""Monte-Carlo scoreline simulation."""

from __future__ import annotations

from typing import Dict, Tuple

import numpy as np


def simulate_matches(
    lambda_home: float,
    lambda_away: float,
    n_sims: int = 10_000,
    seed: int = 7,
) -> Dict[str, float]:
    rng = np.random.default_rng(seed)
    home_goals = rng.poisson(lam=max(lambda_home, 0.05), size=n_sims)
    away_goals = rng.poisson(lam=max(lambda_away, 0.05), size=n_sims)
    home_wins = np.sum(home_goals > away_goals) / n_sims
    draws = np.sum(home_goals == away_goals) / n_sims
    away_wins = np.sum(home_goals < away_goals) / n_sims
    totals = home_goals + away_goals
    return {
        "home": float(home_wins),
        "draw": float(draws),
        "away": float(away_wins),
        "over_1_5": float(np.mean(totals > 1.5)),
        "over_2_5": float(np.mean(totals > 2.5)),
        "over_3_5": float(np.mean(totals > 3.5)),
        "btts_yes": float(np.mean((home_goals > 0) & (away_goals > 0))),
        "avg_home_goals": float(np.mean(home_goals)),
        "avg_away_goals": float(np.mean(away_goals)),
    }


def ht_result_approx(lambda_home: float, lambda_away: float, n_sims: int = 8_000) -> Tuple[float, float, float]:
    """Approximate HT result by scaling intensities to ~45 minutes."""
    return (
        simulate_matches(lambda_home * 0.45, lambda_away * 0.45, n_sims=n_sims)["home"],
        simulate_matches(lambda_home * 0.45, lambda_away * 0.45, n_sims=n_sims)["draw"],
        simulate_matches(lambda_home * 0.45, lambda_away * 0.45, n_sims=n_sims)["away"],
    )
