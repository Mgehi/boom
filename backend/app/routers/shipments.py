import csv
import io
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

import httpx
from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse
from pypdf import PdfReader, PdfWriter
from sqlalchemy import and_, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import async_session, get_db
from app.db.models import BusinessSettings as SettingsModel
from app.db.models import Shipment as ShipmentModel
from app.deps import get_current_user
from app.schemas.shipment import CreateShipmentRequest, ShipmentOut, ShipmentStatus
from app.schemas.user import UserOut
from app.services.delhivery import (
    create_delhivery_shipment,
    get_packing_slip,
    map_delhivery_status,
    track_delhivery_shipment,
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["shipments"])

FINAL_STATUSES = {ShipmentStatus.DELIVERED.value, ShipmentStatus.RTO.value}
SYNC_STALE_SECONDS = 300


async def _create_shipment_internal(order: CreateShipmentRequest, user_id: str, db: AsyncSession) -> ShipmentModel:
    """Create shipment in Delhivery, then persist it."""
    delhivery_response = await create_delhivery_shipment(order)

    waybill = None
    if delhivery_response.get("packages"):
        waybill = delhivery_response["packages"][0].get("waybill")

    now = datetime.now(timezone.utc)
    shipment = ShipmentModel(
        user_id=user_id,
        order_id=order.order_id,
        waybill=waybill,
        pickup_location=order.pickup_location,
        sender=order.sender.model_dump(),
        receiver=order.receiver.model_dump(),
        items=[i.model_dump() for i in order.items],
        payment_mode=order.payment_mode.value,
        cod_amount=order.cod_amount or 0,
        weight=order.weight,
        length=order.length or 10,
        breadth=order.breadth or 10,
        height=order.height or 10,
        seller_gst=order.seller_gst or "",
        seller_invoice=order.seller_invoice or "",
        shipment_type=order.shipment_type.value,
        status=(ShipmentStatus.MANIFESTED if waybill else ShipmentStatus.PENDING).value,
        delhivery_response=delhivery_response,
        created_at=now,
        updated_at=now,
    )
    db.add(shipment)
    await db.commit()
    await db.refresh(shipment)
    return shipment


async def sync_user_shipment_statuses(user_id: str, db: AsyncSession, force: bool = False) -> int:
    """Refresh shipment statuses for the user from Delhivery for non-final, stale shipments.
    Returns count of shipments updated. Best-effort; logs errors but never raises."""
    try:
        conditions = [
            ShipmentModel.user_id == user_id,
            ShipmentModel.waybill.isnot(None),
            ShipmentModel.status.notin_(list(FINAL_STATUSES)),
        ]
        if not force:
            cutoff = datetime.now(timezone.utc) - timedelta(seconds=SYNC_STALE_SECONDS)
            conditions.append(or_(ShipmentModel.last_synced_at.is_(None), ShipmentModel.last_synced_at < cutoff))

        result = await db.execute(select(ShipmentModel.waybill).where(and_(*conditions)).limit(500))
        waybills = [w for (w,) in result.all() if w]
        if not waybills:
            return 0

        updated = 0
        now = datetime.now(timezone.utc)
        for i in range(0, len(waybills), 50):
            batch = waybills[i:i + 50]
            try:
                data = await track_delhivery_shipment(",".join(batch))
            except Exception as e:
                logger.warning(f"Bulk tracking failed for batch: {str(e)}")
                continue

            shipment_data = data.get("ShipmentData") or []
            for entry in shipment_data:
                sd = entry.get("Shipment", {}) or {}
                awb = sd.get("AWB") or sd.get("Awb")
                if not awb:
                    continue
                status_obj = sd.get("Status") or {}
                status_raw = status_obj.get("Status") or status_obj.get("StatusType") or ""
                instructions = status_obj.get("Instructions") or ""
                new_status = map_delhivery_status(instructions or status_raw)

                await db.execute(
                    update(ShipmentModel)
                    .where(ShipmentModel.user_id == user_id, ShipmentModel.waybill == awb)
                    .values(status=new_status.value, tracking_data=data, last_synced_at=now, updated_at=now)
                )
                updated += 1

        # Mark unmatched (Delhivery didn't return data) as synced too so we don't hammer the API
        await db.execute(
            update(ShipmentModel)
            .where(
                ShipmentModel.user_id == user_id,
                ShipmentModel.waybill.in_(waybills),
                ShipmentModel.last_synced_at != now,
            )
            .values(last_synced_at=now)
        )
        await db.commit()
        return updated
    except Exception as e:
        logger.error(f"sync_user_shipment_statuses failed: {str(e)}")
        return 0


