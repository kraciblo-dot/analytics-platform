from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

class ApiKeyCreate(BaseModel):
    name: str
    expires_in_days: Optional[int] = None

class ApiKeyResponse(BaseModel):
    id: int
    name: str
    raw_key: str  
    prefix: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class ApiKeyList(BaseModel):
    id: int
    name: str
    prefix: str
    is_active: bool
    created_at: datetime
    expires_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)