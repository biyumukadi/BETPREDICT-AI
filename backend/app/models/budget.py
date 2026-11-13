"""Responsible gambling budget and stake tracking."""

import uuid
from datetime import date, datetime
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class BudgetProfile(Base, TimestampMixin):
    __tablename__ = "budget_profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True)
    currency: Mapped[str] = mapped_column(String(8), default="EUR")
    max_budget: Mapped[float] = mapped_column(Float, default=100.0)
    daily_loss_limit: Mapped[float] = mapped_column(Float, default=20.0)
    weekly_loss_limit: Mapped[float] = mapped_column(Float, default=50.0)
    monthly_loss_limit: Mapped[float] = mapped_column(Float, default=150.0)
    total_staked: Mapped[float] = mapped_column(Float, default=0.0)
    total_returned: Mapped[float] = mapped_column(Float, default=0.0)
    notifications_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    alerts_muted: Mapped[bool] = mapped_column(Boolean, default=False)

    user: Mapped["User"] = relationship(back_populates="budget_profile")
    decisions: Mapped[list["StakeDecision"]] = relationship(back_populates="budget_profile")

    @property
    def roi(self) -> float:
        if self.total_staked <= 0:
            return 0.0
        return (self.total_returned - self.total_staked) / self.total_staked


class StakeDecision(Base, TimestampMixin):
    """User decision log — informational only; app never holds player funds."""

    __tablename__ = "stake_decisions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    budget_profile_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("budget_profiles.id"))
    fixture_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("fixtures.id"), nullable=True)
    decision_date: Mapped[date] = mapped_column(Date, nullable=False)
    market: Mapped[str] = mapped_column(String(40), nullable=False)
    selection: Mapped[str] = mapped_column(String(40), nullable=False)
    stake_amount: Mapped[float] = mapped_column(Float, nullable=False)
    odds_decimal: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    returned_amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    result: Mapped[str] = mapped_column(String(20), default="pending")  # pending|won|lost|void
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    settled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    budget_profile: Mapped["BudgetProfile"] = relationship(back_populates="decisions")


from app.models.user import User  # noqa: E402
