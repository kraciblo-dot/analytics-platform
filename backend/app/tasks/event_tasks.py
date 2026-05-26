import asyncio
from app.core.celery_app import celery_app
from app.repositories.event_repo import EventRepository
import structlog

logger = structlog.get_logger()

@celery_app.task(name="process_event_async")
def process_event_async(event_payload, org_id: dict):
    from app.services.event_service import EventService
    from app.db.database import AsyncSessionLocal

    """
    Celery worker entry point. It creates its own database session,
    injects the dependencies, and executes the service layer.
    """
    logger.info("Starting background event ingestion", event_type=event_payload.get("type"))
    
    async def run_service():
        async with AsyncSessionLocal() as db_session:
            repo = EventRepository(db_session)
            service = EventService(repo)
            await service.process_incoming_event(event_payload)
            
    asyncio.run(run_service())
    return "Success"