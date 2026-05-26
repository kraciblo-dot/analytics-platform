import enum
from sqlalchemy import  ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy import Column, Integer, String, Enum as SQLEnum
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
    users = relationship("User", back_populates="organization", cascade="all, delete-orphan")

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    
    # Enforcing the Enum for Role-Based Access Control
    # role = Column(SQLEnum(RoleEnum, name="roleenum", create_type=False), nullable=False)
    role = Column(
        SQLEnum(
            RoleEnum, 
            name="roleenum", 
            create_type=False, 
            values_callable=lambda obj: [e.value for e in obj]
        ), 
        nullable=False
    )
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Linked to Organization with cascading deletes
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    
    # Relationships
    organization = relationship("Organization", back_populates="users")

class Dashboard(Base):
    __tablename__ = "dashboards"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    configuration = Column(JSONB, nullable=False) # Stores {"days_back": 7, "event_name": "page_view"}
    
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"))