from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models.tenant import User
from app.api.deps import get_current_admin
from app.schemas.invite import InviteCreate, InviteResponse, InviteAccept
from app.repositories.invite_repo import InviteRepository
from app.services.invite_service import InviteService

router = APIRouter(prefix="/api/invites", tags=["Team Invites"])

def get_invite_service(db: AsyncSession = Depends(get_db)) -> InviteService:
    repo = InviteRepository(db)
    return InviteService(repo, db)

@router.post("/", response_model=InviteResponse, status_code=status.HTTP_201_CREATED)
async def generate_team_invite(
    payload: InviteCreate,
    current_admin: User = Depends(get_current_admin),
    service: InviteService = Depends(get_invite_service)
):
    """
    Generates a secure invite link for a new team member. 
    Only Owners and Admins can access this endpoint.
    """
    return await service.create_invite(
        org_id=current_admin.organization_id,
        email=payload.email,
        role=payload.role
    )

@router.post("/accept", status_code=status.HTTP_200_OK)
async def accept_team_invite(
    payload: InviteAccept,
    service: InviteService = Depends(get_invite_service)
):
    """
    Public endpoint. Consumes an invite token and a password to create a new user account.
    """
    return await service.accept_invite(token=payload.token, password=payload.password)