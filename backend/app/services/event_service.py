import csv
import io
from pydantic import ValidationError

from app.repositories.event_repo import EventRepository
from app.schemas.event import EventCreate
from app.tasks.event_tasks import process_event_async

class EventService:
    def __init__(self, repo: EventRepository):
        self.repo = repo

    async def process_incoming_event(self, event_data: dict):
        """Processes a single event directly."""
        return await self.repo.create_event(event_data)

    async def process_batch_events(self, event_payloads: list[dict], org_id: int):
        """
        Processes a batch of events.
        This is the method actually called by your background Celery worker.
        """
        for payload in event_payloads:
            payload["organization_id"] = org_id
            await self.repo.create_event(payload)
            
        return len(event_payloads)

    async def process_csv_upload(self, file_content: str, org_id: int) -> dict:
        from app.tasks.event_tasks import process_event_async
        """
        Parses a flat CSV, validates against the Pydantic schema, and queues to Celery.
        Any column that isn't 'event_name' or 'timestamp' becomes a property.
        """
        reader = csv.DictReader(io.StringIO(file_content))
        valid_events = []
        errors = []

        for row_num, row in enumerate(reader, start=1):
            try:
                event_name = row.pop("event_name", None)
                if not event_name:
                    errors.append(f"Row {row_num}: Missing 'event_name'")
                    continue

                timestamp_str = row.pop("timestamp", None)
                timestamp = timestamp_str if timestamp_str else None 

                properties = {k: v for k, v in row.items() if v}

                event = EventCreate(
                    event_name=event_name,
                    timestamp=timestamp,
                    properties=properties
                )
                
                valid_events.append(event.model_dump())

            except ValidationError as e:
                errors.append(f"Row {row_num} validation error: {e.errors()[0]['msg']}")

        if valid_events:
            process_event_async.delay(valid_events, org_id)

        return {
            "queued_events": len(valid_events),
            "errors": errors
        }