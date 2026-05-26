from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.db.database import get_db
from app.models.tenant import User
from app.api.deps import get_current_admin, get_current_owner
from app.schemas.api_key import ApiKeyCreate, ApiKeyResponse, ApiKeyList
from app.repositories.api_key_repo import ApiKeyRepository
from app.services.api_key_service import ApiKeyService


router = APIRouter(prefix="/api/keys", tags=["API Keys"])

# Dependency to inject the service cleanly
def get_api_key_service(db: AsyncSession = Depends(get_db)) -> ApiKeyService:
    repo = ApiKeyRepository(db)
    return ApiKeyService(repo)

@router.post("/", response_model=ApiKeyResponse, status_code=status.HTTP_201_CREATED)
async def generate_api_key(
    payload: ApiKeyCreate,
    current_user: User = Depends(get_current_owner),
    service: ApiKeyService = Depends(get_api_key_service)
):
    """
    Generate a new API key. 
    The raw secret key is only ever returned ONCE in this response.
    """
    return await service.create_api_key(
        org_id=current_user.organization_id,
        name=payload.name,
        expires_in_days=payload.expires_in_days
    )

@router.get("/", response_model=List[ApiKeyList])
async def list_api_keys(
    current_user: User = Depends(get_current_owner),
    service: ApiKeyService = Depends(get_api_key_service)
):
    """List all API keys belonging to the organization (safe fields only)."""
    return await service.list_org_keys(org_id=current_user.organization_id)

@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    key_id: int,
    current_admin: User = Depends(get_current_admin), 
    service: ApiKeyService = Depends(get_api_key_service)
):
    """
    Revokes (deletes) an API key permanently.
    """
    await service.revoke_api_key(key_id=key_id, org_id=current_admin.organization_id)
    return None

@router.post("/{key_id}/rotate", status_code=status.HTTP_201_CREATED)
async def rotate_api_key(
    key_id: int,
    current_admin: User = Depends(get_current_admin),
    service: ApiKeyService = Depends(get_api_key_service)
):
    """
    Revokes the specific API key and instantly issues a replacement.
    """
    return await service.rotate_api_key(key_id=key_id, org_id=current_admin.organization_id)