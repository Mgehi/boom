from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class AddAllowedEmailRequest(BaseModel):
    email: str
    note: Optional[str] = ""


class AllowedEmailOut(BaseModel):
    id: str
    email: str
    note: Optional[str] = ""
    added_by: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}
