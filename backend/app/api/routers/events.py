from fastapi import APIRouter, Depends, Request, UploadFile, File, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.event import EventBatchCreate
from app.api.deps import get_current_owner
from app.models.tenant import User
from app.core.limiter import limiter

from app.tasks.event_tasks import process_event_logic
from app.db.database import get_db, AsyncSessionLocal

from app.repositories.event_repo import EventRepository
from app.services.event_service import EventService

router = APIRouter(prefix="/api/events", tags=["Data Ingestion"])

def get_event_service(db: AsyncSession = Depends(get_db)) -> EventService:
    repo = EventRepository(db)
    return EventService(repo)

async def background_csv_processor(text_content: str, org_id: str):
    async with AsyncSessionLocal() as db_session:
        repo = EventRepository(db_session)
        service = EventService(repo)
        await service.process_csv_upload(text_content, org_id)

@router.post("/ingest", status_code=202)
@limiter.limit("100/minute")
async def ingest_events(
    request: Request,
    payload: EventBatchCreate, 
    background_tasks: BackgroundTasks, 
    current_user: User = Depends(get_current_owner),
):
    """
    Ingest events asynchronously. 
    Returns a 202 Accepted immediately while FastAPI processes the data natively.
    """
    org_id = current_user.organization_id
    event_dicts = [ev.model_dump() for ev in payload.events]
    
    background_tasks.add_task(process_event_logic, event_dicts, org_id)
    
    return {
        "status": "accepted", 
        "message": f"Queued {len(event_dicts)} events for native background processing",
        "organization_id": org_id
    }


# @router.post("/upload-csv", status_code=202)
# @limiter.limit("50/minute") 
# async def upload_events_csv(
#     request: Request,
#     background_tasks: BackgroundTasks, 
#     file: UploadFile = File(...),
#     current_user: User = Depends(get_current_owner),
# ):
#     """
#     Accepts a CSV file of events, validates the format, and instantly 
#     queues them for async database insertion in the background.
#     """
#     if not file.filename.endswith('.csv'):
#         raise HTTPException(status_code=400, detail="Invalid file type. Must be a CSV.")
    
#     content = await file.read()
#     try:
#         text_content = content.decode("utf-8")
#     except UnicodeDecodeError:
#         raise HTTPException(status_code=400, detail="File must be UTF-8 encoded.")

#     background_tasks.add_task(background_csv_processor, text_content, current_user.organization_id)

#     return {
#         "status": "accepted",
#         "message": "CSV upload accepted. Processing records in the background."
#     }

@router.post("/upload-csv", status_code=200)
async def upload_events_csv(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_owner),
    service: EventService = Depends(get_event_service)
):
    content = await file.read()
    text_content = content.decode("utf-8")
    
    result = await service.process_csv_upload(text_content, current_user.organization_id)

    return {
        "status": "success",
        "message": f"Processed {result['queued_events']} events.",
        "errors": result["errors"]
    }