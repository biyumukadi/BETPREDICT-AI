"""API-Football adapter — used only when API_FOOTBALL_KEY is configured."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

import httpx

from app.core.config import get_settings
from app.services.data_providers.base import (
    ProviderCompetition,
    ProviderFixture,
    ProviderTeam,
    SportsDataProvider,
)


class ApiFootballProvider(SportsDataProvider):
    name = "api_football"

    def __init__(self) -> None:
        settings = get_settings()
        self.base_url = settings.api_football_base_url.rstrip("/")
        self.api_key = settings.api_football_key
        if not self.api_key:
            raise RuntimeError("API_FOOTBALL_KEY is required for ApiFootballProvider")

    def _headers(self) -> dict:
        return {"x-apisports-key": self.api_key}

    async def fetch_competitions(self) -> List[ProviderCompetition]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(f"{self.base_url}/leagues", headers=self._headers(), params={"current": "true"})
            resp.raise_for_status()
            data = resp.json().get("response", [])
        out: List[ProviderCompetition] = []
        for item in data[:50]:
            league = item.get("league", {})
            country = item.get("country", {})
            season = str((item.get("seasons") or [{}])[-1].get("year", ""))
            out.append(
                ProviderCompetition(
                    external_id=str(league.get("id")),
                    name=league.get("name", "Unknown"),
                    country=country.get("name", "Unknown"),
                    code=league.get("name", "")[:8],
                    season=season,
                    logo_url=league.get("logo"),
                )
            )
        return out

    async def fetch_teams(self, competition_external_id: str) -> List[ProviderTeam]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(
                f"{self.base_url}/teams",
                headers=self._headers(),
                params={"league": competition_external_id, "season": datetime.utcnow().year},
            )
            resp.raise_for_status()
            data = resp.json().get("response", [])
        return [
            ProviderTeam(
                external_id=str(t["team"]["id"]),
                name=t["team"]["name"],
                country=t["team"].get("country") or "Unknown",
                short_name=t["team"].get("code"),
                competition_external_id=competition_external_id,
                logo_url=t["team"].get("logo"),
            )
            for t in data
        ]

    async def fetch_fixtures(
        self,
        date_from: datetime,
        date_to: datetime,
        competition_external_id: Optional[str] = None,
    ) -> List[ProviderFixture]:
        params: dict = {
            "from": date_from.strftime("%Y-%m-%d"),
            "to": date_to.strftime("%Y-%m-%d"),
        }
        if competition_external_id:
            params["league"] = competition_external_id
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(f"{self.base_url}/fixtures", headers=self._headers(), params=params)
            resp.raise_for_status()
            data = resp.json().get("response", [])
        fixtures: List[ProviderFixture] = []
        for item in data:
            fx = item.get("fixture", {})
            league = item.get("league", {})
            teams = item.get("teams", {})
            goals = item.get("goals", {})
            score = item.get("score", {})
            status_short = (fx.get("status") or {}).get("short", "NS")
            status = {
                "NS": "scheduled",
                "TBD": "scheduled",
                "1H": "live",
                "2H": "live",
                "HT": "live",
                "FT": "finished",
                "AET": "finished",
                "PEN": "finished",
                "PST": "postponed",
                "CANC": "cancelled",
            }.get(status_short, "scheduled")
            kickoff = datetime.fromisoformat(fx["date"].replace("Z", "+00:00"))
            fixtures.append(
                ProviderFixture(
                    external_id=str(fx["id"]),
                    competition_external_id=str(league.get("id")),
                    home_team_external_id=str(teams["home"]["id"]),
                    away_team_external_id=str(teams["away"]["id"]),
                    kickoff_at=kickoff,
                    status=status,
                    matchday=league.get("round"),
                    venue=(fx.get("venue") or {}).get("name"),
                    home_score=goals.get("home"),
                    away_score=goals.get("away"),
                    home_score_ht=(score.get("halftime") or {}).get("home"),
                    away_score_ht=(score.get("halftime") or {}).get("away"),
                    raw={"provider": "api_football"},
                )
            )
        return fixtures
