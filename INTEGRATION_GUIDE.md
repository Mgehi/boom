# Delhivery Logistics Automation System

An automated logistics management system that integrates with Delhivery API to streamline shipment creation, tracking, and pickup scheduling for small businesses.

## Features

### 🚀 Automated Shipment Processing
- **Webhook Integration**: Receive orders from your e-commerce website and automatically create shipments in Delhivery
- **Manual Shipment Creation**: Create shipments through an intuitive web form
- **Real-time Status Updates**: Track shipments and view current status
- **Waybill Generation**: Automatically generate and download shipping labels

### 📊 Dashboard & Reporting
- **Live Statistics**: Monitor today's shipments, in-transit packages, delivered orders, and exceptions
- **Shipment History**: View all shipments with advanced filtering by status
- **Detailed View**: Access complete shipment information including sender, receiver, and package details

### 📦 Pickup Management
- **Schedule Pickups**: Request pickups directly through the dashboard
- **Pickup History**: Track all scheduled pickups

### ⚙️ API Integration
- **RESTful API**: Complete API for programmatic access
- **Webhook Endpoint**: `/api/orders` - Auto-create shipments from external systems
- **Tracking API**: Real-time tracking through Delhivery
- **Label Generation**: Download shipping labels programmatically

## Tech Stack

**Backend:**
- FastAPI (Python)
- MongoDB (Database)
- HTTPx (HTTP client for Delhivery API)
- Pydantic (Data validation)

**Frontend:**
- React 18
- React Router (Navigation)
- Axios (HTTP client)
- Tailwind CSS (Styling)
- Shadcn/UI (Components)
- Sonner (Toast notifications)

## API Documentation

### Webhook Endpoint

**POST** `/api/orders`

Automatically creates a shipment in Delhivery when an order is received.

**Request Body:**
```json
{
  "order_id": "ORD12345",
  "pickup_location": "Mumbai_Warehouse",
  "sender": {
    "name": "Business Name",
    "phone": "9876543210",
    "address": "123 Street",
    "city": "Mumbai",
    "state": "Maharashtra",
    "pincode": "400001",
    "country": "India"
  },
  "receiver": {
    "name": "Customer Name",
    "phone": "9876543211",
    "email": "customer@email.com",
    "address": "456 Street",
    "city": "Delhi",
    "state": "Delhi",
    "pincode": "110001",
    "country": "India"
  },
  "items": [
    {
      "name": "Product Name",
      "qty": 1,
      "price": 999.00
    }
  ],
  "payment_mode": "Prepaid",
  "cod_amount": 0,
  "weight": 0.5,
  "length": 10,
  "breadth": 10,
  "height": 10
}
```

### Other API Endpoints

- **GET** `/api/shipments` - List all shipments (optional: `?status=Delivered`)
- **GET** `/api/shipments/{id}` - Get shipment details
- **GET** `/api/shipments/{id}/track` - Track shipment
- **GET** `/api/shipments/{id}/label` - Get waybill label URL
- **POST** `/api/pickups` - Schedule a pickup
- **GET** `/api/pickups` - List all pickups
- **GET** `/api/dashboard/stats` - Get dashboard statistics

## Integration Guide

### E-commerce Website Integration

1. **Copy the webhook URL** from Settings page
2. **Configure your e-commerce platform** to POST order data to the webhook
3. **Map order fields** to the API payload format
4. **Handle response** - You'll receive the waybill number and shipment status

## Delhivery API Notes

### Important Configuration

1. **Pickup Location**: Must match the registered warehouse name in your Delhivery account exactly
2. **API Key**: Contact Delhivery to activate your API key for production use
3. **Testing**: The provided test API key may have limited functionality - contact Delhivery support for full access

### Common Issues

- **"Warehouse not registered"**: Ensure your pickup location matches the exact name registered with Delhivery
- **No waybill returned**: Check if your API key has proper permissions and the warehouse is configured
