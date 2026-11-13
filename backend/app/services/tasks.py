"""Celery tasks for sync, prediction refresh and evaluation."""

from app.core.celery_app import celery
from app.db.session import SyncSessionLocal
from app.services.evaluation import evaluate_finished


@celery.task(name="app.services.tasks.sync_fixtures")
def sync_fixtures() -> dict:
    from app.services.sync import sync_catalog, sync_fixtures as _sync
    import asyncio

    async def _run():
        from app.db.session import AsyncSessionLocal

        async with AsyncSessionLocal() as session:
            catalog = await sync_catalog(session)
            fixtures = await _sync(session)
            await session.commit()
            return {**catalog, **fixtures}

    return asyncio.get_event_loop().run_until_complete(_run())


@celery.task(name="app.services.tasks.refresh_predictions")
def refresh_predictions() -> dict:
    import asyncio
    from app.services.sync import generate_predictions_for_upcoming

    async def _run():
        from app.db.session import AsyncSessionLocal

        async with AsyncSessionLocal() as session:
            result = await generate_predictions_for_upcoming(session)
            await session.commit()
            return result

    return asyncio.get_event_loop().run_until_complete(_run())


@celery.task(name="app.services.tasks.evaluate_finished_matches")
def evaluate_finished_matches() -> dict:
    import asyncio

    async def _run():
        from app.db.session import AsyncSessionLocal

        async with AsyncSessionLocal() as session:
            result = await evaluate_finished(session)
            await session.commit()
            return result

    return asyncio.get_event_loop().run_until_complete(_run())
