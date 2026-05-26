from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime
from app.models.tenant import RoleEnum

class InviteCreate(BaseModel):
    email: EmailStr
    role: RoleEnum

    
class InviteResponse(BaseModel):
    id: int
    email: str
    role: RoleEnum
    expires_at: datetime
    invite_link: str 
    
    model_config = ConfigDict(from_attributes=True)

class InviteAccept(BaseModel):
    token: str
    password: str  