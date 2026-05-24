from pydantic import BaseModel, EmailStr
from app.models.tenant import RoleEnum

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    organization_name: str 

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    role: RoleEnum
    organization_id: int

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str