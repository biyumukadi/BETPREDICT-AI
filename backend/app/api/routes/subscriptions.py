from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, user_plan
from app.core.config import get_settings
from app.db.session import get_db
from app.models.user import Subscription, SubscriptionPlan, User, UserRole

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


class PlanInfo(BaseModel):
    plan: str
    price_eur_monthly: Optional[float]
    features: list[str]


PLANS = [
    PlanInfo(
        plan="free",
        price_eur_monthly=0,
        features=[
            "Browse fixtures",
            "Essential team statistics",
            "Limited daily AI analyses",
        ],
    ),
    PlanInfo(
        plan="premium",
        price_eur_monthly=19.99,
        features=[
            "Advanced AI analyses",
            "Probability vs odds comparison",
            "Full prediction history",
            "Personalized alerts",
        ],
    ),
    PlanInfo(
        plan="pro",
        price_eur_monthly=49.99,
        features=[
            "Deep statistical dashboards",
            "Excel/PDF export",
            "Detailed performance tracking",
            "Conditional API access",
        ],
    ),
]


@router.get("/plans", response_model=list[PlanInfo])
async def list_plans():
    return PLANS


@router.get("/me")
async def my_subscription(user: User = Depends(get_current_user)):
    plan = user_plan(user)
    return {
        "plan": plan.value,
        "status": user.subscription.status if user.subscription else "active",
        "payment_provider": user.subscription.payment_provider if user.subscription else "none",
        "current_period_end": user.subscription.current_period_end if user.subscription else None,
    }


class CheckoutRequest(BaseModel):
    plan: SubscriptionPlan
    provider: str = "stripe"  # stripe | mpesa | airtel | orange


@router.post("/checkout")
async def checkout(
    payload: CheckoutRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    settings = get_settings()
    if payload.plan == SubscriptionPlan.FREE:
        raise HTTPException(status_code=400, detail="Free plan does not require checkout")

    if payload.provider == "stripe":
        if not settings.stripe_secret_key:
            # Demo checkout simulation when Stripe is not configured
            sub = user.subscription or Subscription(user_id=user.id)
            sub.plan = payload.plan
            sub.status = "active"
            sub.payment_provider = "stripe_demo"
            sub.current_period_end = datetime.now(timezone.utc) + timedelta(days=30)
            sub.notes = "DEMO subscription — Stripe keys not configured"
            if payload.plan == SubscriptionPlan.PREMIUM:
                user.role = UserRole.PREMIUM
            elif payload.plan == SubscriptionPlan.PRO:
                user.role = UserRole.PRO
            db.add(sub)
            db.add(user)
            await db.flush()
            return {
                "mode": "demo",
                "message": "Stripe not configured — activated demo subscription for 30 days.",
                "plan": payload.plan.value,
            }
        import stripe

        stripe.api_key = settings.stripe_secret_key
        price = settings.stripe_price_premium if payload.plan == SubscriptionPlan.PREMIUM else settings.stripe_price_pro
        session = stripe.checkout.Session.create(
            mode="subscription",
            line_items=[{"price": price, "quantity": 1}],
            success_url=f"{settings.cors_origin_list[0]}/billing?success=1",
            cancel_url=f"{settings.cors_origin_list[0]}/billing?canceled=1",
            customer_email=user.email,
            metadata={"user_id": str(user.id), "plan": payload.plan.value},
        )
        return {"mode": "stripe", "checkout_url": session.url}

    # Mobile Money placeholders — require regional credentials
    return {
        "mode": "mobile_money_pending",
        "provider": payload.provider,
        "message": (
            f"{payload.provider} checkout requires licensed credentials. "
            "Configure MPESA_*/AIRTEL_*/ORANGE_* env vars for production."
        ),
    }


@router.post("/webhook/stripe")
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    settings = get_settings()
    payload = await request.body()
    if not settings.stripe_webhook_secret:
        return {"received": True, "mode": "demo_ignored"}
    import stripe

    sig = request.headers.get("stripe-signature", "")
    event = stripe.Webhook.construct_event(payload, sig, settings.stripe_webhook_secret)
    return {"received": True, "type": event.get("type")}
