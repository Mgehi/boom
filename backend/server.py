from fastapi import FastAPI, APIRouter, HTTPException, Query, UploadFile, File, Request, Response, Cookie, Depends
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import httpx
from enum import Enum
import csv
import io
import zipfile

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Delhivery Configuration
DELHIVERY_API_KEY = os.environ.get('DELHIVERY_API_KEY', '')
DELHIVERY_BASE_URL = os.environ.get('DELHIVERY_BASE_URL', 'https://track.delhivery.com/api')

# Create the main app
app = FastAPI()
api_router = APIRouter(prefix="/api")

# Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Enums
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

# ============ User & Auth Models ============
class User(BaseModel):
    user_id: str
    email: str
    name: str
    picture: Optional[str] = None
    is_admin: bool = False
    created_at: Optional[datetime] = None

class UserSession(BaseModel):
    user_id: str
    session_token: str
    expires_at: datetime
    created_at: datetime

class AllowedEmail(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    note: Optional[str] = ""
    added_by: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Models
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

class ShipmentType(str, Enum):
    FORWARD = "FWD"
    REVERSE = "RVP"

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

class Shipment(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
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
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class PickupRequest(BaseModel):
    pickup_location: str
    pickup_date: str
    pickup_time: Optional[str] = "10:00:00"
    expected_package_count: int

class Pickup(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None
    pickup_location: str
    pickup_date: str
    pickup_time: str = "10:00:00"
    expected_package_count: int
    status: str = "Scheduled"
    delhivery_response: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class DashboardStats(BaseModel):
    total_shipments: int
    today_shipments: int
    in_transit: int
    delivered: int
    exceptions: int

class BusinessSettings(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None
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
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

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

class PincodeCheckRequest(BaseModel):
    pincode: str

# Delhivery API Functions
async def create_delhivery_shipment(shipment_data: CreateShipmentRequest) -> Dict[str, Any]:
    """Create shipment in Delhivery and get waybill"""
    url = f"{DELHIVERY_BASE_URL}/cmu/create.json"
    
    # Prepare Delhivery payload
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
    import json as json_module
    form_data = {
        "format": "json",
        "data": json_module.dumps(shipment_payload)
    }
    
    headers = {
        "Authorization": f"Token {DELHIVERY_API_KEY}"
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                url,
                data=form_data,
                headers=headers
            )
            response.raise_for_status()
            result = response.json()
            
            # Check if Delhivery accepted the request
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
    
    headers = {
        "Authorization": f"Token {DELHIVERY_API_KEY}"
    }
    
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


# Final statuses that don't need further syncing
FINAL_STATUSES = {ShipmentStatus.DELIVERED.value, ShipmentStatus.RTO.value}
# Auto-sync staleness threshold
SYNC_STALE_SECONDS = 300  # 5 minutes


async def sync_user_shipment_statuses(user_id: str, force: bool = False) -> int:
    """Refresh shipment statuses for the user from Delhivery for non-final, stale shipments.
    Returns count of shipments updated. Best-effort; logs errors but never raises."""
    try:
        query: Dict[str, Any] = {
            "user_id": user_id,
            "waybill": {"$exists": True, "$ne": None},
            "status": {"$nin": list(FINAL_STATUSES)},
        }
        if not force:
            cutoff = (datetime.now(timezone.utc) - timedelta(seconds=SYNC_STALE_SECONDS)).isoformat()
            query["$or"] = [
                {"last_synced_at": {"$exists": False}},
                {"last_synced_at": None},
                {"last_synced_at": {"$lt": cutoff}},
            ]
        
        shipments = await db.shipments.find(query, {"_id": 0, "id": 1, "waybill": 1}).to_list(500)
        if not shipments:
            return 0
        
        waybills = [s["waybill"] for s in shipments if s.get("waybill")]
        if not waybills:
            return 0
        
        # Delhivery supports comma-separated waybills (batch up to ~50 per request to be safe)
        updated = 0
        now_iso = datetime.now(timezone.utc).isoformat()
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
                # Prefer Instructions for finer detail (e.g., "Delivered")
                new_status = map_delhivery_status(instructions or status_raw)
                
                await db.shipments.update_one(
                    {"user_id": user_id, "waybill": awb},
                    {"$set": {
                        "status": new_status.value,
                        "tracking_data": data,
                        "last_synced_at": now_iso,
                        "updated_at": now_iso,
                    }}
                )
                updated += 1
        
        # Mark unmatched (Delhivery didn't return data) as synced too so we don't hammer the API
        await db.shipments.update_many(
            {"user_id": user_id, "waybill": {"$in": waybills}, "last_synced_at": {"$ne": now_iso}},
            {"$set": {"last_synced_at": now_iso}}
        )
        return updated
    except Exception as e:
        logger.error(f"sync_user_shipment_statuses failed: {str(e)}")
        return 0

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
                # Delhivery returns pickup_id on success
                if result.get("pickup_id"):
                    logger.info(f"Pickup scheduled successfully: {result.get('pickup_id')}")
                    return result
                else:
                    # No pickup_id means error
                    error_msg = result.get("error", result.get("detail", "Pickup scheduling failed"))
                    raise HTTPException(status_code=400, detail=f"Delhivery error: {error_msg}")
            else:
                error_text = response.text[:300]
                raise HTTPException(status_code=400, detail=f"Delhivery error: {error_text}")
    except HTTPException:
        raise
    except httpx.HTTPError as e:
        logger.error(f"Pickup scheduling error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Pickup scheduling error: {str(e)}")

# API Endpoints
@api_router.get("/")
async def root():
    return {"message": "Delhivery Logistics Automation API", "status": "running"}

# ============ Public Tracking (no auth) ============
@api_router.get("/track/{waybill}")
async def public_track(waybill: str):
    """Public tracking endpoint - no auth required. Customer-facing."""
    # Look up shipment in our DB (across all users) for order_id/receiver context
    shipment = await db.shipments.find_one(
        {"waybill": waybill},
        {"_id": 0, "order_id": 1, "receiver": 1, "shipment_type": 1, "status": 1, "created_at": 1}
    )
    
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    
    # Fetch live tracking from Delhivery
    try:
        tracking_data = await track_delhivery_shipment(waybill)
    except HTTPException:
        tracking_data = None
    
    # Extract scans / status from Delhivery response
    scans = []
    current_status = shipment.get("status", "Pending")
    edd = None  # expected delivery date
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
        # Reverse so newest first
        scans.reverse()
        current_status = sd.get("Status", {}).get("Status", current_status)
        edd = sd.get("ExpectedDeliveryDate") or sd.get("PromisedDeliveryDate")
        origin = sd.get("Origin", "")
        destination = sd.get("Destination", "")
    
    return {
        "waybill": waybill,
        "order_id": shipment.get("order_id"),
        "receiver_name": shipment["receiver"]["name"],
        "receiver_city": shipment["receiver"]["city"],
        "shipment_type": shipment.get("shipment_type", "FWD"),
        "current_status": current_status,
        "expected_delivery": edd,
        "origin": origin,
        "destination": destination,
        "scans": scans,
        "created_at": shipment.get("created_at"),
    }

# ============ Auth Endpoints ============
async def get_current_user(
    request: Request,
    session_token: Optional[str] = Cookie(None),
) -> User:
    """Get the current authenticated user from cookie or Authorization header."""
    token = session_token
    if not token:
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
    
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    session = await db.user_sessions.find_one({"session_token": token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    expires_at = session["expires_at"]
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Session expired")
    
    user_doc = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    if not user_doc:
        raise HTTPException(status_code=401, detail="User not found")
    
    return User(**user_doc)

@api_router.post("/auth/session")
async def create_session(request: Request, response: Response):
    """Exchange session_id from Emergent Auth for a session_token cookie."""
    session_id = request.headers.get("X-Session-ID")
    if not session_id:
        raise HTTPException(status_code=400, detail="X-Session-ID header required")
    
    # Fetch user data from Emergent Auth
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            auth_resp = await client.get(
                "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data",
                headers={"X-Session-ID": session_id},
            )
            auth_resp.raise_for_status()
            data = auth_resp.json()
    except httpx.HTTPError as e:
        logger.error(f"Auth provider error: {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid session_id")
    
    email = data.get("email")
    name = data.get("name", "")
    picture = data.get("picture", "")
    session_token = data.get("session_token")
    
    if not email or not session_token:
        raise HTTPException(status_code=401, detail="Invalid auth response")
    
    email_lower = email.lower().strip()
    
    # Check if any admin exists
    admin_exists = await db.users.find_one({"is_admin": True})
    
    # Find existing user
    existing = await db.users.find_one({"email": email_lower}, {"_id": 0})
    
    if existing:
        # Existing user - just refresh session
        user_id = existing["user_id"]
        is_admin = existing.get("is_admin", False)
        
        # First sign-in: promote first user to admin (bootstrap)
        if not admin_exists and not is_admin:
            await db.users.update_one(
                {"user_id": user_id},
                {"$set": {"is_admin": True, "name": name, "picture": picture}}
            )
            is_admin = True
            logger.info(f"Bootstrap: promoted {email_lower} to admin (first user)")
        else:
            await db.users.update_one(
                {"user_id": user_id},
                {"$set": {"name": name, "picture": picture}}
            )
    else:
        # New user - check if allowed
        is_admin = False
        if not admin_exists:
            # Bootstrap: no admin yet → this user becomes admin
            is_admin = True
            logger.info(f"Bootstrap: making {email_lower} the first admin")
        else:
            # Admin exists - check whitelist
            allowed = await db.allowed_emails.find_one({"email": email_lower})
            if not allowed:
                logger.warning(f"Access denied for unwhitelisted email: {email_lower}")
                raise HTTPException(
                    status_code=403,
                    detail=f"Access denied. The email '{email}' is not authorized to use this dashboard. Please contact your administrator."
                )
        
        user_id = f"user_{uuid.uuid4().hex[:12]}"
        await db.users.insert_one({
            "user_id": user_id,
            "email": email_lower,
            "name": name,
            "picture": picture,
            "is_admin": is_admin,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
    
    # Save session (7 days)
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    await db.user_sessions.insert_one({
        "user_id": user_id,
        "session_token": session_token,
        "expires_at": expires_at.isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    
    # Set httpOnly cookie
    response.set_cookie(
        key="session_token",
        value=session_token,
        max_age=7 * 24 * 60 * 60,
        path="/",
        httponly=True,
        secure=True,
        samesite="none",
    )
    
    return {
        "user_id": user_id,
        "email": email_lower,
        "name": name,
        "picture": picture,
        "is_admin": is_admin,
    }

@api_router.get("/auth/me", response_model=User)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get the current authenticated user."""
    return current_user

@api_router.post("/auth/logout")
async def logout(response: Response, request: Request, session_token: Optional[str] = Cookie(None)):
    """Logout user - delete session and clear cookie."""
    token = session_token
    if not token:
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
    
    if token:
        await db.user_sessions.delete_one({"session_token": token})
    
    response.delete_cookie(key="session_token", path="/", samesite="none", secure=True)
    return {"success": True}

# ============ Admin Endpoints (Email Whitelist Management) ============
async def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """Require admin privileges."""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

class AddAllowedEmailRequest(BaseModel):
    email: str
    note: Optional[str] = ""

@api_router.get("/admin/allowed-emails")
async def list_allowed_emails(admin: User = Depends(get_admin_user)):
    """List all whitelisted client emails (admin only)."""
    emails = await db.allowed_emails.find({}, {"_id": 0}).sort("created_at", -1).to_list(1000)
    for e in emails:
        if isinstance(e.get("created_at"), str):
            e["created_at"] = datetime.fromisoformat(e["created_at"])
    return emails

@api_router.post("/admin/allowed-emails")
async def add_allowed_email(payload: AddAllowedEmailRequest, admin: User = Depends(get_admin_user)):
    """Add an email to the whitelist (admin only)."""
    email_lower = payload.email.lower().strip()
    if not email_lower or "@" not in email_lower:
        raise HTTPException(status_code=400, detail="Please enter a valid email address")
    
    existing = await db.allowed_emails.find_one({"email": email_lower})
    if existing:
        raise HTTPException(status_code=400, detail=f"{email_lower} is already on the whitelist")
    
    entry = AllowedEmail(email=email_lower, note=payload.note or "", added_by=admin.user_id)
    doc = entry.model_dump()
    doc["created_at"] = doc["created_at"].isoformat()
    await db.allowed_emails.insert_one(doc)
    
    logger.info(f"Admin {admin.email} added {email_lower} to whitelist")
    return entry

@api_router.delete("/admin/allowed-emails/{entry_id}")
async def remove_allowed_email(entry_id: str, admin: User = Depends(get_admin_user)):
    """Remove an email from the whitelist (admin only). User must re-add the email to allow access again."""
    result = await db.allowed_emails.delete_one({"id": entry_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Whitelist entry not found")
    
    logger.info(f"Admin {admin.email} removed entry {entry_id} from whitelist")
    return {"success": True}

@api_router.get("/admin/users")
async def list_registered_users(admin: User = Depends(get_admin_user)):
    """List all registered users with their last activity (admin only)."""
    users = await db.users.find({}, {"_id": 0}).sort("created_at", -1).to_list(1000)
    
    # Add shipment counts per user
    for u in users:
        u["shipment_count"] = await db.shipments.count_documents({"user_id": u["user_id"]})
    
    return users

@api_router.delete("/admin/users/{user_id}")
async def revoke_user(user_id: str, admin: User = Depends(get_admin_user)):
    """Revoke a user's access (delete user + sessions). Their email must also be removed from the whitelist to fully block them."""
    if user_id == admin.user_id:
        raise HTTPException(status_code=400, detail="You cannot revoke your own access")
    
    user = await db.users.find_one({"user_id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.get("is_admin"):
        raise HTTPException(status_code=400, detail="Cannot revoke another admin")
    
    # Delete user account + active sessions
    await db.users.delete_one({"user_id": user_id})
    await db.user_sessions.delete_many({"user_id": user_id})
    
    logger.info(f"Admin {admin.email} revoked user {user.get('email')}")
    return {"success": True, "message": f"User {user.get('email')} has been signed out. Remove their email from the whitelist to prevent re-signup."}

@api_router.post("/orders", response_model=Shipment)
async def receive_order(order: CreateShipmentRequest, current_user: User = Depends(get_current_user)):
    """Webhook endpoint to receive orders from external website and auto-create shipment"""
    try:
        # Create shipment in Delhivery
        delhivery_response = await create_delhivery_shipment(order)
        
        # Extract waybill from response
        waybill = None
        if delhivery_response.get("packages"):
            waybill = delhivery_response["packages"][0].get("waybill")
        
        # Create shipment in our database
        shipment = Shipment(
            user_id=current_user.user_id,
            order_id=order.order_id,
            waybill=waybill,
            pickup_location=order.pickup_location,
            sender=order.sender,
            receiver=order.receiver,
            items=order.items,
            payment_mode=order.payment_mode,
            cod_amount=order.cod_amount,
            weight=order.weight,
            length=order.length,
            breadth=order.breadth,
            height=order.height,
            seller_gst=order.seller_gst,
            seller_invoice=order.seller_invoice,
            shipment_type=order.shipment_type,
            status=ShipmentStatus.MANIFESTED if waybill else ShipmentStatus.PENDING,
            delhivery_response=delhivery_response
        )
        
        doc = shipment.model_dump()
        doc['created_at'] = doc['created_at'].isoformat()
        doc['updated_at'] = doc['updated_at'].isoformat()
        
        await db.shipments.insert_one(doc)
        
        logger.info(f"Order {order.order_id} for user {current_user.user_id} manifested with waybill {waybill}")
        return shipment
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process order: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/shipments", response_model=Shipment)
async def create_shipment_manual(order: CreateShipmentRequest, current_user: User = Depends(get_current_user)):
    """Manually create a shipment"""
    return await receive_order(order, current_user)

@api_router.get("/shipments", response_model=List[Shipment])
async def get_shipments(
    status: Optional[ShipmentStatus] = None,
    limit: int = Query(100, le=500),
    current_user: User = Depends(get_current_user)
):
    """Get all shipments for the current user"""
    # Best-effort sync of stale statuses from Delhivery (throttled)
    await sync_user_shipment_statuses(current_user.user_id)
    
    query = {"user_id": current_user.user_id}
    if status:
        query["status"] = status.value
    
    shipments = await db.shipments.find(query, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
    
    for shipment in shipments:
        if isinstance(shipment['created_at'], str):
            shipment['created_at'] = datetime.fromisoformat(shipment['created_at'])
        if isinstance(shipment['updated_at'], str):
            shipment['updated_at'] = datetime.fromisoformat(shipment['updated_at'])
    
    return shipments

@api_router.get("/shipments/{shipment_id}", response_model=Shipment)
async def get_shipment(shipment_id: str, current_user: User = Depends(get_current_user)):
    """Get shipment by ID (scoped to user)"""
    shipment = await db.shipments.find_one({"id": shipment_id, "user_id": current_user.user_id}, {"_id": 0})
    
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    
    if isinstance(shipment['created_at'], str):
        shipment['created_at'] = datetime.fromisoformat(shipment['created_at'])
    if isinstance(shipment['updated_at'], str):
        shipment['updated_at'] = datetime.fromisoformat(shipment['updated_at'])
    
    return shipment

@api_router.get("/shipments/{shipment_id}/track")
async def track_shipment(shipment_id: str, current_user: User = Depends(get_current_user)):
    """Track shipment using Delhivery API (scoped to user)"""
    shipment = await db.shipments.find_one({"id": shipment_id, "user_id": current_user.user_id}, {"_id": 0})
    
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    
    if not shipment.get("waybill"):
        raise HTTPException(status_code=400, detail="No waybill found for this shipment")
    
    tracking_data = await track_delhivery_shipment(shipment["waybill"])
    
    # Extract latest status and persist it to DB
    update_fields: Dict[str, Any] = {
        "tracking_data": tracking_data,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "last_synced_at": datetime.now(timezone.utc).isoformat(),
    }
    try:
        if tracking_data and tracking_data.get("ShipmentData"):
            sd = tracking_data["ShipmentData"][0].get("Shipment", {}) or {}
            status_obj = sd.get("Status") or {}
            status_raw = status_obj.get("Status") or status_obj.get("StatusType") or ""
            instructions = status_obj.get("Instructions") or ""
            new_status = map_delhivery_status(instructions or status_raw)
            update_fields["status"] = new_status.value
    except Exception as e:
        logger.warning(f"Failed to extract status from tracking_data: {str(e)}")
    
    await db.shipments.update_one(
        {"id": shipment_id, "user_id": current_user.user_id},
        {"$set": update_fields}
    )
    
    return tracking_data


@api_router.post("/shipments/refresh")
async def refresh_all_shipments(current_user: User = Depends(get_current_user)):
    """Force-refresh statuses for all of the user's non-final shipments from Delhivery."""
    updated = await sync_user_shipment_statuses(current_user.user_id, force=True)
    return {"updated": updated, "message": f"Refreshed {updated} shipment(s)"}

@api_router.get("/shipments/{shipment_id}/label")
async def get_shipment_label(shipment_id: str, current_user: User = Depends(get_current_user)):
    """Generate and stream waybill label PDF"""
    shipment = await db.shipments.find_one({"id": shipment_id, "user_id": current_user.user_id}, {"_id": 0})
    
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    
    if not shipment.get("waybill"):
        raise HTTPException(status_code=400, detail="No waybill found for this shipment")
    
    # Step 1: Get the PDF download link from Delhivery
    url = f"{DELHIVERY_BASE_URL}/p/packing_slip"
    params = {"wbns": shipment["waybill"], "pdf": "true"}
    headers = {"Authorization": f"Token {DELHIVERY_API_KEY}"}
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as http_client:
            response = await http_client.get(url, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            packages = data.get("packages", [])
            if not packages:
                raise HTTPException(status_code=404, detail="No label found for this waybill")
            
            pdf_link = packages[0].get("pdf_download_link")
            if not pdf_link:
                raise HTTPException(status_code=404, detail="PDF download link not available")
            
            # Step 2: Fetch the actual PDF from the signed URL
            pdf_response = await http_client.get(pdf_link)
            pdf_response.raise_for_status()
            
            return StreamingResponse(
                io.BytesIO(pdf_response.content),
                media_type="application/pdf",
                headers={"Content-Disposition": f'attachment; filename="label_{shipment["waybill"]}.pdf"'}
            )
    except HTTPException:
        raise
    except httpx.HTTPError as e:
        logger.error(f"Label download error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to download label: {str(e)}")

@api_router.post("/pickups", response_model=Pickup)
async def schedule_pickup(pickup: PickupRequest, current_user: User = Depends(get_current_user)):
    """Schedule a pickup with Delhivery"""
    try:
        delhivery_response = await schedule_delhivery_pickup(pickup)
        
        pickup_obj = Pickup(
            user_id=current_user.user_id,
            pickup_location=pickup.pickup_location,
            pickup_date=pickup.pickup_date,
            pickup_time=pickup.pickup_time or "10:00:00",
            expected_package_count=pickup.expected_package_count,
            delhivery_response=delhivery_response
        )
        
        doc = pickup_obj.model_dump()
        doc['created_at'] = doc['created_at'].isoformat()
        
        await db.pickups.insert_one(doc)
        
        logger.info(f"Pickup scheduled for user {current_user.user_id}: {pickup.pickup_location} on {pickup.pickup_date}")
        return pickup_obj
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to schedule pickup: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/pickups", response_model=List[Pickup])
async def get_pickups(limit: int = Query(100, le=500), current_user: User = Depends(get_current_user)):
    """Get all pickups for the current user"""
    pickups = await db.pickups.find({"user_id": current_user.user_id}, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
    
    for pickup in pickups:
        if isinstance(pickup['created_at'], str):
            pickup['created_at'] = datetime.fromisoformat(pickup['created_at'])
    
    return pickups

@api_router.get("/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats(current_user: User = Depends(get_current_user)):
    """Get dashboard statistics for the current user"""
    # Best-effort sync of stale statuses from Delhivery (throttled)
    await sync_user_shipment_statuses(current_user.user_id)
    
    base_query = {"user_id": current_user.user_id}
    
    total = await db.shipments.count_documents(base_query)
    
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    today = await db.shipments.count_documents({
        **base_query,
        "created_at": {"$gte": today_start.isoformat()}
    })
    
    in_transit = await db.shipments.count_documents({**base_query, "status": ShipmentStatus.IN_TRANSIT.value})
    delivered = await db.shipments.count_documents({**base_query, "status": ShipmentStatus.DELIVERED.value})
    exceptions = await db.shipments.count_documents({**base_query, "status": ShipmentStatus.EXCEPTION.value})
    
    return DashboardStats(
        total_shipments=total,
        today_shipments=today,
        in_transit=in_transit,
        delivered=delivered,
        exceptions=exceptions
    )

# ============ Business Settings (Default Sender) ============
@api_router.get("/settings")
async def get_settings(current_user: User = Depends(get_current_user)):
    """Get business settings (default sender details) for current user"""
    settings = await db.settings.find_one({"user_id": current_user.user_id}, {"_id": 0})
    if not settings:
        return BusinessSettings(user_id=current_user.user_id).model_dump()
    return settings

@api_router.put("/settings")
async def update_settings(settings: BusinessSettings, current_user: User = Depends(get_current_user)):
    """Update business settings for current user"""
    settings.updated_at = datetime.now(timezone.utc)
    settings.user_id = current_user.user_id
    doc = settings.model_dump()
    doc['updated_at'] = doc['updated_at'].isoformat()
    doc['id'] = f"settings_{current_user.user_id}"
    
    await db.settings.update_one(
        {"user_id": current_user.user_id},
        {"$set": doc},
        upsert=True
    )
    return doc

# ============ Pincode Serviceability Check ============
@api_router.get("/pincode/check")
async def check_pincode_serviceability(pincode: str, current_user: User = Depends(get_current_user)):
    """Check if a pincode is serviceable by Delhivery"""
    # Pincode endpoint uses a different base path
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

# ============ Warehouse Registration ============
@api_router.post("/warehouse/register")
async def register_warehouse(warehouse: WarehouseRegistration, current_user: User = Depends(get_current_user)):
    """Register a warehouse/pickup location with Delhivery"""
    url = f"{DELHIVERY_BASE_URL}/backend/clientwarehouse/create/"
    headers = {
        "Authorization": f"Token {DELHIVERY_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Build payload - return fields are required by Delhivery; auto-fill from main address
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
            # Success: "<message>A new client warehouse has been created in HQ(Delhivery).</message>" with <success>True</success>
            # Failure: "<success>False</success>" with error details
            
            is_success = (
                "<success>true</success>" in response_lower or
                "warehouse has been created" in response_lower or
                "successfully" in response_lower
            )
            
            # Warehouse already exists is also a "success" state for our purposes
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
                # Extract a clean error from the XML response
                import re
                error_match = re.search(r"<message>(.*?)</message>", response_text)
                error_msg = error_match.group(1) if error_match else response_text[:300]
                logger.error(f"Warehouse registration failed: {response_text[:500]}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Delhivery rejected: {error_msg}"
                )
    except HTTPException:
        raise
    except httpx.HTTPError as e:
        logger.error(f"Warehouse registration error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to register warehouse: {str(e)}")
    except Exception as e:
        logger.error(f"Warehouse registration unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to register warehouse: {str(e)}")

# ============ Bulk Shipment Upload (CSV) ============
@api_router.get("/shipments/bulk/template")
async def download_bulk_template(current_user: User = Depends(get_current_user)):
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

@api_router.post("/shipments/bulk/upload")
async def bulk_upload_shipments(file: UploadFile = File(...), current_user: User = Depends(get_current_user)):
    """Upload CSV file to create multiple shipments at once"""
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")
    
    # Get default sender settings for current user
    settings = await db.settings.find_one({"user_id": current_user.user_id}, {"_id": 0})
    if not settings or not settings.get("sender_name"):
        raise HTTPException(
            status_code=400,
            detail="Please configure default sender details in Settings before bulk upload"
        )
    
    content = await file.read()
    csv_text = content.decode("utf-8")
    reader = csv.DictReader(io.StringIO(csv_text))
    
    results = {
        "total": 0,
        "success": 0,
        "failed": 0,
        "shipments": [],
        "errors": []
    }
    
    for row in reader:
        results["total"] += 1
        try:
            # Weight: support both new 'weight_grams' (preferred) and legacy 'weight' (kg)
            if row.get("weight_grams"):
                weight_kg = float(row["weight_grams"]) / 1000.0
            elif row.get("weight"):
                weight_kg = float(row["weight"])
            else:
                weight_kg = 0.5
            
            order = CreateShipmentRequest(
                order_id=row["order_id"].strip(),
                pickup_location=settings.get("pickup_location", ""),
                sender=Address(
                    name=settings["sender_name"],
                    phone=settings["sender_phone"],
                    email=settings.get("sender_email") or None,
                    address=settings["sender_address"],
                    city=settings["sender_city"],
                    state=settings["sender_state"],
                    pincode=settings["sender_pincode"],
                    country="India"
                ),
                receiver=Address(
                    name=row["receiver_name"].strip(),
                    phone=row["receiver_phone"].strip(),
                    email=row.get("receiver_email", "").strip() or None,
                    address=row["receiver_address"].strip(),
                    city=row["receiver_city"].strip(),
                    state=row["receiver_state"].strip(),
                    pincode=row["receiver_pincode"].strip(),
                    country="India"
                ),
                items=[OrderItem(
                    name=row["item_name"].strip(),
                    qty=int(row["item_qty"]),
                    price=float(row["item_price"]),
                    hsn_code=row.get("hsn_code", "").strip()
                )],
                payment_mode=PaymentMode(row["payment_mode"].strip()),
                cod_amount=float(row.get("cod_amount", 0) or 0),
                weight=weight_kg,
                length=float(row.get("length", 10) or 10),
                breadth=float(row.get("breadth", 10) or 10),
                height=float(row.get("height", 10) or 10),
                seller_gst=settings.get("seller_gst", "") or "",
                seller_invoice=row.get("invoice_number", "").strip(),
                shipment_type=ShipmentType(row.get("shipment_type", "FWD").strip() or "FWD")
            )
            
            shipment = await _create_shipment_internal(order, current_user.user_id)
            results["success"] += 1
            results["shipments"].append({
                "order_id": shipment.order_id,
                "waybill": shipment.waybill,
                "status": shipment.status.value
            })
        except Exception as e:
            results["failed"] += 1
            results["errors"].append({
                "order_id": row.get("order_id", "Unknown"),
                "error": str(e)
            })
            logger.error(f"Bulk upload error for {row.get('order_id')}: {str(e)}")
    
    return results

@api_router.get("/shipments/bulk/download")
async def bulk_download_shipments(status: Optional[ShipmentStatus] = None, current_user: User = Depends(get_current_user)):
    """Download all shipments for current user as a single CSV file"""
    query = {"user_id": current_user.user_id}
    if status:
        query["status"] = status.value
    
    # Limit to 5000 most recent shipments per export with field projection for performance
    projection = {
        "_id": 0,
        "order_id": 1, "waybill": 1, "status": 1, "shipment_type": 1,
        "receiver": 1, "sender": 1, "items": 1, "weight": 1,
        "payment_mode": 1, "cod_amount": 1, "created_at": 1,
    }
    shipments = await db.shipments.find(query, projection).sort("created_at", -1).limit(5000).to_list(5000)
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Order ID", "Waybill", "Status", "Type", "Receiver Name", "Receiver Phone",
        "Receiver Address", "Receiver City", "Receiver State", "Receiver Pincode",
        "Sender Name", "Sender City", "Items", "Weight (g)", "Payment Mode",
        "COD Amount", "Total Amount", "Created Date"
    ])
    
    for s in shipments:
        items_str = "; ".join([f"{i['name']} (x{i['qty']})" for i in s.get("items", [])])
        total_amount = sum([i["price"] * i["qty"] for i in s.get("items", [])])
        weight_g = int(s.get("weight", 0) * 1000)
        writer.writerow([
            s.get("order_id", ""),
            s.get("waybill", ""),
            s.get("status", ""),
            s.get("shipment_type", "FWD"),
            s["receiver"]["name"],
            s["receiver"]["phone"],
            s["receiver"]["address"],
            s["receiver"]["city"],
            s["receiver"]["state"],
            s["receiver"]["pincode"],
            s["sender"]["name"],
            s["sender"]["city"],
            items_str,
            weight_g,
            s.get("payment_mode", ""),
            s.get("cod_amount", 0),
            total_amount,
            s.get("created_at", "")
        ])
    
    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8")),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="shipments_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'}
    )

@api_router.get("/shipments/bulk/labels")
async def bulk_download_labels(waybills: str = Query(..., description="Comma-separated waybill numbers"), current_user: User = Depends(get_current_user)):
    """Download multiple shipping labels as a single PDF (combined)"""
    waybill_list = [w.strip() for w in waybills.split(",") if w.strip()]
    
    if not waybill_list:
        raise HTTPException(status_code=400, detail="No waybills provided")
    
    # Delhivery supports comma-separated waybills, returns JSON with PDF links per package
    url = f"{DELHIVERY_BASE_URL}/p/packing_slip"
    params = {"wbns": ",".join(waybill_list), "pdf": "true"}
    headers = {"Authorization": f"Token {DELHIVERY_API_KEY}"}
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as http_client:
            response = await http_client.get(url, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            packages = data.get("packages", [])
            if not packages:
                raise HTTPException(status_code=404, detail="No labels found for the given waybills")
            
            # Fetch all PDFs and combine them into a ZIP for download
            output_zip = io.BytesIO()
            with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as zf:
                for pkg in packages:
                    pdf_link = pkg.get("pdf_download_link")
                    waybill = pkg.get("wbn", "unknown")
                    if pdf_link:
                        pdf_resp = await http_client.get(pdf_link)
                        if pdf_resp.status_code == 200:
                            zf.writestr(f"label_{waybill}.pdf", pdf_resp.content)
            
            output_zip.seek(0)
            return StreamingResponse(
                output_zip,
                media_type="application/zip",
                headers={"Content-Disposition": f'attachment; filename="bulk_labels_{datetime.now().strftime("%Y%m%d_%H%M%S")}.zip"'}
            )
    except HTTPException:
        raise
    except httpx.HTTPError as e:
        logger.error(f"Bulk label download error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to download labels: {str(e)}")

# Helper for bulk upload
async def _create_shipment_internal(order: CreateShipmentRequest, user_id: str) -> Shipment:
    """Internal helper to create a shipment"""
    delhivery_response = await create_delhivery_shipment(order)
    
    waybill = None
    if delhivery_response.get("packages"):
        waybill = delhivery_response["packages"][0].get("waybill")
    
    shipment = Shipment(
        user_id=user_id,
        order_id=order.order_id,
        waybill=waybill,
        pickup_location=order.pickup_location,
        sender=order.sender,
        receiver=order.receiver,
        items=order.items,
        payment_mode=order.payment_mode,
        cod_amount=order.cod_amount,
        weight=order.weight,
        length=order.length,
        breadth=order.breadth,
        height=order.height,
        seller_gst=order.seller_gst,
        seller_invoice=order.seller_invoice,
        shipment_type=order.shipment_type,
        status=ShipmentStatus.MANIFESTED if waybill else ShipmentStatus.PENDING,
        delhivery_response=delhivery_response
    )
    
    doc = shipment.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['updated_at'] = doc['updated_at'].isoformat()
    await db.shipments.insert_one(doc)
    
    return shipment

# Include router
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()