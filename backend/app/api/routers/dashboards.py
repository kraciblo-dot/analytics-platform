from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.database import get_db
from app.models.tenant import Dashboard, User
from app.schemas.dashboard import DashboardCreate, DashboardResponse
from app.api.deps import get_current_user

router = APIRouter(prefix="/api/dashboards", tags=["Dashboards"])

@router.post("", response_model=DashboardResponse)
async def save_dashboard(
    payload: DashboardCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    new_dash = Dashboard(
        name=payload.name,
        configuration=payload.configuration,
        user_id=current_user.id,
        organization_id=current_user.organization_id
    )
    db.add(new_dash)
    await db.commit()
    await db.refresh(new_dash)
    return new_dash

@router.get("", response_model=list[DashboardResponse])
async def get_dashboards(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Dashboard).where(Dashboard.organization_id == current_user.organization_id)
    )
    return result.scalars().all()