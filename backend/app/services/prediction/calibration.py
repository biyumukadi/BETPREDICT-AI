"""Probability calibration helpers."""

from __future__ import annotations

from typing import Tuple

import numpy as np


def normalize_triplet(home: float, draw: float, away: float) -> Tuple[float, float, float]:
    vals = np.array([max(home, 1e-9), max(draw, 1e-9), max(away, 1e-9)], dtype=float)
    vals = vals / vals.sum()
    return float(vals[0]), float(vals[1]), float(vals[2])


def temperature_scale(probs: Tuple[float, float, float], temperature: float = 1.15) -> Tuple[float, float, float]:
    """Softmax temperature scaling for mild calibration."""
    logits = np.log(np.clip(probs, 1e-9, 1.0))
    scaled = np.exp(logits / max(temperature, 1e-3))
    scaled = scaled / scaled.sum()
    return float(scaled[0]), float(scaled[1]), float(scaled[2])


def weighted_ensemble(
    components: dict[str, Tuple[float, float, float]],
    weights: dict[str, float],
) -> Tuple[float, float, float]:
    home = draw = away = 0.0
    wsum = 0.0
    for name, (h, d, a) in components.items():
        w = float(weights.get(name, 0.0))
        home += w * h
        draw += w * d
        away += w * a
        wsum += w
    if wsum <= 0:
        return 1 / 3, 1 / 3, 1 / 3
    return normalize_triplet(home / wsum, draw / wsum, away / wsum)


def confidence_from_entropy(home: float, draw: float, away: float) -> float:
    """Calibrated confidence index in [0,1] from distribution sharpness."""
    p = np.array([home, draw, away], dtype=float)
    p = p / p.sum()
    entropy = -np.sum(p * np.log(np.clip(p, 1e-12, 1.0)))
    max_entropy = np.log(3.0)
    sharpness = 1.0 - (entropy / max_entropy)
    # Cap confidence — never present as certainty
    return float(np.clip(0.35 + 0.55 * sharpness, 0.35, 0.92))


def brier_score_multiclass(probs: Tuple[float, float, float], outcome_idx: int) -> float:
    y = np.zeros(3)
    y[outcome_idx] = 1.0
    p = np.array(probs, dtype=float)
    return float(np.mean((p - y) ** 2))


def log_loss_multiclass(probs: Tuple[float, float, float], outcome_idx: int) -> float:
    p = np.clip(probs[outcome_idx], 1e-15, 1.0)
    return float(-np.log(p))
