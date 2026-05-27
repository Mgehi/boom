from fastapi import FastAPI, APIRouter, HTTPException, Query
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone
import httpx
from enum import Enum

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

class CreateShipmentRequest(BaseModel):
    order_id: str
    pickup_location: str
    sender: Address
    receiver: Address
    items: List[OrderItem]
    payment_mode: PaymentMode
    cod_amount: Optional[float] = 0
    weight: float
    length: Optional[float] = 10
    breadth: Optional[float] = 10
    height: Optional[float] = 10

class Shipment(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
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
    status: ShipmentStatus = ShipmentStatus.PENDING
    delhivery_response: Optional[Dict[str, Any]] = None
    tracking_data: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class PickupRequest(BaseModel):
    pickup_location: str
    pickup_date: str
    pickup_time: str
    expected_package_count: int

class Pickup(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    pickup_location: str
    pickup_date: str
    pickup_time: str
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

# Delhivery API Functions
async def create_delhivery_shipment(shipment_data: CreateShipmentRequest) -> Dict[str, Any]:
    """Create shipment in Delhivery and get waybill"""
    url = f"{DELHIVERY_BASE_URL}/cmu/create.json"
    
    # Prepare Delhivery payload
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
            "hsn_code": "",
            "cod_amount": str(shipment_data.cod_amount) if shipment_data.payment_mode == PaymentMode.COD else "0",
            "order_date": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
            "total_amount": str(sum([item.price * item.qty for item in shipment_data.items])),
            "seller_add": shipment_data.sender.address,
            "seller_name": shipment_data.sender.name,
            "seller_inv": "",
            "quantity": str(sum([item.qty for item in shipment_data.items])),
            "waybill": "",
            "shipment_width": str(shipment_data.breadth),
            "shipment_height": str(shipment_data.height),
            "weight": str(shipment_data.weight),
            "seller_gst_tin": "",
            "shipping_mode": "Surface",
            "address_type": "home"
        }]
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
    """Track shipment using Delhivery API"""
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

async def schedule_delhivery_pickup(pickup_data: PickupRequest) -> Dict[str, Any]:
    """Schedule pickup with Delhivery"""
    url = f"{DELHIVERY_BASE_URL}/fm/request/new/"
    
    headers = {
        "Authorization": f"Token {DELHIVERY_API_KEY}"
    }
    
    # Form-encoded data for Delhivery
    form_data = {
        "pickup_location": pickup_data.pickup_location,
        "pickup_date": pickup_data.pickup_date,
        "pickup_time": pickup_data.pickup_time,
        "expected_package_count": str(pickup_data.expected_package_count)
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, data=form_data, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            # Check if Delhivery accepted the pickup request
            if not result.get("success", False):
                error_msg = result.get("error", "Delhivery rejected the pickup request")
                logger.error(f"Delhivery pickup API error: {error_msg}")
                raise HTTPException(status_code=400, detail=f"Delhivery error: {error_msg}")
            
            return result
    except httpx.HTTPError as e:
        logger.error(f"Pickup scheduling error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Pickup scheduling error: {str(e)}")

# API Endpoints
@api_router.get("/")
async def root():
    return {"message": "Delhivery Logistics Automation API", "status": "running"}

@api_router.post("/orders", response_model=Shipment)
async def receive_order(order: CreateShipmentRequest):
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
            status=ShipmentStatus.MANIFESTED if waybill else ShipmentStatus.PENDING,
            delhivery_response=delhivery_response
        )
        
        doc = shipment.model_dump()
        doc['created_at'] = doc['created_at'].isoformat()
        doc['updated_at'] = doc['updated_at'].isoformat()
        
        await db.shipments.insert_one(doc)
        
        logger.info(f"Order {order.order_id} automatically manifested with waybill {waybill}")
        return shipment
        
    except Exception as e:
        logger.error(f"Failed to process order: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/shipments", response_model=Shipment)
async def create_shipment_manual(order: CreateShipmentRequest):
    """Manually create a shipment"""
    return await receive_order(order)

