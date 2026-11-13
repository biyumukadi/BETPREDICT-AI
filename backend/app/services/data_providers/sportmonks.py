"""Sportmonks adapter stub — activated when SPORTMONKS_TOKEN is set."""

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


class SportmonksProvider(SportsDataProvider):
    name = "sportmonks"

    def __init__(self) -> None:
        settings = get_settings()
        self.base_url = settings.sportmonks_base_url.rstrip("/")
        self.token = settings.sportmonks_token
        if not self.token:
            raise RuntimeError("SPORTMONKS_TOKEN is required")

    async def fetch_competitions(self) -> List[ProviderCompetition]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(f"{self.base_url}/leagues", params={"api_token": self.token})
            resp.raise_for_status()
            data = resp.json().get("data", [])
        return [
            ProviderCompetition(
                external_id=str(item["id"]),
                name=item.get("name", "Unknown"),
                country=str((item.get("country") or {}).get("name") or "Unknown"),
                code=item.get("short_code"),
            )
            for item in data[:50]
        ]

    async def fetch_teams(self, competition_external_id: str) -> List[ProviderTeam]:
        return []

    async def fetch_fixtures(
        self,
        date_from: datetime,
        date_to: datetime,
        competition_external_id: Optional[str] = None,
    ) -> List[ProviderFixture]:
        return []
