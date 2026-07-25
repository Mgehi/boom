import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import get_db
from app.db.models import Pickup as PickupModel
from app.deps import get_current_user
from app.schemas.pickup import PickupOut, PickupRequest
from app.schemas.user import UserOut
from app.services.delhivery import schedule_delhivery_pickup

logger = logging.getLogger(__name__)
router = APIRouter(tags=["pickups"])


@router.post("/pickups", response_model=PickupOut)
async def schedule_pickup(
    pickup: PickupRequest,
    current_user: UserOut = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Schedule a pickup with Delhivery"""
    try:
        delhivery_response = await schedule_delhivery_pickup(pickup)

        pickup_obj = PickupModel(
            user_id=current_user.user_id,
            pickup_location=pickup.pickup_location,
            pickup_date=pickup.pickup_date,
            pickup_time=pickup.pickup_time or "10:00:00",
            expected_package_count=pickup.expected_package_count,
            delhivery_response=delhivery_response,
            created_at=datetime.now(timezone.utc),
        )
        db.add(pickup_obj)
        await db.commit()
        await db.refresh(pickup_obj)

        logger.info(f"Pickup scheduled for user {current_user.user_id}: {pickup.pickup_location} on {pickup.pickup_date}")
        return pickup_obj
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to schedule pickup: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pickups", response_model=list[PickupOut])
async def get_pickups(
    limit: int = Query(100, le=500),
    current_user: UserOut = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all pickups for the current user"""
    result = await db.execute(
        select(PickupModel)
        .where(PickupModel.user_id == current_user.user_id)
        .order_by(PickupModel.created_at.desc())
        .limit(limit)
    )
    return result.scalars().all()
