from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from app.db.database import Base

class Event(Base):
    __tablename__ = "events"
    
    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    
    # E.g., "user_signed_up", "button_clicked"
    event_name = Column(String, index=True, nullable=False) 
    
    # Flexible JSON payload for custom data (e.g., {"browser": "Chrome", "plan": "Pro"})
    properties = Column(JSON, default={})
    
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)