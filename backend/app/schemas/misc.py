from typing import Optional

from pydantic import BaseModel


class DashboardStats(BaseModel):
    total_shipments: int
    today_shipments: int
    in_transit: int
    delivered: int
    exceptions: int


class WarehouseRegistration(BaseModel):
    name: str
    email: str
    phone: str
    address: str
    city: str
    state: str
    country: str = "India"
    pin: str
    return_address: Optional[str] = None
    return_pin: Optional[str] = None
    return_city: Optional[str] = None
    return_state: Optional[str] = None
