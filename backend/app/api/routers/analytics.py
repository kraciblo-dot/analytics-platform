from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, cast, Date
from datetime import datetime, timedelta
from typing import List, Dict, Any

from app.db.database import get_db
from app.models.event import Event
from app.api.deps import get_current_user
from app.models.tenant import User

router = APIRouter(prefix="/api/analytics", tags=["Analytics & Dashboards"])

@router.get("/timeseries")
async def get_time_series_data(
    event_name: str,
    days_back: int = Query(7, description="Number of days to look back"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns aggregated daily counts for a specific event to power Line/Bar charts.
    """
    start_date = datetime.utcnow() - timedelta(days=days_back)
    
    stmt = (
        select(
            cast(Event.timestamp, Date).label("day"),
            func.count(Event.id).label("total_count")
        )
        .where(Event.organization_id == current_user.organization_id)
        .where(Event.event_name == event_name)
        .where(Event.timestamp >= start_date)
        .group_by(cast(Event.timestamp, Date))
        .order_by(cast(Event.timestamp, Date))
    )
    
    result = await db.execute(stmt)
    rows = result.all()
    
    chart_data = [
        {"date": row.day.strftime("%Y-%m-%d"), "count": row.total_count}
        for row in rows
    ]
    
    return {
        "event_name": event_name,
        "time_range": f"Last {days_back} days",
        "data": chart_data
    }

@router.get("/kpi")
async def get_kpi_total(
    event_name: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns the absolute total count of an event to power a single KPI Number Card.
    """
    stmt = (
        select(func.count(Event.id))
        .where(Event.organization_id == current_user.organization_id)
        .where(Event.event_name == event_name)
    )
    
    result = await db.execute(stmt)
    total = result.scalar() or 0
    
    return {
        "event_name": event_name,
        "total_count": total
    }