import json as json_module
import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict

import httpx
from fastapi import HTTPException

from app.core.config import settings
from app.schemas.pickup import PickupRequest
from app.schemas.shipment import CreateShipmentRequest, PaymentMode, ShipmentStatus
from app.schemas.misc import WarehouseRegistration

logger = logging.getLogger(__name__)

DELHIVERY_API_KEY = settings.DELHIVERY_API_KEY
DELHIVERY_BASE_URL = settings.DELHIVERY_BASE_URL


async def create_delhivery_shipment(shipment_data: CreateShipmentRequest) -> Dict[str, Any]:
    """Create shipment in Delhivery and get waybill"""
    url = f"{DELHIVERY_BASE_URL}/cmu/create.json"

    # pickup_location must only contain the warehouse name (must be pre-registered in Delhivery)
    # Extra fields cause "ClientWarehouse matching query does not exist." errors
    # Weight is in GRAMS for Delhivery (input is kg, multiply by 1000)
    # For reverse shipment (RVP): pickup is FROM the receiver TO the warehouse

    weight_grams = int(shipment_data.weight * 1000)
    hsn_codes = ",".join([item.hsn_code or "" for item in shipment_data.items])

    shipment_payload = {
        "shipments": [{
            "name": shipment_data.receiver.name,
            "add": shipment_data.receiver.address,
            "pin": shipment_data.receiver.pincode,
            "city": shipment_data.receiver.city,
            "state": shipment_data.receiver.state,
            "country": shipment_data.receiver.country,
            "phone": shipment_data.receiver.phone,
            "order": shipment_data.order_id,
            "payment_mode": shipment_data.payment_mode.value,
            "return_pin": shipment_data.sender.pincode,
            "return_city": shipment_data.sender.city,
            "return_phone": shipment_data.sender.phone,
            "return_add": shipment_data.sender.address,
            "return_state": shipment_data.sender.state,
            "return_country": shipment_data.sender.country,
            "products_desc": ", ".join([item.name for item in shipment_data.items]),
            "hsn_code": hsn_codes,
            "cod_amount": str(shipment_data.cod_amount) if shipment_data.payment_mode == PaymentMode.COD else "0",
            "order_date": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
            "total_amount": str(sum([item.price * item.qty for item in shipment_data.items])),
            "seller_add": shipment_data.sender.address,
            "seller_name": shipment_data.sender.name,
            "seller_inv": shipment_data.seller_invoice or "",
            "quantity": str(sum([item.qty for item in shipment_data.items])),
            "waybill": "",
            "shipment_width": str(int(shipment_data.breadth)),
            "shipment_height": str(int(shipment_data.height)),
            "shipment_length": str(int(shipment_data.length)),
            "weight": str(weight_grams),
            "seller_gst_tin": shipment_data.seller_gst or "",
            "shipping_mode": "Surface",
            "address_type": "home",
            "pickup_type": shipment_data.shipment_type.value
        }],
        "pickup_location": {
            "name": shipment_data.pickup_location
        }
    }

    # Delhivery expects form-encoded data, not JSON
    form_data = {
        "format": "json",
        "data": json_module.dumps(shipment_payload)
    }

    headers = {"Authorization": f"Token {DELHIVERY_API_KEY}"}

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, data=form_data, headers=headers)
            response.raise_for_status()
            result = response.json()

            if not result.get("success", False):
                error_msg = result.get("rmk", "Delhivery rejected the shipment")
                logger.error(f"Delhivery API rejected shipment: {error_msg}")
                raise HTTPException(status_code=400, detail=f"Delhivery error: {error_msg}")

            return result
    except httpx.HTTPError as e:
        logger.error(f"Delhivery API error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Delhivery API error: {str(e)}")


async def track_delhivery_shipment(waybill: str) -> Dict[str, Any]:
    """Track shipment using Delhivery API. `waybill` can be a single AWB or comma-separated AWBs."""
    url = f"{DELHIVERY_BASE_URL}/v1/packages/json/"
    headers = {"Authorization": f"Token {DELHIVERY_API_KEY}"}
    params = {"waybill": waybill}

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        logger.error(f"Tracking API error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Tracking API error: {str(e)}")


def map_delhivery_status(status_str: str) -> ShipmentStatus:
    """Map Delhivery status string to our ShipmentStatus enum."""
    if not status_str:
        return ShipmentStatus.MANIFESTED
    s = str(status_str).strip().lower()
    if "deliver" in s and "out for" not in s and "not deliver" not in s and "un" not in s:
        return ShipmentStatus.DELIVERED
    if "out for delivery" in s or s == "ofd":
        return ShipmentStatus.OUT_FOR_DELIVERY
    if "rto" in s or "return" in s:
        return ShipmentStatus.RTO
    if "in transit" in s or "dispatched" in s or "in-transit" in s or "intransit" in s:
        return ShipmentStatus.IN_TRANSIT
    if "manifest" in s:
        return ShipmentStatus.MANIFESTED
    if "pending" in s:
        return ShipmentStatus.PENDING
    if "exception" in s or "ndr" in s or "fail" in s or "undeliver" in s:
        return ShipmentStatus.EXCEPTION
    return ShipmentStatus.MANIFESTED


