"""Interchangeable sports data provider adapters."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class ProviderCompetition:
    external_id: str
    name: str
    country: str
    code: Optional[str] = None
    season: str = "2025-2026"
    logo_url: Optional[str] = None


@dataclass
class ProviderTeam:
    external_id: str
    name: str
    country: str
    short_name: Optional[str] = None
    competition_external_id: Optional[str] = None
    elo_rating: float = 1500.0
    logo_url: Optional[str] = None


@dataclass
class ProviderFixture:
    external_id: str
    competition_external_id: str
    home_team_external_id: str
    away_team_external_id: str
    kickoff_at: datetime
    status: str = "scheduled"
    matchday: Optional[int] = None
    venue: Optional[str] = None
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    home_score_ht: Optional[int] = None
    away_score_ht: Optional[int] = None
    home_xg: Optional[float] = None
    away_xg: Optional[float] = None
    raw: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProviderOdds:
    fixture_external_id: str
    bookmaker: str
    market: str
    selection: str
    odds_decimal: float
    captured_at: datetime
    source_licensed: bool = False


class SportsDataProvider(ABC):
    name: str = "base"

    @abstractmethod
    async def fetch_competitions(self) -> List[ProviderCompetition]:
        raise NotImplementedError

    @abstractmethod
    async def fetch_teams(self, competition_external_id: str) -> List[ProviderTeam]:
        raise NotImplementedError

    @abstractmethod
    async def fetch_fixtures(
        self,
        date_from: datetime,
        date_to: datetime,
        competition_external_id: Optional[str] = None,
    ) -> List[ProviderFixture]:
        raise NotImplementedError

    async def fetch_odds(self, fixture_external_id: str) -> List[ProviderOdds]:
        return []

    async def healthcheck(self) -> Dict[str, Any]:
        return {"provider": self.name, "ok": True}
