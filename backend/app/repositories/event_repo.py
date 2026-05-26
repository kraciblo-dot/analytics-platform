from sqlalchemy.ext.asyncio import AsyncSession
from app.models.event import Event

class EventRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_event(self, event_data: dict) -> Event:
        db_event = Event(**event_data)
        self.session.add(db_event)
        await self.session.commit()
        await self.session.refresh(db_event)
        return db_event