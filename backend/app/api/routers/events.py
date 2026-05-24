from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
import asyncio

from app.db.database import get_db
from app.models.event import Event
from app.schemas.event import EventBatchCreate
from app.api.deps import get_current_user
from app.models.tenant import User
from app.api.ws_manager import manager 
from app.core.limiter import limiter
from app.api.deps import get_current_owner

router = APIRouter(prefix="/api/events", tags=["Data Ingestion"])

# Simulated Celery Worker Function
async def background_data_enrichment(event_count: int, org_id: int):
    """Simulates a heavy background task like IP geolocation or sending to a data lake."""
    await asyncio.sleep(2)  # Simulate network delay
    print(f"[BACKGROUND WORKER] Successfully enriched {event_count} events for Org {org_id}")

@router.post("/ingest", status_code=202) # 202 is the correct HTTP status for async queues
@limiter.limit("100/minute")
async def ingest_events(
    request: Request,
    payload: EventBatchCreate, 
    background_tasks: BackgroundTasks, # <-- Inject the background task manager
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_owner),
    # current_user: User = Depends(get_current_user)
):
    org_id = current_user.organization_id
    db_events = []
    
    for ev in payload.events:
        db_event = Event(
            organization_id=org_id,
            event_name=ev.event_name,
            properties=ev.properties,
            timestamp=ev.timestamp or datetime.utcnow()
        )
        db.add(db_event)
        db_events.append(db_event)
        
        # Broadcast to UI immediately
        await manager.broadcast_to_org({
            "event_name": ev.event_name,
            "properties": ev.properties,
            "timestamp": str(db_event.timestamp)
        }, org_id)
    
    await db.commit()
    
    # NEW: Offload the heavy processing to the background worker
    background_tasks.add_task(background_data_enrichment, len(db_events), org_id)
    
    return {
        "status": "accepted", 
        "message": f"Queued {len(db_events)} events for background processing",
        "organization_id": org_id
    }