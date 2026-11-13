"""Logistic regression style 1X2 probability from engineered features."""

from __future__ import annotations

from typing import Dict, Tuple

import numpy as np
from sklearn.linear_model import LogisticRegression


FEATURE_ORDER = [
    "elo_diff",
    "form_diff",
    "gf_avg_diff",
    "ga_avg_diff",
    "xg_diff",
    "home_advantage",
    "rest_diff",
    "injury_impact",
]


def features_from_dict(raw: Dict[str, float]) -> np.ndarray:
    return np.array([[float(raw.get(k, 0.0)) for k in FEATURE_ORDER]], dtype=float)


def fit_default_logistic() -> LogisticRegression:
    """
    Fit a small logistic model on synthetic historically-plausible patterns.
    This is a bootstrap prior used when insufficient labeled history exists.
    Demo/training labels are not match results from the evaluation set.
    """
    rng = np.random.default_rng(42)
    n = 4000
    X = rng.normal(0, 1, size=(n, len(FEATURE_ORDER)))
    # Stronger home / attack / Elo => more home wins
    logits = (
        0.55 * X[:, 0]
        + 0.35 * X[:, 1]
        + 0.40 * X[:, 2]
        - 0.35 * X[:, 3]
        + 0.45 * X[:, 4]
        + 0.25 * X[:, 5]
        + 0.10 * X[:, 6]
        - 0.20 * X[:, 7]
    )
    # Three-class via thresholds around draw band
    y = np.where(logits > 0.35, 0, np.where(logits < -0.35, 2, 1))  # 0=H,1=D,2=A
    model = LogisticRegression(max_iter=500)
    model.fit(X, y)
    return model


_MODEL: LogisticRegression | None = None


def get_logistic_model() -> LogisticRegression:
    global _MODEL
    if _MODEL is None:
        _MODEL = fit_default_logistic()
    return _MODEL


def logistic_probs(features: Dict[str, float]) -> Tuple[float, float, float]:
    model = get_logistic_model()
    X = features_from_dict(features)
    probs = model.predict_proba(X)[0]
    # Ensure class order H,D,A
    class_to_idx = {c: i for i, c in enumerate(model.classes_)}
    home = float(probs[class_to_idx.get(0, 0)])
    draw = float(probs[class_to_idx.get(1, 1)])
    away = float(probs[class_to_idx.get(2, 2)])
    total = home + draw + away
    return home / total, draw / total, away / total