async def schedule_delhivery_pickup(pickup_data: PickupRequest) -> Dict[str, Any]:
    """Schedule pickup with Delhivery"""
    # Pickup endpoint does NOT include /api prefix and uses JSON (not form-encoded)
    base = DELHIVERY_BASE_URL.replace("/api", "")
    url = f"{base}/fm/request/new/"

    headers = {
        "Authorization": f"Token {DELHIVERY_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "pickup_location": pickup_data.pickup_location,
        "pickup_date": pickup_data.pickup_date,
        "pickup_time": pickup_data.pickup_time or "10:00:00",
        "expected_package_count": pickup_data.expected_package_count
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)

            if response.status_code in [200, 201]:
                result = response.json()
                if result.get("pickup_id"):
                    logger.info(f"Pickup scheduled successfully: {result.get('pickup_id')}")
                    return result
                else:
                    error_msg = result.get("error", result.get("detail", "Pickup scheduling failed"))
                    logger.error(f"Pickup scheduling failed: {error_msg}")
                    if "wallet balance" in str(error_msg).lower():
                        raise HTTPException(status_code=400, detail="Pickup scheduling failed: insufficient wallet balance")
                    raise HTTPException(status_code=400, detail=f"Delhivery error: {error_msg}")
            else:
                error_text = response.text[:300]
                logger.error(f"Pickup scheduling failed ({response.status_code}): {error_text}")
                if "wallet balance" in error_text.lower():
                    raise HTTPException(status_code=400, detail="Pickup scheduling failed: insufficient wallet balance")
                raise HTTPException(status_code=400, detail=f"Delhivery error: {error_text}")
    except HTTPException:
        raise
    except httpx.HTTPError as e:
        logger.error(f"Pickup scheduling error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Pickup scheduling error: {str(e)}")


async def register_delhivery_warehouse(warehouse: WarehouseRegistration) -> Dict[str, Any]:
    """Register a warehouse/pickup location with Delhivery"""
    url = f"{DELHIVERY_BASE_URL}/backend/clientwarehouse/create/"
    headers = {
        "Authorization": f"Token {DELHIVERY_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "name": warehouse.name,
        "email": warehouse.email,
        "phone": warehouse.phone,
        "address": warehouse.address,
        "city": warehouse.city,
        "country": warehouse.country,
        "pin": warehouse.pin,
        "return_address": warehouse.return_address or warehouse.address,
        "return_pin": warehouse.return_pin or warehouse.pin,
        "return_city": warehouse.return_city or warehouse.city,
        "return_state": warehouse.return_state or warehouse.state,
        "return_country": warehouse.country,
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as http_client:
            response = await http_client.post(url, json=payload, headers=headers)
            response_text = response.text
            response_lower = response_text.lower()

            # Delhivery returns XML for warehouse endpoints
            is_success = (
                "<success>true</success>" in response_lower or
                "warehouse has been created" in response_lower or
                "successfully" in response_lower
            )
            already_exists = "already exists" in response_lower

            if is_success:
                logger.info(f"Warehouse {warehouse.name} registered with Delhivery")
                return {
                    "success": True,
                    "message": f"Warehouse '{warehouse.name}' registered successfully with Delhivery",
                }
            elif already_exists:
                logger.info(f"Warehouse {warehouse.name} already exists in Delhivery")
                return {
                    "success": True,
                    "message": f"Warehouse '{warehouse.name}' is already registered with Delhivery and ready to use",
                    "already_exists": True
                }
            else:
                error_match = re.search(r"<message>(.*?)</message>", response_text)
                error_msg = error_match.group(1) if error_match else response_text[:300]
                logger.error(f"Warehouse registration failed: {response_text[:500]}")
                raise HTTPException(status_code=400, detail=f"Delhivery rejected: {error_msg}")
    except HTTPException:
        raise
    except httpx.HTTPError as e:
        logger.error(f"Warehouse registration error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to register warehouse: {str(e)}")
    except Exception as e:
        logger.error(f"Warehouse registration unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to register warehouse: {str(e)}")


async def check_pincode_serviceability(pincode: str) -> Dict[str, Any]:
    """Check if a pincode is serviceable by Delhivery"""
    base = DELHIVERY_BASE_URL.replace("/api", "")
    url = f"{base}/c/api/pin-codes/json/"
    headers = {"Authorization": f"Token {DELHIVERY_API_KEY}"}
    params = {"filter_codes": pincode}

    try:
        async with httpx.AsyncClient(timeout=15.0) as http_client:
            response = await http_client.get(url, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()

            delivery_codes = data.get("delivery_codes", [])
            if not delivery_codes:
                return {
                    "pincode": pincode,
                    "serviceable": False,
                    "message": f"Pincode {pincode} is not serviceable"
                }

            postal_code = delivery_codes[0].get("postal_code", {})
            return {
                "pincode": pincode,
                "serviceable": True,
                "city": postal_code.get("city", ""),
                "state": postal_code.get("state_code", ""),
                "district": postal_code.get("district", ""),
                "cod_available": postal_code.get("cod") == "Y",
                "prepaid_available": postal_code.get("pre_paid") == "Y",
                "pickup_available": postal_code.get("pickup") == "Y",
                "country": postal_code.get("country_code", "IN"),
                "raw_data": postal_code
            }
    except httpx.HTTPError as e:
        logger.error(f"Pincode check error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to check pincode: {str(e)}")


async def get_packing_slip(waybills: str) -> Dict[str, Any]:
    """Fetch packing-slip metadata (incl. pdf_download_link per package) for one or more waybills."""
    url = f"{DELHIVERY_BASE_URL}/p/packing_slip"
    params = {"wbns": waybills, "pdf": "true"}
    headers = {"Authorization": f"Token {DELHIVERY_API_KEY}"}

    async with httpx.AsyncClient(timeout=30.0) as http_client:
        response = await http_client.get(url, params=params, headers=headers)
        response.raise_for_status()
        return response.json()
