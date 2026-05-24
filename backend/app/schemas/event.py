from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime

class EventCreate(BaseModel):
    event_name: str
    properties: Dict[str, Any] = Field(default_factory=dict)
    timestamp: Optional[datetime] = None

class EventBatchCreate(BaseModel):
    events: List[EventCreate]