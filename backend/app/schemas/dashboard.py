from pydantic import BaseModel, ConfigDict
from typing import Dict, Any

class DashboardCreate(BaseModel):
    name: str
    configuration: Dict[str, Any]

class DashboardResponse(DashboardCreate):
    id: int
    user_id: int
    organization_id: int

    model_config = ConfigDict(from_attributes=True)