async def sync_shipment_statuses_task(user_id: str, force: bool = False) -> None:
    """BackgroundTasks entry point: opens its own DB session since the
    request's session is already closed by the time background tasks run."""
    async with async_session() as db:
        await sync_user_shipment_statuses(user_id, db, force=force)


@router.post("/orders", response_model=ShipmentOut)
async def receive_order(
    order: CreateShipmentRequest,
    current_user: UserOut = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Webhook endpoint to receive orders from external website and auto-create shipment"""
    try:
        shipment = await _create_shipment_internal(order, current_user.user_id, db)
        logger.info(f"Order {order.order_id} for user {current_user.user_id} manifested with waybill {shipment.waybill}")
        return shipment
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process order: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/shipments", response_model=ShipmentOut)
async def create_shipment_manual(
    order: CreateShipmentRequest,
    current_user: UserOut = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Manually create a shipment"""
    return await receive_order(order, current_user, db)


@router.get("/shipments", response_model=list[ShipmentOut])
async def get_shipments(
    background_tasks: BackgroundTasks,
    status: Optional[ShipmentStatus] = None,
    limit: int = Query(100, le=500),
    current_user: UserOut = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all shipments for the current user"""
    background_tasks.add_task(sync_shipment_statuses_task, current_user.user_id)

    query = select(ShipmentModel).where(ShipmentModel.user_id == current_user.user_id)
    if status:
        query = query.where(ShipmentModel.status == status.value)
    query = query.order_by(ShipmentModel.created_at.desc()).limit(limit)

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/shipments/{shipment_id}", response_model=ShipmentOut)
async def get_shipment(
    shipment_id: str,
    current_user: UserOut = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get shipment by ID (scoped to user)"""
    shipment = await db.get(ShipmentModel, shipment_id)
    if not shipment or shipment.user_id != current_user.user_id:
        raise HTTPException(status_code=404, detail="Shipment not found")
    return shipment


@router.get("/shipments/{shipment_id}/track")
async def track_shipment(
    shipment_id: str,
    current_user: UserOut = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Track shipment using Delhivery API (scoped to user)"""
    shipment = await db.get(ShipmentModel, shipment_id)
    if not shipment or shipment.user_id != current_user.user_id:
        raise HTTPException(status_code=404, detail="Shipment not found")

    if not shipment.waybill:
        raise HTTPException(status_code=400, detail="No waybill found for this shipment")

    tracking_data = await track_delhivery_shipment(shipment.waybill)

    now = datetime.now(timezone.utc)
    shipment.tracking_data = tracking_data
    shipment.updated_at = now
    shipment.last_synced_at = now
    try:
        if tracking_data and tracking_data.get("ShipmentData"):
            sd = tracking_data["ShipmentData"][0].get("Shipment", {}) or {}
            status_obj = sd.get("Status") or {}
            status_raw = status_obj.get("Status") or status_obj.get("StatusType") or ""
            instructions = status_obj.get("Instructions") or ""
            shipment.status = map_delhivery_status(instructions or status_raw).value
    except Exception as e:
        logger.warning(f"Failed to extract status from tracking_data: {str(e)}")

    await db.commit()
    return tracking_data


@router.post("/shipments/refresh")
async def refresh_all_shipments(
    current_user: UserOut = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Force-refresh statuses for all of the user's non-final shipments from Delhivery."""
    updated = await sync_user_shipment_statuses(current_user.user_id, db, force=True)
    return {"updated": updated, "message": f"Refreshed {updated} shipment(s)"}


@router.get("/shipments/{shipment_id}/label")
async def get_shipment_label(
    shipment_id: str,
    current_user: UserOut = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate and stream waybill label PDF"""
    shipment = await db.get(ShipmentModel, shipment_id)
    if not shipment or shipment.user_id != current_user.user_id:
        raise HTTPException(status_code=404, detail="Shipment not found")

    if not shipment.waybill:
        raise HTTPException(status_code=400, detail="No waybill found for this shipment")

    try:
        data = await get_packing_slip(shipment.waybill)
        packages = data.get("packages", [])
        if not packages:
            raise HTTPException(status_code=404, detail="No label found for this waybill")

        pdf_link = packages[0].get("pdf_download_link")
        if not pdf_link:
            raise HTTPException(status_code=404, detail="PDF download link not available")

        async with httpx.AsyncClient(timeout=30.0) as http_client:
            pdf_response = await http_client.get(pdf_link)
            pdf_response.raise_for_status()

        return StreamingResponse(
            io.BytesIO(pdf_response.content),
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="label_{shipment.waybill}.pdf"'}
        )
    except HTTPException:
        raise
    except httpx.HTTPError as e:
        logger.error(f"Label download error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to download label: {str(e)}")


@router.get("/shipments/bulk/template")
async def download_bulk_template(current_user: UserOut = Depends(get_current_user)):
    """Download CSV template for bulk shipment upload (weight in grams)"""
    csv_content = """order_id,receiver_name,receiver_phone,receiver_email,receiver_address,receiver_city,receiver_state,receiver_pincode,item_name,item_qty,item_price,hsn_code,payment_mode,cod_amount,weight_grams,length,breadth,height,shipment_type,invoice_number
ORD001,John Doe,9876543210,john@example.com,123 Main Street,Mumbai,Maharashtra,400001,Sample Product,1,999.00,6109,Prepaid,0,500,10,10,10,FWD,INV001
ORD002,Jane Smith,9876543211,jane@example.com,456 Park Road,Delhi,Delhi,110001,Electronics Item,2,1499.00,8517,COD,2998.00,1500,20,15,10,FWD,INV002
RVP001,Return Customer,9876543212,return@example.com,789 Return Lane,Pune,Maharashtra,411001,Defective Item,1,599.00,6109,Prepaid,0,500,10,10,10,RVP,INV003
"""
    return StreamingResponse(
        io.BytesIO(csv_content.encode("utf-8")),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="bulk_shipment_template.csv"'}
    )


@router.post("/shipments/bulk/upload")
async def bulk_upload_shipments(
    file: UploadFile = File(...),
    current_user: UserOut = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload CSV file to create multiple shipments at once.

    NOTE: batches beyond a couple hundred rows can exceed Vercel's Hobby-tier
    function timeout since each row is a sequential Delhivery API call — see
    LIMITS_AND_GOTCHAS.md.
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")

    business_settings = await db.get(SettingsModel, current_user.user_id)
    if not business_settings or not business_settings.sender_name:
        raise HTTPException(
            status_code=400,
            detail="Please configure default sender details in Settings before bulk upload"
        )

    content = await file.read()
    csv_text = content.decode("utf-8")
    reader = csv.DictReader(io.StringIO(csv_text))

    results = {"total": 0, "success": 0, "failed": 0, "shipments": [], "errors": []}

    for row in reader:
        results["total"] += 1
        try:
            if row.get("weight_grams"):
                weight_kg = float(row["weight_grams"]) / 1000.0
            elif row.get("weight"):
                weight_kg = float(row["weight"])
            else:
                weight_kg = 0.5

            order = CreateShipmentRequest(
                order_id=row["order_id"].strip(),
                pickup_location=business_settings.pickup_location or "",
                sender={
                    "name": business_settings.sender_name,
                    "phone": business_settings.sender_phone,
                    "email": business_settings.sender_email or None,
                    "address": business_settings.sender_address,
                    "city": business_settings.sender_city,
                    "state": business_settings.sender_state,
                    "pincode": business_settings.sender_pincode,
                    "country": "India",
                },
                receiver={
                    "name": row["receiver_name"].strip(),
                    "phone": row["receiver_phone"].strip(),
                    "email": row.get("receiver_email", "").strip() or None,
                    "address": row["receiver_address"].strip(),
                    "city": row["receiver_city"].strip(),
                    "state": row["receiver_state"].strip(),
                    "pincode": row["receiver_pincode"].strip(),
                    "country": "India",
                },
                items=[{
                    "name": row["item_name"].strip(),
                    "qty": int(row["item_qty"]),
                    "price": float(row["item_price"]),
                    "hsn_code": row.get("hsn_code", "").strip(),
                }],
                payment_mode=row["payment_mode"].strip(),
                cod_amount=float(row.get("cod_amount", 0) or 0),
                weight=weight_kg,
                length=float(row.get("length", 10) or 10),
                breadth=float(row.get("breadth", 10) or 10),
                height=float(row.get("height", 10) or 10),
                seller_gst=business_settings.seller_gst or "",
                seller_invoice=row.get("invoice_number", "").strip(),
                shipment_type=row.get("shipment_type", "FWD").strip() or "FWD",
            )

            shipment = await _create_shipment_internal(order, current_user.user_id, db)
            results["success"] += 1
            results["shipments"].append({
                "order_id": shipment.order_id,
                "waybill": shipment.waybill,
                "status": shipment.status,
            })
        except Exception as e:
            results["failed"] += 1
            results["errors"].append({
                "order_id": row.get("order_id", "Unknown"),
                "error": str(e)
            })
            logger.error(f"Bulk upload error for {row.get('order_id')}: {str(e)}")

    return results


@router.get("/shipments/bulk/download")
async def bulk_download_shipments(
    status: Optional[ShipmentStatus] = None,
    current_user: UserOut = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Download all shipments for current user as a single CSV file"""
    query = select(ShipmentModel).where(ShipmentModel.user_id == current_user.user_id)
    if status:
        query = query.where(ShipmentModel.status == status.value)
    # Limit to 5000 most recent shipments per export
    query = query.order_by(ShipmentModel.created_at.desc()).limit(5000)

    result = await db.execute(query)
    shipments = result.scalars().all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Order ID", "Waybill", "Status", "Type", "Receiver Name", "Receiver Phone",
        "Receiver Address", "Receiver City", "Receiver State", "Receiver Pincode",
        "Sender Name", "Sender City", "Items", "Weight (g)", "Payment Mode",
        "COD Amount", "Total Amount", "Created Date"
    ])

    for s in shipments:
        items_str = "; ".join([f"{i['name']} (x{i['qty']})" for i in (s.items or [])])
        total_amount = sum([i["price"] * i["qty"] for i in (s.items or [])])
        weight_g = int((s.weight or 0) * 1000)
        writer.writerow([
            s.order_id or "",
            s.waybill or "",
            s.status or "",
            s.shipment_type or "FWD",
            s.receiver["name"],
            s.receiver["phone"],
            s.receiver["address"],
            s.receiver["city"],
            s.receiver["state"],
            s.receiver["pincode"],
            s.sender["name"],
            s.sender["city"],
            items_str,
            weight_g,
            s.payment_mode or "",
            s.cod_amount or 0,
            total_amount,
            s.created_at,
        ])

    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8")),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="shipments_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'}
    )


@router.get("/shipments/bulk/labels")
async def bulk_download_labels(
    waybills: str = Query(..., description="Comma-separated waybill numbers"),
    current_user: UserOut = Depends(get_current_user),
):
    """Download multiple shipping labels merged into a single PDF.

    NOTE: batches beyond ~50-100 waybills can exceed Vercel's Hobby-tier
    function timeout since each label PDF is fetched sequentially — see
    LIMITS_AND_GOTCHAS.md.
    """
    waybill_list = [w.strip() for w in waybills.split(",") if w.strip()]
    if not waybill_list:
        raise HTTPException(status_code=400, detail="No waybills provided")

    try:
        data = await get_packing_slip(",".join(waybill_list))
        packages = data.get("packages", [])
        if not packages:
            raise HTTPException(status_code=404, detail="No labels found for the given waybills")

        merger = PdfWriter()
        merged_count = 0
        async with httpx.AsyncClient(timeout=60.0) as http_client:
            for pkg in packages:
                pdf_link = pkg.get("pdf_download_link")
                if not pdf_link:
                    continue
                pdf_resp = await http_client.get(pdf_link)
                if pdf_resp.status_code != 200 or not pdf_resp.content:
                    continue
                try:
                    reader = PdfReader(io.BytesIO(pdf_resp.content))
                    for page in reader.pages:
                        merger.add_page(page)
                    merged_count += 1
                except Exception as e:
                    logger.warning(f"Skipping unreadable PDF for waybill {pkg.get('wbn')}: {str(e)}")

        if merged_count == 0:
            raise HTTPException(status_code=404, detail="No label PDFs could be fetched from Delhivery")

        output_pdf = io.BytesIO()
        merger.write(output_pdf)
        merger.close()
        output_pdf.seek(0)

        return StreamingResponse(
            output_pdf,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="bulk_labels_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf"'}
        )
    except HTTPException:
        raise
    except httpx.HTTPError as e:
        logger.error(f"Bulk label download error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to download labels: {str(e)}")