@api_router.get("/shipments", response_model=List[Shipment])
async def get_shipments(
    status: Optional[ShipmentStatus] = None,
    limit: int = Query(100, le=500)
):
    """Get all shipments with optional status filter"""
    query = {}
    if status:
        query["status"] = status.value
    
    shipments = await db.shipments.find(query, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
    
    # Convert ISO strings back to datetime
    for shipment in shipments:
        if isinstance(shipment['created_at'], str):
            shipment['created_at'] = datetime.fromisoformat(shipment['created_at'])
        if isinstance(shipment['updated_at'], str):
            shipment['updated_at'] = datetime.fromisoformat(shipment['updated_at'])
    
    return shipments

@api_router.get("/shipments/{shipment_id}", response_model=Shipment)
async def get_shipment(shipment_id: str):
    """Get shipment by ID"""
    shipment = await db.shipments.find_one({"id": shipment_id}, {"_id": 0})
    
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    
    if isinstance(shipment['created_at'], str):
        shipment['created_at'] = datetime.fromisoformat(shipment['created_at'])
    if isinstance(shipment['updated_at'], str):
        shipment['updated_at'] = datetime.fromisoformat(shipment['updated_at'])
    
    return shipment

@api_router.get("/shipments/{shipment_id}/track")
async def track_shipment(shipment_id: str):
    """Track shipment using Delhivery API"""
    shipment = await db.shipments.find_one({"id": shipment_id}, {"_id": 0})
    
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    
    if not shipment.get("waybill"):
        raise HTTPException(status_code=400, detail="No waybill found for this shipment")
    
    # Get tracking data from Delhivery
    tracking_data = await track_delhivery_shipment(shipment["waybill"])
    
    # Update tracking data in database
    await db.shipments.update_one(
        {"id": shipment_id},
        {
            "$set": {
                "tracking_data": tracking_data,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    return tracking_data

@api_router.get("/shipments/{shipment_id}/label")
async def get_shipment_label(shipment_id: str):
    """Generate and get waybill label URL"""
    shipment = await db.shipments.find_one({"id": shipment_id}, {"_id": 0})
    
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    
    if not shipment.get("waybill"):
        raise HTTPException(status_code=400, detail="No waybill found for this shipment")
    
    # Delhivery label URL format
    label_url = f"{DELHIVERY_BASE_URL}/api/p/packing_slip?wbns={shipment['waybill']}&pdf=true"
    
    return {
        "waybill": shipment["waybill"],
        "label_url": label_url,
        "message": "Use this URL to download the shipping label"
    }

@api_router.post("/pickups", response_model=Pickup)
async def schedule_pickup(pickup: PickupRequest):
    """Schedule a pickup with Delhivery"""
    try:
        # Schedule pickup with Delhivery
        delhivery_response = await schedule_delhivery_pickup(pickup)
        
        # Save pickup in database
        pickup_obj = Pickup(
            pickup_location=pickup.pickup_location,
            pickup_date=pickup.pickup_date,
            pickup_time=pickup.pickup_time,
            expected_package_count=pickup.expected_package_count,
            delhivery_response=delhivery_response
        )
        
        doc = pickup_obj.model_dump()
        doc['created_at'] = doc['created_at'].isoformat()
        
        await db.pickups.insert_one(doc)
        
        logger.info(f"Pickup scheduled for {pickup.pickup_location} on {pickup.pickup_date}")
        return pickup_obj
        
    except Exception as e:
        logger.error(f"Failed to schedule pickup: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/pickups", response_model=List[Pickup])
async def get_pickups(limit: int = Query(100, le=500)):
    """Get all pickups"""
    pickups = await db.pickups.find({}, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
    
    for pickup in pickups:
        if isinstance(pickup['created_at'], str):
            pickup['created_at'] = datetime.fromisoformat(pickup['created_at'])
    
    return pickups

@api_router.get("/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats():
    """Get dashboard statistics"""
    total = await db.shipments.count_documents({})
    
    # Today's shipments
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    today = await db.shipments.count_documents({
        "created_at": {"$gte": today_start.isoformat()}
    })
    
    # Status counts
    in_transit = await db.shipments.count_documents({"status": ShipmentStatus.IN_TRANSIT.value})
    delivered = await db.shipments.count_documents({"status": ShipmentStatus.DELIVERED.value})
    exceptions = await db.shipments.count_documents({"status": ShipmentStatus.EXCEPTION.value})
    
    return DashboardStats(
        total_shipments=total,
        today_shipments=today,
        in_transit=in_transit,
        delivered=delivered,
        exceptions=exceptions
    )

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