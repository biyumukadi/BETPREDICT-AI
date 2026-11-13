"""football-data.org adapter — activated when FOOTBALL_DATA_ORG_KEY is set."""

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


class FootballDataOrgProvider(SportsDataProvider):
    name = "football_data_org"

    def __init__(self) -> None:
        settings = get_settings()
        self.base_url = settings.football_data_org_base_url.rstrip("/")
        self.api_key = settings.football_data_org_key
        if not self.api_key:
            raise RuntimeError("FOOTBALL_DATA_ORG_KEY is required")

    def _headers(self) -> dict:
        return {"X-Auth-Token": self.api_key}

    async def fetch_competitions(self) -> List[ProviderCompetition]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(f"{self.base_url}/competitions", headers=self._headers())
            resp.raise_for_status()
            data = resp.json().get("competitions", [])
        return [
            ProviderCompetition(
                external_id=str(item["id"]),
                name=item.get("name", "Unknown"),
                country=(item.get("area") or {}).get("name", "Unknown"),
                code=item.get("code"),
            )
            for item in data
        ]

    async def fetch_teams(self, competition_external_id: str) -> List[ProviderTeam]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(
                f"{self.base_url}/competitions/{competition_external_id}/teams",
                headers=self._headers(),
            )
            resp.raise_for_status()
            data = resp.json().get("teams", [])
        return [
            ProviderTeam(
                external_id=str(t["id"]),
                name=t["name"],
                country=(t.get("area") or {}).get("name", "Unknown"),
                short_name=t.get("tla") or t.get("shortName"),
                competition_external_id=competition_external_id,
                logo_url=t.get("crest"),
            )
            for t in data
        ]

    async def fetch_fixtures(
        self,
        date_from: datetime,
        date_to: datetime,
        competition_external_id: Optional[str] = None,
    ) -> List[ProviderFixture]:
        params = {
            "dateFrom": date_from.strftime("%Y-%m-%d"),
            "dateTo": date_to.strftime("%Y-%m-%d"),
        }
        url = f"{self.base_url}/matches"
        if competition_external_id:
            url = f"{self.base_url}/competitions/{competition_external_id}/matches"
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(url, headers=self._headers(), params=params)
            resp.raise_for_status()
            data = resp.json().get("matches", [])
        fixtures: List[ProviderFixture] = []
        for m in data:
            status_map = {
                "SCHEDULED": "scheduled",
                "TIMED": "scheduled",
                "IN_PLAY": "live",
                "PAUSED": "live",
                "FINISHED": "finished",
                "POSTPONED": "postponed",
                "CANCELLED": "cancelled",
            }
            score = m.get("score") or {}
            full = score.get("fullTime") or {}
            half = score.get("halfTime") or {}
            fixtures.append(
                ProviderFixture(
                    external_id=str(m["id"]),
                    competition_external_id=str((m.get("competition") or {}).get("id") or competition_external_id),
                    home_team_external_id=str(m["homeTeam"]["id"]),
                    away_team_external_id=str(m["awayTeam"]["id"]),
                    kickoff_at=datetime.fromisoformat(m["utcDate"].replace("Z", "+00:00")),
                    status=status_map.get(m.get("status"), "scheduled"),
                    matchday=m.get("matchday"),
                    home_score=full.get("home"),
                    away_score=full.get("away"),
                    home_score_ht=half.get("home"),
                    away_score_ht=half.get("away"),
                    raw={"provider": "football_data_org"},
                )
            )
        return fixtures
