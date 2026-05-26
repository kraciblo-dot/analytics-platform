import asyncio
from app.core.celery_app import celery_app
from app.repositories.event_repo import EventRepository
import structlog

logger = structlog.get_logger()

async def process_event_logic(event_payload, org_id):
    from app.services.event_service import EventService
    from app.db.database import AsyncSessionLocal
    
    logger.info("Starting background event ingestion", event_type=event_payload.get("type"), org_id=org_id)
    
    async with AsyncSessionLocal() as db_session:
        repo = EventRepository(db_session)
        service = EventService(repo)
        await service.process_incoming_event(event_payload)
        
    return "Success"


# 2. THE CELERY TASK (Kept exactly as is for the future, but currently not used by FastAPI)
@celery_app.task(name="process_event_async")
def process_event_async(event_payload, org_id: dict):
    """
    Celery worker entry point. It creates its own database session,
    injects the dependencies, and executes the service layer.
    """
    asyncio.run(process_event_logic(event_payload, org_id))
    return "Success"