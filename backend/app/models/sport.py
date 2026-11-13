"""Sport domain models: competitions, teams, fixtures, stats."""

import enum
import uuid
from datetime import date, datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class FixtureStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    LIVE = "live"
    FINISHED = "finished"
    POSTPONED = "postponed"
    CANCELLED = "cancelled"


class Competition(Base, TimestampMixin):
    __tablename__ = "competitions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    external_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    provider: Mapped[str] = mapped_column(String(40), default="demo", nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    country: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    season: Mapped[str] = mapped_column(String(20), default="2025-2026")
    logo_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    teams: Mapped[list["Team"]] = relationship(back_populates="competition")
    fixtures: Mapped[list["Fixture"]] = relationship(back_populates="competition")


class Team(Base, TimestampMixin):
    __tablename__ = "teams"
    __table_args__ = (UniqueConstraint("provider", "external_id", name="uq_team_provider_ext"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    external_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    provider: Mapped[str] = mapped_column(String(40), default="demo", nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    short_name: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    country: Mapped[str] = mapped_column(String(100), nullable=False)
    competition_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("competitions.id"), nullable=True
    )
    elo_rating: Mapped[float] = mapped_column(Float, default=1500.0)
    logo_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    competition: Mapped[Optional["Competition"]] = relationship(back_populates="teams")
    stats: Mapped[list["TeamStats"]] = relationship(back_populates="team")
    injuries: Mapped[list["Injury"]] = relationship(back_populates="team")


class Fixture(Base, TimestampMixin):
    __tablename__ = "fixtures"
    __table_args__ = (UniqueConstraint("provider", "external_id", name="uq_fixture_provider_ext"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    external_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    provider: Mapped[str] = mapped_column(String(40), default="demo", nullable=False)
    competition_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("competitions.id"))
    home_team_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("teams.id"))
    away_team_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("teams.id"))
    kickoff_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    status: Mapped[FixtureStatus] = mapped_column(Enum(FixtureStatus), default=FixtureStatus.SCHEDULED)
    matchday: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    venue: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    home_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    away_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    home_score_ht: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    away_score_ht: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    home_xg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    away_xg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    raw_payload: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    competition: Mapped["Competition"] = relationship(back_populates="fixtures")
    home_team: Mapped["Team"] = relationship(foreign_keys=[home_team_id])
    away_team: Mapped["Team"] = relationship(foreign_keys=[away_team_id])
    predictions: Mapped[list["Prediction"]] = relationship(back_populates="fixture")


class TeamStats(Base, TimestampMixin):
    """Rolling/historical team statistics — never include future match data."""

    __tablename__ = "team_stats"
    __table_args__ = (UniqueConstraint("team_id", "as_of_date", name="uq_team_stats_date"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False)
    as_of_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    matches_played: Mapped[int] = mapped_column(Integer, default=0)
    wins: Mapped[int] = mapped_column(Integer, default=0)
    draws: Mapped[int] = mapped_column(Integer, default=0)
    losses: Mapped[int] = mapped_column(Integer, default=0)
    goals_for: Mapped[int] = mapped_column(Integer, default=0)
    goals_against: Mapped[int] = mapped_column(Integer, default=0)
    goals_for_avg: Mapped[float] = mapped_column(Float, default=0.0)
    goals_against_avg: Mapped[float] = mapped_column(Float, default=0.0)
    xg_for_avg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    xg_against_avg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    home_goals_for_avg: Mapped[float] = mapped_column(Float, default=0.0)
    home_goals_against_avg: Mapped[float] = mapped_column(Float, default=0.0)
    away_goals_for_avg: Mapped[float] = mapped_column(Float, default=0.0)
    away_goals_against_avg: Mapped[float] = mapped_column(Float, default=0.0)
    form_last5: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    corners_avg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    cards_avg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    days_rest: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)

    team: Mapped["Team"] = relationship(back_populates="stats")


class Injury(Base, TimestampMixin):
    __tablename__ = "injuries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False)
    player_name: Mapped[str] = mapped_column(String(200), nullable=False)
    reason: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="out")  # out | doubtful | suspended
    expected_return: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    confirmed: Mapped[bool] = mapped_column(Boolean, default=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    team: Mapped["Team"] = relationship(back_populates="injuries")


from app.models.prediction import Prediction  # noqa: E402
