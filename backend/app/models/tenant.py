from sqlalchemy import Column, String, Integer, ForeignKey, Enum, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.db.database import Base
from sqlalchemy.dialects.postgresql import JSONB

class RoleEnum(str, enum.Enum):
    OWNER = "Owner"
    ADMIN = "Admin"
    ANALYST = "Analyst"
    VIEWER = "Viewer"

class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    users = relationship("User", back_populates="organization")
    # Later, we will add 'events' and 'dashboards' here

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(RoleEnum), default=RoleEnum.VIEWER, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    role = Column(String, default="viewer", nullable=False)
    
    # Relationships
    organization = relationship("Organization", back_populates="users")

class Dashboard(Base):
    __tablename__ = "dashboards"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    configuration = Column(JSONB, nullable=False) # Stores {"days_back": 7, "event_name": "page_view"}
    user_id = Column(Integer, ForeignKey("users.id"))
    organization_id = Column(Integer, ForeignKey("organizations.id"))