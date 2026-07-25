"""One-endpoint domains that don't earn their own file: dashboard stats,
public tracking, pincode check, warehouse registration."""
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import get_db
from app.db.models import Shipment as ShipmentModel
from app.deps import get_current_user
from app.routers.shipments import sync_shipment_statuses_task
from app.schemas.misc import DashboardStats, WarehouseRegistration
from app.schemas.shipment import ShipmentStatus
from app.schemas.user import UserOut
from app.services.delhivery import (
    check_pincode_serviceability,
    register_delhivery_warehouse,
    track_delhivery_shipment,
)

router = APIRouter(tags=["misc"])


@router.get("/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    background_tasks: BackgroundTasks,
    current_user: UserOut = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get dashboard statistics for the current user"""
    background_tasks.add_task(sync_shipment_statuses_task, current_user.user_id)

    async def count(*conditions):
        result = await db.execute(
            select(func.count()).select_from(ShipmentModel).where(ShipmentModel.user_id == current_user.user_id, *conditions)
        )
        return result.scalar_one()

    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    total = await count()
    today = await count(ShipmentModel.created_at >= today_start)
    in_transit = await count(ShipmentModel.status == ShipmentStatus.IN_TRANSIT.value)
    delivered = await count(ShipmentModel.status == ShipmentStatus.DELIVERED.value)
    exceptions = await count(ShipmentModel.status == ShipmentStatus.EXCEPTION.value)

    return DashboardStats(
        total_shipments=total,
        today_shipments=today,
        in_transit=in_transit,
        delivered=delivered,
        exceptions=exceptions,
    )


@router.get("/track/{waybill}")
async def public_track(waybill: str, db: AsyncSession = Depends(get_db)):
    """Public tracking endpoint - no auth required. Customer-facing."""
    result = await db.execute(select(ShipmentModel).where(ShipmentModel.waybill == waybill))
    shipment = result.scalars().first()

    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")

    try:
        tracking_data = await track_delhivery_shipment(waybill)
    except HTTPException:
        tracking_data = None

    scans = []
    current_status = shipment.status or "Pending"
    edd = None
    origin = None
    destination = None

    if tracking_data and tracking_data.get("ShipmentData"):
        sd = tracking_data["ShipmentData"][0].get("Shipment", {})
        scans_raw = sd.get("Scans", [])
        for s in scans_raw:
            d = s.get("ScanDetail", {})
            scans.append({
                "status": d.get("Scan", ""),
                "instructions": d.get("Instructions", ""),
                "location": d.get("ScannedLocation", ""),
                "datetime": d.get("ScanDateTime", ""),
            })
        scans.reverse()
        current_status = sd.get("Status", {}).get("Status", current_status)
        edd = sd.get("ExpectedDeliveryDate") or sd.get("PromisedDeliveryDate")
        origin = sd.get("Origin", "")
        destination = sd.get("Destination", "")

    return {
        "waybill": waybill,
        "order_id": shipment.order_id,
        "receiver_name": shipment.receiver["name"],
        "receiver_city": shipment.receiver["city"],
        "shipment_type": shipment.shipment_type or "FWD",
        "current_status": current_status,
        "expected_delivery": edd,
        "origin": origin,
        "destination": destination,
        "scans": scans,
        "created_at": shipment.created_at,
    }


@router.get("/pincode/check")
async def check_pincode(pincode: str, current_user: UserOut = Depends(get_current_user)):
    """Check if a pincode is serviceable by Delhivery"""
    return await check_pincode_serviceability(pincode)


@router.post("/warehouse/register")
async def register_warehouse(warehouse: WarehouseRegistration, current_user: UserOut = Depends(get_current_user)):
    """Register a warehouse/pickup location with Delhivery"""
    return await register_delhivery_warehouse(warehouse)
