from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class BusinessSettingsIn(BaseModel):
    business_name: str = ""
    sender_name: str = ""
    sender_phone: str = ""
    sender_email: Optional[str] = None
    sender_address: str = ""
    sender_city: str = ""
    sender_state: str = ""
    sender_pincode: str = ""
    pickup_location: str = ""
    seller_gst: Optional[str] = ""


class BusinessSettingsOut(BusinessSettingsIn):
    user_id: Optional[str] = None
    updated_at: datetime

    model_config = {"from_attributes": True}
