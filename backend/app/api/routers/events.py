from fastapi import APIRouter, Depends, Request, UploadFile, File, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.event import EventBatchCreate
from app.api.deps import get_current_owner
from app.models.tenant import User
from app.core.limiter import limiter
from app.tasks.event_tasks import process_event_async
from app.db.database import get_db
from app.repositories.event_repo import EventRepository
from app.services.event_service import EventService

router = APIRouter(prefix="/api/events", tags=["Data Ingestion"])

def get_event_service(db: AsyncSession = Depends(get_db)) -> EventService:
    repo = EventRepository(db)
    return EventService(repo)

@router.post("/ingest", status_code=202)
@limiter.limit("100/minute")
async def ingest_events(
    request: Request,
    payload: EventBatchCreate, 
    current_user: User = Depends(get_current_owner),
):
    """
    Ingest events asynchronously. 
    Returns a 202 Accepted immediately while Celery processes the data.
    """
    org_id = current_user.organization_id
    
    event_dicts = [ev.model_dump() for ev in payload.events]
    
    process_event_async.delay(event_dicts, org_id)
    
    return {
        "status": "accepted", 
        "message": f"Queued {len(event_dicts)} events for background processing via Celery",
        "organization_id": org_id
    }


@router.post("/upload-csv", status_code=202)
@limiter.limit("50/minute") 
async def upload_events_csv(
    request: Request,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_owner),
    service: EventService = Depends(get_event_service)
):
    """
    Accepts a CSV file of events, parses properties dynamically, 
    and queues them for async database insertion.
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Invalid file type. Must be a CSV.")
    
    content = await file.read()
    try:
        text_content = content.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File must be UTF-8 encoded.")

    result = await service.process_csv_upload(text_content, current_user.organization_id)

    return {
        "status": "accepted",
        "message": f"Processed CSV. Queued {result['queued_events']} valid events.",
        "errors": result["errors"]  
    }