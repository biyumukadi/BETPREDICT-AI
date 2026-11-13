"""
Deterministic DEMO data provider.

All fixtures, stats and odds are synthetic and clearly flagged as demo.
They are generated from seeded statistical parameters — not presented as live results.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from app.services.data_providers.base import (
    ProviderCompetition,
    ProviderFixture,
    ProviderOdds,
    ProviderTeam,
    SportsDataProvider,
)

COMPETITIONS = [
    ProviderCompetition("demo-l1", "Ligue 1", "France", "FL1", "2025-2026"),
    ProviderCompetition("demo-pl", "Premier League", "England", "PL", "2025-2026"),
    ProviderCompetition("demo-ll", "La Liga", "Spain", "PD", "2025-2026"),
    ProviderCompetition("demo-sa", "Serie A", "Italy", "SA", "2025-2026"),
    ProviderCompetition("demo-bl", "Bundesliga", "Germany", "BL1", "2025-2026"),
]

TEAMS: Dict[str, List[ProviderTeam]] = {
    "demo-l1": [
        ProviderTeam("demo-psg", "Paris Saint-Germain", "France", "PSG", "demo-l1", 1785),
        ProviderTeam("demo-om", "Olympique de Marseille", "France", "OM", "demo-l1", 1640),
        ProviderTeam("demo-ol", "Olympique Lyonnais", "France", "OL", "demo-l1", 1580),
        ProviderTeam("demo-asm", "AS Monaco", "France", "ASM", "demo-l1", 1625),
        ProviderTeam("demo-rcl", "RC Lens", "France", "RCL", "demo-l1", 1555),
        ProviderTeam("demo-loscm", "Lille OSC", "France", "LOSC", "demo-l1", 1600),
    ],
    "demo-pl": [
        ProviderTeam("demo-mci", "Manchester City", "England", "MCI", "demo-pl", 1850),
        ProviderTeam("demo-liv", "Liverpool", "England", "LIV", "demo-pl", 1820),
        ProviderTeam("demo-ars", "Arsenal", "England", "ARS", "demo-pl", 1805),
        ProviderTeam("demo-che", "Chelsea", "England", "CHE", "demo-pl", 1680),
        ProviderTeam("demo-tot", "Tottenham", "England", "TOT", "demo-pl", 1660),
        ProviderTeam("demo-new", "Newcastle", "England", "NEW", "demo-pl", 1675),
    ],
    "demo-ll": [
        ProviderTeam("demo-rma", "Real Madrid", "Spain", "RMA", "demo-ll", 1840),
        ProviderTeam("demo-bar", "FC Barcelona", "Spain", "BAR", "demo-ll", 1810),
        ProviderTeam("demo-atm", "Atlético Madrid", "Spain", "ATM", "demo-ll", 1720),
        ProviderTeam("demo-sev", "Sevilla", "Spain", "SEV", "demo-ll", 1580),
    ],
    "demo-sa": [
        ProviderTeam("demo-int", "Inter", "Italy", "INT", "demo-sa", 1780),
        ProviderTeam("demo-juv", "Juventus", "Italy", "JUV", "demo-sa", 1725),
        ProviderTeam("demo-mil", "AC Milan", "Italy", "MIL", "demo-sa", 1710),
        ProviderTeam("demo-nap", "Napoli", "Italy", "NAP", "demo-sa", 1700),
    ],
    "demo-bl": [
        ProviderTeam("demo-bay", "Bayern Munich", "Germany", "BAY", "demo-bl", 1835),
        ProviderTeam("demo-bvb", "Borussia Dortmund", "Germany", "BVB", "demo-bl", 1720),
        ProviderTeam("demo-rbl", "RB Leipzig", "Germany", "RBL", "demo-bl", 1685),
        ProviderTeam("demo-bmg", "Borussia M'gladbach", "Germany", "BMG", "demo-bl", 1560),
    ],
}


class DemoProvider(SportsDataProvider):
    name = "demo"

    async def fetch_competitions(self) -> List[ProviderCompetition]:
        return list(COMPETITIONS)

    async def fetch_teams(self, competition_external_id: str) -> List[ProviderTeam]:
        return list(TEAMS.get(competition_external_id, []))

    async def fetch_fixtures(
        self,
        date_from: datetime,
        date_to: datetime,
        competition_external_id: Optional[str] = None,
    ) -> List[ProviderFixture]:
        now = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        fixtures: List[ProviderFixture] = []
        comps = [c for c in COMPETITIONS if competition_external_id in (None, c.external_id)]
        idx = 0
        for day_offset in range(-3, 8):  # finished + upcoming week
            day = now + timedelta(days=day_offset)
            for comp in comps:
                teams = TEAMS[comp.external_id]
                if len(teams) < 2:
                    continue
                home = teams[idx % len(teams)]
                away = teams[(idx + 1) % len(teams)]
                if home.external_id == away.external_id:
                    away = teams[(idx + 2) % len(teams)]
                kickoff = day.replace(hour=18 + (idx % 3), minute=0, tzinfo=timezone.utc)
                status = "finished" if day_offset < 0 else "scheduled"
                home_score = away_score = None
                home_ht = away_ht = None
                home_xg = away_xg = None
                if status == "finished":
                    # Deterministic pseudo-result from Elo gap (demo only)
                    gap = (home.elo_rating - away.elo_rating) / 200.0
                    home_score = max(0, int(1 + (gap > 0) + (idx % 2)))
                    away_score = max(0, int(1 + (gap < 0) + ((idx + 1) % 2) - (1 if gap > 0.5 else 0)))
                    home_ht = home_score // 2
                    away_ht = away_score // 2
                    home_xg = round(home_score + 0.3 - 0.1 * (idx % 3), 2)
                    away_xg = round(away_score + 0.2 + 0.1 * (idx % 2), 2)
                if date_from <= kickoff <= date_to:
                    fixtures.append(
                        ProviderFixture(
                            external_id=f"demo-fx-{comp.code}-{day_offset}-{idx}",
                            competition_external_id=comp.external_id,
                            home_team_external_id=home.external_id,
                            away_team_external_id=away.external_id,
                            kickoff_at=kickoff,
                            status=status,
                            matchday=max(1, 10 + day_offset),
                            venue=f"Stadium {home.short_name or home.name}",
                            home_score=home_score,
                            away_score=away_score,
                            home_score_ht=home_ht,
                            away_score_ht=away_ht,
                            home_xg=home_xg,
                            away_xg=away_xg,
                            raw={"demo": True, "disclaimer": "DEMO DATA — not live sports data"},
                        )
                    )
                idx += 1
        return fixtures

    async def fetch_odds(self, fixture_external_id: str) -> List[ProviderOdds]:
        """Synthetic licensed-demo odds derived from a simple prior — labeled as demo."""
        now = datetime.now(timezone.utc)
        # Stable pseudo odds from fixture id hash
        seed = sum(ord(c) for c in fixture_external_id) % 50
        home = round(1.70 + seed / 100.0, 2)
        draw = round(3.40 + (seed % 10) / 50.0, 2)
        away = round(4.20 - seed / 120.0, 2)
        bookmakers = ["DemoBook A", "DemoBook B"]
        out: List[ProviderOdds] = []
        for bm in bookmakers:
            for sel, odds in (("1", home), ("X", draw), ("2", away)):
                out.append(
                    ProviderOdds(
                        fixture_external_id=fixture_external_id,
                        bookmaker=bm,
                        market="1x2",
                        selection=sel,
                        odds_decimal=odds * (1.0 + (0.01 if bm.endswith("B") else 0.0)),
                        captured_at=now,
                        source_licensed=False,
                    )
                )
        return out
