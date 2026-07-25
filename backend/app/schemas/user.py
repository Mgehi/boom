from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class UserOut(BaseModel):
    user_id: str
    email: str
    name: str
    picture: Optional[str] = None
    is_admin: bool = False
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
