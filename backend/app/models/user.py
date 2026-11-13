"""User, roles and subscription models."""

import enum
import uuid
from datetime import date, datetime
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class UserRole(str, enum.Enum):
    USER = "user"
    PREMIUM = "premium"
    PRO = "pro"
    ADMIN = "admin"
    ANALYST = "analyst"


class SubscriptionPlan(str, enum.Enum):
    FREE = "free"
    PREMIUM = "premium"
    PRO = "pro"


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.USER, nullable=False)
    locale: Mapped[str] = mapped_column(String(8), default="fr", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    mfa_secret: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=False)
    age_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    self_excluded_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    pause_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    daily_analysis_count: Mapped[int] = mapped_column(default=0, nullable=False)
    daily_analysis_reset: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    stripe_customer_id: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)

    subscription: Mapped[Optional["Subscription"]] = relationship(back_populates="user", uselist=False)
    budget_profile: Mapped[Optional["BudgetProfile"]] = relationship(back_populates="user", uselist=False)


class Subscription(Base, TimestampMixin):
    __tablename__ = "subscriptions"
    __table_args__ = (UniqueConstraint("user_id", name="uq_subscription_user"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    plan: Mapped[SubscriptionPlan] = mapped_column(Enum(SubscriptionPlan), default=SubscriptionPlan.FREE)
    status: Mapped[str] = mapped_column(String(40), default="active")
    stripe_subscription_id: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    payment_provider: Mapped[str] = mapped_column(String(40), default="none")
    current_period_end: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    user: Mapped["User"] = relationship(back_populates="subscription")


# Late imports for type hints
from app.models.budget import BudgetProfile  # noqa: E402
