"""Backend API tests for Delhivery Logistics Automation (Iteration 2)."""
import os
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL').rstrip('/')
API = f"{BASE_URL}/api"


@pytest.fixture(scope="module")
def session():
    s = requests.Session()
    return s


# --- Health / Root ---
def test_root(session):
    r = session.get(f"{API}/")
    assert r.status_code == 200
    assert r.json().get("status") == "running"


# --- Dashboard Stats ---
def test_dashboard_stats(session):
    r = session.get(f"{API}/dashboard/stats")
    assert r.status_code == 200
    data = r.json()
    for k in ["total_shipments", "today_shipments", "in_transit", "delivered", "exceptions"]:
        assert k in data
        assert isinstance(data[k], int)


# --- List Shipments ---
def test_list_shipments(session):
    r = session.get(f"{API}/shipments")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


# --- 404 cases ---
def test_get_shipment_not_found(session):
    r = session.get(f"{API}/shipments/nonexistent-id-12345")
    assert r.status_code == 404


def test_track_shipment_not_found(session):
    r = session.get(f"{API}/shipments/nonexistent-id-12345/track")
    assert r.status_code == 404


def test_label_shipment_not_found(session):
    r = session.get(f"{API}/shipments/nonexistent-id-12345/label")
    assert r.status_code == 404


# --- Pincode Serviceability Check ---
def test_pincode_check_serviceable(session):
    r = session.get(f"{API}/pincode/check", params={"pincode": "110001"})
    assert r.status_code == 200, r.text[:300]
    data = r.json()
    assert data["pincode"] == "110001"
    assert "serviceable" in data
    if data["serviceable"]:
        assert "city" in data
        assert "state" in data
        assert "cod_available" in data
        assert "prepaid_available" in data
        assert "pickup_available" in data


def test_pincode_check_non_serviceable(session):
    r = session.get(f"{API}/pincode/check", params={"pincode": "999999"})
    assert r.status_code == 200, r.text[:300]
    data = r.json()
    assert data["pincode"] == "999999"
    assert data["serviceable"] is False


# --- Business Settings (Default Sender) ---
def test_get_settings_initial(session):
    r = session.get(f"{API}/settings")
    assert r.status_code == 200
    data = r.json()
    # required keys
    for k in ["business_name", "sender_name", "sender_phone", "sender_address",
              "sender_city", "sender_state", "sender_pincode", "pickup_location"]:
        assert k in data


def test_update_settings_persist(session):
    payload = {
        "business_name": "TEST_ITER2_Business",
        "sender_name": "TEST_ITER2 Sender",
        "sender_phone": "9999900000",
        "sender_email": "sender@test.com",
        "sender_address": "1 Test Lane",
        "sender_city": "Bangalore",
        "sender_state": "Karnataka",
        "sender_pincode": "560001",
        "pickup_location": "TestWarehouse"
    }
    r = session.put(f"{API}/settings", json=payload)
    assert r.status_code == 200, r.text[:300]
    saved = r.json()
    assert saved["business_name"] == payload["business_name"]
    assert saved["sender_name"] == payload["sender_name"]

    # Verify persistence via GET
    g = session.get(f"{API}/settings")
    assert g.status_code == 200
    data = g.json()
    assert data["business_name"] == payload["business_name"]
    assert data["sender_pincode"] == "560001"
    assert data["pickup_location"] == "TestWarehouse"


# --- Bulk shipment template download ---
def test_bulk_template_download(session):
    r = session.get(f"{API}/shipments/bulk/template")
    assert r.status_code == 200, r.text[:300]
    assert "text/csv" in r.headers.get("content-type", "")
    text = r.text
    assert "order_id" in text
    assert "receiver_name" in text


# --- Bulk download CSV ---
def test_bulk_download_shipments(session):
    r = session.get(f"{API}/shipments/bulk/download")
    assert r.status_code == 200, r.text[:300]
    assert "text/csv" in r.headers.get("content-type", "")
    # Header row present
    assert "Order ID" in r.text
    assert "Waybill" in r.text


# --- Bulk upload (requires settings) ---
def test_bulk_upload_csv(session):
    csv_content = (
        "order_id,receiver_name,receiver_phone,receiver_email,receiver_address,receiver_city,"
        "receiver_state,receiver_pincode,item_name,item_qty,item_price,payment_mode,"
        "cod_amount,weight,length,breadth,height\n"
        "TEST_ITER2_BULK_001,John Doe,9876543210,john@example.com,123 Main Street,Mumbai,"
        "Maharashtra,400001,Sample Product,1,999.00,Prepaid,0,0.5,10,10,10\n"
    )
    files = {"file": ("bulk.csv", csv_content, "text/csv")}
    r = session.post(f"{API}/shipments/bulk/upload", files=files)
    # 200 with results (success or failures from Delhivery), or 400 if settings missing
    assert r.status_code in (200, 400), r.text[:300]
    if r.status_code == 200:
        data = r.json()
        assert "total" in data and "success" in data and "failed" in data
        assert data["total"] == 1
        assert isinstance(data.get("shipments"), list)
        assert isinstance(data.get("errors"), list)


def test_bulk_upload_non_csv(session):
    files = {"file": ("bulk.txt", "not a csv", "text/plain")}
    r = session.post(f"{API}/shipments/bulk/upload", files=files)
    assert r.status_code == 400


# --- Pickup scheduling - default pickup_time ---
def test_schedule_pickup_default_time(session):
    payload = {
        "pickup_location": "TestWarehouse",
        "pickup_date": "2026-02-15",
        "expected_package_count": 3
    }
    r = session.post(f"{API}/pickups", json=payload)
    # Live Delhivery may reject due to warehouse not registered -> 500
    assert r.status_code in (200, 400, 500), f"Unexpected: {r.status_code} {r.text[:300]}"
    if r.status_code == 200:
        data = r.json()
        assert data["pickup_time"] == "10:00:00"


# --- Warehouse Registration ---
def test_warehouse_register(session):
    payload = {
        "name": "TEST_ITER2_Warehouse",
        "email": "wh@test.com",
        "phone": "9999900000",
        "address": "1 Test Lane",
        "city": "Bangalore",
        "state": "Karnataka",
        "country": "India",
        "pin": "560001"
    }
    r = session.post(f"{API}/warehouse/register", json=payload)
    # API contract: 200 success or 400/500 if Delhivery rejects (warehouse exists, etc.)
    assert r.status_code in (200, 400, 500), r.text[:300]


# --- Create shipment validation ---
def test_create_shipment_invalid_payload(session):
    r = session.post(f"{API}/shipments", json={"order_id": "x"}, headers={"Content-Type": "application/json"})
    assert r.status_code == 422


# --- Bulk labels endpoint - validation ---
def test_bulk_labels_empty_waybills(session):
    r = session.get(f"{API}/shipments/bulk/labels", params={"waybills": ""})
    # Either 422 (validation) or 400 (no waybills)
    assert r.status_code in (400, 422)
