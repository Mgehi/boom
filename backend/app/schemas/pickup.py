from datetime import datetime
from typing import Optional, Dict, Any

from pydantic import BaseModel


class PickupRequest(BaseModel):
    pickup_location: str
    pickup_date: str
    pickup_time: Optional[str] = "10:00:00"
    expected_package_count: int


class PickupOut(BaseModel):
    id: str
    user_id: Optional[str] = None
    pickup_location: str
    pickup_date: str
    pickup_time: str = "10:00:00"
    expected_package_count: int
    status: str = "Scheduled"
    delhivery_response: Optional[Dict[str, Any]] = None
    created_at: datetime

    model_config = {"from_attributes": True}
