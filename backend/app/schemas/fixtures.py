from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel


class TeamBrief(BaseModel):
    id: UUID
    name: str
    short_name: Optional[str] = None
    elo_rating: float
    country: str


class CompetitionOut(BaseModel):
    id: UUID
    name: str
    country: str
    code: Optional[str] = None
    season: str


class MarketOut(BaseModel):
    market: str
    selection: str
    probability: float
    confidence: float
    recommended: bool
    odds_decimal: Optional[float] = None
    expected_value: Optional[float] = None
    rationale: Optional[str] = None


class PredictionOut(BaseModel):
    id: UUID
    model_version: str
    published_at: datetime
    is_demo: bool
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
    markets: List[MarketOut] = []


class FixtureOut(BaseModel):
    id: UUID
    kickoff_at: datetime
    status: str
    venue: Optional[str] = None
    matchday: Optional[int] = None
    is_demo: bool
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    home_xg: Optional[float] = None
    away_xg: Optional[float] = None
    competition: CompetitionOut
    home_team: TeamBrief
    away_team: TeamBrief
    prediction: Optional[PredictionOut] = None


class FixtureDetailOut(FixtureOut):
    home_score_ht: Optional[int] = None
    away_score_ht: Optional[int] = None
    odds: List[Dict[str, Any]] = []
    value_bets: List[Dict[str, Any]] = []
    injuries: Dict[str, List[Dict[str, Any]]] = {}
    team_comparison: Dict[str, Any] = {}


class DashboardOut(BaseModel):
    demo_mode: bool
    disclaimer_fr: str
    disclaimer_en: str
    today: List[FixtureOut]
    tomorrow: List[FixtureOut]
    next_7_days: List[FixtureOut]
    finished: List[FixtureOut]
    competitions: List[CompetitionOut]
