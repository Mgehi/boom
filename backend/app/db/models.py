import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Float, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[str] = mapped_column(String, primary_key=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    name: Mapped[str] = mapped_column(String, default="")
    picture: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class UserSession(Base):
    __tablename__ = "user_sessions"

    session_token: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.user_id"), index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class AllowedEmail(Base):
    __tablename__ = "allowed_emails"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    note: Mapped[Optional[str]] = mapped_column(String, default="")
    added_by: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class BusinessSettings(Base):
    __tablename__ = "settings"

    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.user_id"), primary_key=True)
    business_name: Mapped[str] = mapped_column(String, default="")
    sender_name: Mapped[str] = mapped_column(String, default="")
    sender_phone: Mapped[str] = mapped_column(String, default="")
    sender_email: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    sender_address: Mapped[str] = mapped_column(String, default="")
    sender_city: Mapped[str] = mapped_column(String, default="")
    sender_state: Mapped[str] = mapped_column(String, default="")
    sender_pincode: Mapped[str] = mapped_column(String, default="")
    pickup_location: Mapped[str] = mapped_column(String, default="")
    seller_gst: Mapped[Optional[str]] = mapped_column(String, default="")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class Shipment(Base):
    __tablename__ = "shipments"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.user_id"), index=True)
    order_id: Mapped[str] = mapped_column(String, index=True)
    waybill: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    pickup_location: Mapped[str] = mapped_column(String)
    sender: Mapped[dict] = mapped_column(JSONB)
    receiver: Mapped[dict] = mapped_column(JSONB)
    items: Mapped[list] = mapped_column(JSONB)
    payment_mode: Mapped[str] = mapped_column(String)
    cod_amount: Mapped[float] = mapped_column(Float, default=0)
    weight: Mapped[float] = mapped_column(Float)
    length: Mapped[float] = mapped_column(Float, default=10)
    breadth: Mapped[float] = mapped_column(Float, default=10)
    height: Mapped[float] = mapped_column(Float, default=10)
    seller_gst: Mapped[Optional[str]] = mapped_column(String, default="")
    seller_invoice: Mapped[Optional[str]] = mapped_column(String, default="")
    shipment_type: Mapped[str] = mapped_column(String, default="FWD")
    status: Mapped[str] = mapped_column(String, index=True, default="Pending")
    delhivery_response: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    tracking_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    last_synced_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class Pickup(Base):
    __tablename__ = "pickups"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.user_id"), index=True)
    pickup_location: Mapped[str] = mapped_column(String)
    pickup_date: Mapped[str] = mapped_column(String)
    pickup_time: Mapped[str] = mapped_column(String, default="10:00:00")
    expected_package_count: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String, default="Scheduled")
    delhivery_response: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
