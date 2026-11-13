from datetime import date
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class BudgetProfileOut(BaseModel):
    id: UUID
    currency: str
    max_budget: float
    daily_loss_limit: float
    weekly_loss_limit: float
    monthly_loss_limit: float
    total_staked: float
    total_returned: float
    roi: float
    notifications_enabled: bool
    alerts_muted: bool


class BudgetUpdate(BaseModel):
    max_budget: Optional[float] = Field(default=None, ge=0)
    daily_loss_limit: Optional[float] = Field(default=None, ge=0)
    weekly_loss_limit: Optional[float] = Field(default=None, ge=0)
    monthly_loss_limit: Optional[float] = Field(default=None, ge=0)
    notifications_enabled: Optional[bool] = None
    alerts_muted: Optional[bool] = None
    currency: Optional[str] = None


class StakeCreate(BaseModel):
    fixture_id: Optional[UUID] = None
    market: str
    selection: str
    stake_amount: float = Field(gt=0)
    odds_decimal: Optional[float] = Field(default=None, gt=1.0)
    notes: Optional[str] = None


class StakeOut(BaseModel):
    id: UUID
    decision_date: date
    market: str
    selection: str
    stake_amount: float
    odds_decimal: Optional[float]
    returned_amount: Optional[float]
    result: str
    notes: Optional[str]


class BudgetDashboard(BaseModel):
    profile: BudgetProfileOut
    decisions: List[StakeOut]
    alerts: List[str]
    responsible_gaming_notice_fr: str
    responsible_gaming_notice_en: str
