"""Prediction and evaluation models."""

import enum
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class MarketType(str, enum.Enum):
    MATCH_RESULT = "1x2"
    DOUBLE_CHANCE = "double_chance"
    OVER_UNDER_15 = "ou_1_5"
    OVER_UNDER_25 = "ou_2_5"
    OVER_UNDER_35 = "ou_3_5"
    BTTS = "btts"
    EXACT_SCORE = "exact_score"
    HT_RESULT = "ht_result"
    CORNERS = "corners"
    CARDS = "cards"
    ASIAN_HANDICAP = "asian_handicap"


class Prediction(Base, TimestampMixin):
    """One prediction run for a fixture — published before kickoff."""

    __tablename__ = "predictions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    fixture_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("fixtures.id"), index=True)
    model_version: Mapped[str] = mapped_column(String(64), nullable=False)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    home_win_prob: Mapped[float] = mapped_column(Float, nullable=False)
    draw_prob: Mapped[float] = mapped_column(Float, nullable=False)
    away_win_prob: Mapped[float] = mapped_column(Float, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    expected_home_goals: Mapped[float] = mapped_column(Float, nullable=False)
    expected_away_goals: Mapped[float] = mapped_column(Float, nullable=False)
    most_likely_score: Mapped[str] = mapped_column(String(10), nullable=False)
    most_likely_score_prob: Mapped[float] = mapped_column(Float, nullable=False)
    explanation_fr: Mapped[str] = mapped_column(Text, nullable=False)
    explanation_en: Mapped[str] = mapped_column(Text, nullable=False)
    key_factors: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    uncertainties: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    model_breakdown: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    features_snapshot: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    fixture: Mapped["Fixture"] = relationship(back_populates="predictions")
    markets: Mapped[list["PredictionMarket"]] = relationship(back_populates="prediction", cascade="all, delete-orphan")
    evaluation: Mapped[Optional["PredictionEvaluation"]] = relationship(
        back_populates="prediction", uselist=False, cascade="all, delete-orphan"
    )


class PredictionMarket(Base, TimestampMixin):
    __tablename__ = "prediction_markets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    prediction_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("predictions.id"), index=True)
    market: Mapped[MarketType] = mapped_column(Enum(MarketType), nullable=False)
    selection: Mapped[str] = mapped_column(String(40), nullable=False)
    probability: Mapped[float] = mapped_column(Float, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    recommended: Mapped[bool] = mapped_column(Boolean, default=False)
    odds_decimal: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    expected_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    rationale: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    prediction: Mapped["Prediction"] = relationship(back_populates="markets")


class PredictionEvaluation(Base, TimestampMixin):
    """Immutable evaluation after match finishes — incorrect predictions cannot be deleted selectively."""

    __tablename__ = "prediction_evaluations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    prediction_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("predictions.id"), unique=True, nullable=False
    )
    evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    actual_home_score: Mapped[int] = mapped_column(Integer, nullable=False)
    actual_away_score: Mapped[int] = mapped_column(Integer, nullable=False)
    result_1x2_correct: Mapped[bool] = mapped_column(Boolean, nullable=False)
    brier_score_1x2: Mapped[float] = mapped_column(Float, nullable=False)
    log_loss_1x2: Mapped[float] = mapped_column(Float, nullable=False)
    market_results: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    theoretical_roi: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    locked: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    prediction: Mapped["Prediction"] = relationship(back_populates="evaluation")


from app.models.sport import Fixture  # noqa: E402
