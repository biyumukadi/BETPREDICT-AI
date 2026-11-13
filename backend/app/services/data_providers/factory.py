"""Provider factory — picks licensed adapter or falls back to demo."""

from __future__ import annotations

from app.core.config import get_settings
from app.services.data_providers.base import SportsDataProvider
from app.services.data_providers.demo import DemoProvider


def get_provider() -> SportsDataProvider:
    settings = get_settings()
    if settings.is_demo or settings.primary_data_provider == "demo":
        return DemoProvider()

    provider = settings.primary_data_provider.lower()
    if provider == "api_football" and settings.api_football_key:
        from app.services.data_providers.api_football import ApiFootballProvider

        return ApiFootballProvider()
    if provider == "sportmonks" and settings.sportmonks_token:
        from app.services.data_providers.sportmonks import SportmonksProvider

        return SportmonksProvider()
    if provider == "football_data_org" and settings.football_data_org_key:
        from app.services.data_providers.football_data_org import FootballDataOrgProvider

        return FootballDataOrgProvider()
    return DemoProvider()
