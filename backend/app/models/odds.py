"""Odds snapshots and value-bet detection."""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class OddsSnapshot(Base, TimestampMixin):
    __tablename__ = "odds_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    fixture_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("fixtures.id"), index=True)
    bookmaker: Mapped[str] = mapped_column(String(100), nullable=False)
    market: Mapped[str] = mapped_column(String(40), nullable=False)
    selection: Mapped[str] = mapped_column(String(40), nullable=False)
    odds_decimal: Mapped[float] = mapped_column(Float, nullable=False)
    implied_probability: Mapped[float] = mapped_column(Float, nullable=False)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)
    source_licensed: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class ValueBet(Base, TimestampMixin):
    __tablename__ = "value_bets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    fixture_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("fixtures.id"), index=True)
    prediction_market_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("prediction_markets.id"), nullable=True
    )
    bookmaker: Mapped[str] = mapped_column(String(100), nullable=False)
    market: Mapped[str] = mapped_column(String(40), nullable=False)
    selection: Mapped[str] = mapped_column(String(40), nullable=False)
    model_probability: Mapped[float] = mapped_column(Float, nullable=False)
    odds_decimal: Mapped[float] = mapped_column(Float, nullable=False)
    implied_probability: Mapped[float] = mapped_column(Float, nullable=False)
    expected_value: Mapped[float] = mapped_column(Float, nullable=False)
    bookmaker_margin: Mapped[float] = mapped_column(Float, nullable=False)
    disclaimer: Mapped[str] = mapped_column(
        Text,
        default="Une valeur attendue positive estimée ne garantit aucun gain réel.",
    )
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)
