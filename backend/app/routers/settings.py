from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import get_db
from app.db.models import BusinessSettings as SettingsModel
from app.deps import get_current_user
from app.schemas.settings import BusinessSettingsIn, BusinessSettingsOut
from app.schemas.user import UserOut

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_model=BusinessSettingsOut)
async def get_settings(current_user: UserOut = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Get business settings (default sender details) for current user"""
    business_settings = await db.get(SettingsModel, current_user.user_id)
    if not business_settings:
        return BusinessSettingsOut(user_id=current_user.user_id, updated_at=datetime.now(timezone.utc))
    return business_settings


@router.put("", response_model=BusinessSettingsOut)
async def update_settings(
    payload: BusinessSettingsIn,
    current_user: UserOut = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update business settings for current user"""
    business_settings = await db.get(SettingsModel, current_user.user_id)
    now = datetime.now(timezone.utc)
    if not business_settings:
        business_settings = SettingsModel(user_id=current_user.user_id)
        db.add(business_settings)

    for field, value in payload.model_dump().items():
        setattr(business_settings, field, value)
    business_settings.updated_at = now

    await db.commit()
    await db.refresh(business_settings)
    return business_settings
