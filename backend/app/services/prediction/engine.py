"""Ensemble prediction engine combining Poisson, Elo, logistic, XGB and Monte-Carlo."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.services.prediction.calibration import (
    confidence_from_entropy,
    temperature_scale,
    weighted_ensemble,
)
from app.services.prediction.elo import elo_outcome_probs
from app.services.prediction.logistic import logistic_probs
from app.services.prediction.monte_carlo import ht_result_approx, simulate_matches
from app.services.prediction.poisson import estimate_lambdas, poisson_market_bundle
from app.services.prediction.xgboost_model import xgb_probs

MODEL_VERSION = "ensemble-v1.0.0"

DEFAULT_WEIGHTS = {
    "poisson": 0.30,
    "elo": 0.20,
    "logistic": 0.20,
    "xgboost": 0.20,
    "monte_carlo": 0.10,
}


@dataclass
class TeamInput:
    name: str
    elo: float
    goals_for_avg: float
    goals_against_avg: float
    home_gf_avg: float
    home_ga_avg: float
    away_gf_avg: float
    away_ga_avg: float
    xg_for_avg: Optional[float] = None
    xg_against_avg: Optional[float] = None
    form_last5: str = ""
    days_rest: int = 7
    corners_avg: Optional[float] = None
    cards_avg: Optional[float] = None
    injuries: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class PredictionResult:
    model_version: str
    published_at: datetime
    home_win_prob: float
    draw_prob: float
    away_win_prob: float
    confidence: float
    expected_home_goals: float
    expected_away_goals: float
    most_likely_score: str
    most_likely_score_prob: float
    explanation_fr: str
    explanation_en: str
    key_factors: Dict[str, Any]
    uncertainties: Dict[str, Any]
    model_breakdown: Dict[str, Any]
    features_snapshot: Dict[str, Any]
    markets: List[Dict[str, Any]]


def _form_score(form: str) -> float:
    mapping = {"W": 1.0, "D": 0.5, "L": 0.0}
    if not form:
        return 0.5
    vals = [mapping.get(c, 0.5) for c in form.upper()[:5]]
    return sum(vals) / len(vals)


def _injury_impact(injuries: List[Dict[str, Any]]) -> float:
    impact = 0.0
    for inj in injuries:
        if not inj.get("confirmed", True):
            continue
        status = (inj.get("status") or "out").lower()
        if status == "out":
            impact += 0.12
        elif status == "suspended":
            impact += 0.10
        elif status == "doubtful":
            impact += 0.05
    return min(impact, 0.45)


def _attack_defense(team: TeamInput, venue: str) -> tuple[float, float]:
    league_avg = 1.25
    if venue == "home":
        attack = (team.home_gf_avg or team.goals_for_avg) / league_avg
        defense = (team.home_ga_avg or team.goals_against_avg) / league_avg
    else:
        attack = (team.away_gf_avg or team.goals_for_avg) / league_avg
        defense = (team.away_ga_avg or team.goals_against_avg) / league_avg
    if team.xg_for_avg is not None:
        attack = 0.6 * attack + 0.4 * (team.xg_for_avg / league_avg)
    if team.xg_against_avg is not None:
        defense = 0.6 * defense + 0.4 * (team.xg_against_avg / league_avg)
    return max(0.4, attack), max(0.4, defense)


class PredictionEngine:
    def __init__(self, weights: Optional[Dict[str, float]] = None):
        self.weights = weights or DEFAULT_WEIGHTS

    def predict(self, home: TeamInput, away: TeamInput, h2h: Optional[Dict[str, Any]] = None) -> PredictionResult:
        home_att, home_def = _attack_defense(home, "home")
        away_att, away_def = _attack_defense(away, "away")
        lambda_h, lambda_a = estimate_lambdas(home_att, home_def, away_att, away_def)

        # Adjust for rest and injuries
        home_inj = _injury_impact(home.injuries)
        away_inj = _injury_impact(away.injuries)
        rest_adj_h = 0.02 * max(-3, min(3, home.days_rest - away.days_rest))
        lambda_h = max(0.05, lambda_h * (1.0 - 0.35 * home_inj) * (1.0 + rest_adj_h))
        lambda_a = max(0.05, lambda_a * (1.0 - 0.35 * away_inj) * (1.0 - rest_adj_h))

        poisson = poisson_market_bundle(lambda_h, lambda_a)
        elo_h, elo_d, elo_a = elo_outcome_probs(home.elo, away.elo)

        features = {
            "elo_diff": (home.elo - away.elo) / 100.0,
            "form_diff": _form_score(home.form_last5) - _form_score(away.form_last5),
            "gf_avg_diff": home.goals_for_avg - away.goals_for_avg,
            "ga_avg_diff": away.goals_against_avg - home.goals_against_avg,
            "xg_diff": (home.xg_for_avg or home.goals_for_avg) - (away.xg_for_avg or away.goals_for_avg),
            "home_advantage": 1.0,
            "rest_diff": float(home.days_rest - away.days_rest),
            "injury_impact": home_inj - away_inj,
        }
        if h2h:
            features["form_diff"] += 0.05 * float(h2h.get("home_advantage_bias", 0.0))

        log_h, log_d, log_a = logistic_probs(features)
        xgb_h, xgb_d, xgb_a = xgb_probs(features)
        mc = simulate_matches(lambda_h, lambda_a)

        components = {
            "poisson": (poisson["home"], poisson["draw"], poisson["away"]),
            "elo": (elo_h, elo_d, elo_a),
            "logistic": (log_h, log_d, log_a),
            "xgboost": (xgb_h, xgb_d, xgb_a),
            "monte_carlo": (mc["home"], mc["draw"], mc["away"]),
        }
        home_p, draw_p, away_p = weighted_ensemble(components, self.weights)
        home_p, draw_p, away_p = temperature_scale((home_p, draw_p, away_p), temperature=1.12)
        confidence = confidence_from_entropy(home_p, draw_p, away_p)

        # Blend totals / BTTS from Poisson + MC
        over_15 = 0.7 * poisson["over_1_5"] + 0.3 * mc["over_1_5"]
        over_25 = 0.7 * poisson["over_2_5"] + 0.3 * mc["over_2_5"]
        over_35 = 0.7 * poisson["over_3_5"] + 0.3 * mc["over_3_5"]
        btts = 0.7 * poisson["btts_yes"] + 0.3 * mc["btts_yes"]
        ht_h, ht_d, ht_a = ht_result_approx(lambda_h, lambda_a)

        asian_line = round((lambda_h - lambda_a) * 2) / 2  # nearest 0.5
        if asian_line == 0:
            asian_line = -0.25 if home_p > away_p else 0.25

        corners_exp = None
        if home.corners_avg is not None and away.corners_avg is not None:
            corners_exp = 0.55 * home.corners_avg + 0.45 * away.corners_avg
        cards_exp = None
        if home.cards_avg is not None and away.cards_avg is not None:
            cards_exp = 0.5 * (home.cards_avg + away.cards_avg)

        markets = self._build_markets(
            home_p=home_p,
            draw_p=draw_p,
            away_p=away_p,
            over_15=over_15,
            over_25=over_25,
            over_35=over_35,
            btts=btts,
            score=str(poisson["most_likely_score"]),
            score_p=float(poisson["most_likely_score_prob"]),
            ht=(ht_h, ht_d, ht_a),
            asian_line=asian_line,
            corners_exp=corners_exp,
            cards_exp=cards_exp,
            confidence=confidence,
        )

        key_factors = {
            "elo": {"home": home.elo, "away": away.elo, "diff": home.elo - away.elo},
            "expected_goals": {"home": round(lambda_h, 3), "away": round(lambda_a, 3)},
            "form": {"home": home.form_last5, "away": away.form_last5},
            "rest_days": {"home": home.days_rest, "away": away.days_rest},
            "injuries_confirmed": {
                "home": [i for i in home.injuries if i.get("confirmed")],
                "away": [i for i in away.injuries if i.get("confirmed")],
            },
            "xg_available": home.xg_for_avg is not None and away.xg_for_avg is not None,
        }
        uncertainties = {
            "message_fr": "Les probabilités sont estimées et ne garantissent aucun résultat.",
            "message_en": "Probabilities are estimates and do not guarantee any outcome.",
            "factors": [
                "Variance in finishing vs xG",
                "Late injury / lineup changes",
                "Referee and weather effects not fully modeled",
                "Sample size of recent matches",
            ],
            "data_completeness": {
                "xg": home.xg_for_avg is not None,
                "corners": corners_exp is not None,
                "cards": cards_exp is not None,
                "h2h": bool(h2h),
            },
        }

        explanation_fr = self._explain_fr(home, away, home_p, draw_p, away_p, lambda_h, lambda_a, confidence)
        explanation_en = self._explain_en(home, away, home_p, draw_p, away_p, lambda_h, lambda_a, confidence)

        return PredictionResult(
            model_version=MODEL_VERSION,
            published_at=datetime.now(timezone.utc),
            home_win_prob=round(home_p, 4),
            draw_prob=round(draw_p, 4),
            away_win_prob=round(away_p, 4),
            confidence=round(confidence, 4),
            expected_home_goals=round(lambda_h, 3),
            expected_away_goals=round(lambda_a, 3),
            most_likely_score=str(poisson["most_likely_score"]),
            most_likely_score_prob=round(float(poisson["most_likely_score_prob"]), 4),
            explanation_fr=explanation_fr,
            explanation_en=explanation_en,
            key_factors=key_factors,
            uncertainties=uncertainties,
            model_breakdown={
                "weights": self.weights,
                "components": {
                    k: {"home": round(v[0], 4), "draw": round(v[1], 4), "away": round(v[2], 4)}
                    for k, v in components.items()
                },
            },
            features_snapshot=features,
            markets=markets,
        )

    def _build_markets(self, **kw: Any) -> List[Dict[str, Any]]:
        home_p, draw_p, away_p = kw["home_p"], kw["draw_p"], kw["away_p"]
        confidence = kw["confidence"]
        markets: List[Dict[str, Any]] = [
            self._mkt("1x2", "1", home_p, confidence, home_p == max(home_p, draw_p, away_p)),
            self._mkt("1x2", "X", draw_p, confidence * 0.9, draw_p == max(home_p, draw_p, away_p)),
            self._mkt("1x2", "2", away_p, confidence, away_p == max(home_p, draw_p, away_p)),
            self._mkt("double_chance", "1X", home_p + draw_p, confidence, False),
            self._mkt("double_chance", "X2", draw_p + away_p, confidence, False),
            self._mkt("double_chance", "12", home_p + away_p, confidence, False),
            self._mkt("ou_1_5", "Over", kw["over_15"], confidence, kw["over_15"] >= 0.55),
            self._mkt("ou_1_5", "Under", 1 - kw["over_15"], confidence, kw["over_15"] < 0.45),
            self._mkt("ou_2_5", "Over", kw["over_25"], confidence, kw["over_25"] >= 0.55),
            self._mkt("ou_2_5", "Under", 1 - kw["over_25"], confidence, kw["over_25"] < 0.45),
            self._mkt("ou_3_5", "Over", kw["over_35"], confidence * 0.85, kw["over_35"] >= 0.55),
            self._mkt("ou_3_5", "Under", 1 - kw["over_35"], confidence * 0.85, kw["over_35"] < 0.45),
            self._mkt("btts", "Yes", kw["btts"], confidence, kw["btts"] >= 0.55),
            self._mkt("btts", "No", 1 - kw["btts"], confidence, kw["btts"] < 0.45),
            self._mkt("exact_score", kw["score"], kw["score_p"], confidence * 0.7, True),
            self._mkt("ht_result", "1", kw["ht"][0], confidence * 0.8, False),
            self._mkt("ht_result", "X", kw["ht"][1], confidence * 0.8, False),
            self._mkt("ht_result", "2", kw["ht"][2], confidence * 0.8, False),
            self._mkt(
                "asian_handicap",
                f"Home {kw['asian_line']:+}",
                home_p,
                confidence * 0.75,
                False,
                rationale=f"Line derived from expected goal difference ({kw['asian_line']:+})",
            ),
        ]
        if kw["corners_exp"] is not None:
            markets.append(
                self._mkt(
                    "corners",
                    f"Over {kw['corners_exp']:.1f}",
                    0.52,
                    confidence * 0.6,
                    False,
                    rationale="Based on rolling corner averages when available",
                )
            )
        if kw["cards_exp"] is not None:
            markets.append(
                self._mkt(
                    "cards",
                    f"Over {kw['cards_exp']:.1f}",
                    0.50,
                    confidence * 0.55,
                    False,
                    rationale="Based on rolling card averages when available",
                )
            )
        return markets

    @staticmethod
    def _mkt(
        market: str,
        selection: str,
        probability: float,
        confidence: float,
        recommended: bool,
        rationale: Optional[str] = None,
    ) -> Dict[str, Any]:
        return {
            "market": market,
            "selection": selection,
            "probability": round(float(probability), 4),
            "confidence": round(float(min(confidence, 0.92)), 4),
            "recommended": recommended and probability >= 0.5,
            "rationale": rationale,
        }

    @staticmethod
    def _explain_fr(home, away, h, d, a, lh, la, conf) -> str:
        tip = "domicile" if h >= max(d, a) else ("nul" if d >= a else "extérieur")
        return (
            f"Analyse estimée pour {home.name} vs {away.name}. "
            f"Probabilités calibrées : 1={h:.0%}, X={d:.0%}, 2={a:.0%}. "
            f"Buts attendus : {lh:.2f} – {la:.2f}. "
            f"Scénario le plus probable selon le modèle : {tip}. "
            f"Indice de confiance calibré : {conf:.0%}. "
            f"Ceci est une estimation statistique, jamais une certitude."
        )

    @staticmethod
    def _explain_en(home, away, h, d, a, lh, la, conf) -> str:
        tip = "home" if h >= max(d, a) else ("draw" if d >= a else "away")
        return (
            f"Estimated analysis for {home.name} vs {away.name}. "
            f"Calibrated probabilities: 1={h:.0%}, X={d:.0%}, 2={a:.0%}. "
            f"Expected goals: {lh:.2f} – {la:.2f}. "
            f"Most likely model scenario: {tip}. "
            f"Calibrated confidence index: {conf:.0%}. "
            f"This is a statistical estimate, never a certainty."
        )
