"""Gradient-boosted model for advanced 1X2 predictions."""

from __future__ import annotations

from typing import Dict, Tuple

import numpy as np

from app.services.prediction.logistic import FEATURE_ORDER, features_from_dict

try:
    from xgboost import XGBClassifier

    HAS_XGB = True
except Exception:  # pragma: no cover
    HAS_XGB = False
    from sklearn.ensemble import GradientBoostingClassifier as XGBClassifier


_MODEL = None


def _train_bootstrap() -> object:
    rng = np.random.default_rng(123)
    n = 5000
    X = rng.normal(0, 1, size=(n, len(FEATURE_ORDER)))
    score = (
        0.6 * X[:, 0]
        + 0.3 * X[:, 1]
        + 0.45 * X[:, 2]
        - 0.4 * X[:, 3]
        + 0.5 * X[:, 4]
        + 0.2 * X[:, 5]
        + 0.08 * X[:, 6]
        - 0.25 * X[:, 7]
    )
    y = np.where(score > 0.3, 0, np.where(score < -0.3, 2, 1))
    if HAS_XGB:
        model = XGBClassifier(
            n_estimators=80,
            max_depth=3,
            learning_rate=0.08,
            subsample=0.9,
            colsample_bytree=0.9,
            objective="multi:softprob",
            num_class=3,
            eval_metric="mlogloss",
            verbosity=0,
        )
    else:
        model = XGBClassifier(random_state=123)
    model.fit(X, y)
    return model


def get_xgb_model() -> object:
    global _MODEL
    if _MODEL is None:
        _MODEL = _train_bootstrap()
    return _MODEL


def xgb_probs(features: Dict[str, float]) -> Tuple[float, float, float]:
    model = get_xgb_model()
    X = features_from_dict(features)
    probs = model.predict_proba(X)[0]
    classes = getattr(model, "classes_", np.array([0, 1, 2]))
    class_to_idx = {int(c): i for i, c in enumerate(classes)}
    home = float(probs[class_to_idx.get(0, 0)])
    draw = float(probs[class_to_idx.get(1, 1)])
    away = float(probs[class_to_idx.get(2, 2)])
    total = home + draw + away
    return home / total, draw / total, away / total
