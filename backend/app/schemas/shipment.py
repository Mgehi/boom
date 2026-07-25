from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any

from pydantic import BaseModel, EmailStr


class ShipmentStatus(str, Enum):
    PENDING = "Pending"
    MANIFESTED = "Manifested"
    IN_TRANSIT = "In Transit"
    OUT_FOR_DELIVERY = "Out for Delivery"
    DELIVERED = "Delivered"
    RTO = "RTO"
    EXCEPTION = "Exception"


class PaymentMode(str, Enum):
    COD = "COD"
    PREPAID = "Prepaid"


class ShipmentType(str, Enum):
    FORWARD = "FWD"
    REVERSE = "RVP"


class Address(BaseModel):
    name: str
    phone: str
    email: Optional[EmailStr] = None
    address: str
    city: str
    state: str
    pincode: str
    country: str = "India"


class OrderItem(BaseModel):
    name: str
    qty: int
    price: float
    sku: Optional[str] = None
    hsn_code: Optional[str] = ""


class CreateShipmentRequest(BaseModel):
    order_id: str
    pickup_location: str
    sender: Address
    receiver: Address
    items: List[OrderItem]
    payment_mode: PaymentMode
    cod_amount: Optional[float] = 0
    weight: float  # in kg (converted to grams for Delhivery)
    length: Optional[float] = 10
    breadth: Optional[float] = 10
    height: Optional[float] = 10
    seller_gst: Optional[str] = ""
    seller_invoice: Optional[str] = ""
    shipment_type: ShipmentType = ShipmentType.FORWARD


class ShipmentOut(BaseModel):
    id: str
    user_id: Optional[str] = None
    order_id: str
    waybill: Optional[str] = None
    pickup_location: str
    sender: Address
    receiver: Address
    items: List[OrderItem]
    payment_mode: PaymentMode
    cod_amount: float = 0
    weight: float
    length: float = 10
    breadth: float = 10
    height: float = 10
    seller_gst: Optional[str] = ""
    seller_invoice: Optional[str] = ""
    shipment_type: ShipmentType = ShipmentType.FORWARD
    status: ShipmentStatus = ShipmentStatus.PENDING
    delhivery_response: Optional[Dict[str, Any]] = None
    tracking_data: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
