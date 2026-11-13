"""Celery application for scheduled prediction and data sync jobs."""

from celery import Celery
from celery.schedules import crontab

from app.core.config import get_settings

settings = get_settings()

celery = Celery(
    "betpredict",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.services.tasks"],
)

celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        "sync-fixtures-hourly": {
            "task": "app.services.tasks.sync_fixtures",
            "schedule": crontab(minute=15),
        },
        "refresh-predictions-hourly": {
            "task": "app.services.tasks.refresh_predictions",
            "schedule": crontab(minute=30),
        },
        "evaluate-finished-matches": {
            "task": "app.services.tasks.evaluate_finished_matches",
            "schedule": crontab(minute=45),
        },
    },
)
