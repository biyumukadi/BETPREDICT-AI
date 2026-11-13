"""Odds comparison, implied probabilities and value-bet detection."""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple


def implied_probability(odds_decimal: float) -> float:
    if odds_decimal <= 1.0:
        return 1.0
    return 1.0 / odds_decimal


def bookmaker_margin(odds: List[float]) -> float:
    """Overround / margin across a mutually exclusive market."""
    if not odds:
        return 0.0
    return sum(implied_probability(o) for o in odds) - 1.0


def remove_vig(odds: List[float]) -> List[float]:
    imps = [implied_probability(o) for o in odds]
    total = sum(imps)
    if total <= 0:
        return [1 / len(odds)] * len(odds)
    return [i / total for i in imps]


def expected_value(model_probability: float, odds_decimal: float) -> float:
    """EV = (p * odds) - 1"""
    return (model_probability * odds_decimal) - 1.0


def detect_value_bets(
    model_probs: Dict[str, float],
    bookmaker_odds: Dict[str, float],
    bookmaker: str,
    market: str,
    min_ev: float = 0.03,
) -> List[Dict]:
    """
    Compare model probabilities to offered odds.
    Positive EV is theoretical only and does not guarantee profit.
    """
    results = []
    odds_list = list(bookmaker_odds.values())
    margin = bookmaker_margin(odds_list)
    for selection, odds in bookmaker_odds.items():
        p = model_probs.get(selection)
        if p is None:
            continue
        ev = expected_value(p, odds)
        if ev >= min_ev:
            results.append(
                {
                    "bookmaker": bookmaker,
                    "market": market,
                    "selection": selection,
                    "model_probability": round(p, 4),
                    "odds_decimal": odds,
                    "implied_probability": round(implied_probability(odds), 4),
                    "expected_value": round(ev, 4),
                    "bookmaker_margin": round(margin, 4),
                    "disclaimer": (
                        "Une valeur attendue positive estimée ne garantit aucun gain réel. "
                        "A positive estimated expected value does not guarantee any real profit."
                    ),
                }
            )
    return results


def fair_odds(probability: float) -> Optional[float]:
    if probability <= 0:
        return None
    return round(1.0 / probability, 3)
