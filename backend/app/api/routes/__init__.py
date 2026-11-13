from fastapi import APIRouter

from app.api.routes import admin, auth, budget, fixtures, notifications, predictions, subscriptions

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(fixtures.router)
api_router.include_router(predictions.router)
api_router.include_router(budget.router)
api_router.include_router(subscriptions.router)
api_router.include_router(notifications.router)
api_router.include_router(admin.router)
