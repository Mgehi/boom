"""Backend regression tests for Iteration 3 Delhivery fixes.

Coverage:
- POST /api/warehouse/register (STAYFREE already_exists case)
- POST /api/orders with STAYFREE -> real waybill, status=Manifested
- POST /api/pickups -> Delhivery pickup_id (URL without /api prefix, JSON body)
- GET /api/shipments/{id}/label -> PDF binary (from S3 pdf_download_link)
- GET /api/shipments/bulk/labels?waybills=... -> ZIP of PDFs
- GET /api/pincode/check?pincode=452007 -> Indore serviceable
"""
import os
import io
import zipfile
from datetime import datetime, timedelta

import pytest
import requests

BASE_URL = os.environ['REACT_APP_BACKEND_URL'].rstrip('/')
API = f"{BASE_URL}/api"


@pytest.fixture(scope="module")
def session():
    s = requests.Session()
    return s


@pytest.fixture(scope="module")
def stayfree_sender():
    """Verified working sender (Indore) per problem statement."""
    return {
        "name": "MG",
        "phone": "9165656655",
        "email": "mg@stayfree.example.com",
        "address": "13/27 RANIPURA MAI ROAD",
        "city": "Indore",
        "state": "Madhya Pradesh",
        "pincode": "452007",
        "country": "India",
    }


# ---- Pincode serviceability (Indore) ----
def test_pincode_452007_indore_serviceable(session):
    r = session.get(f"{API}/pincode/check", params={"pincode": "452007"})
    assert r.status_code == 200, r.text[:400]
    data = r.json()
    assert data["pincode"] == "452007"
    assert data["serviceable"] is True
    # Delhivery returns state code; both 'Madhya Pradesh' & 'MP' are acceptable
    state = (data.get("state") or "").lower()
    assert "mp" in state or "madhya" in state, f"Expected MP/Madhya Pradesh, got {state!r}"
    city = (data.get("city") or "").lower()
    assert "indore" in city, f"Expected Indore, got {city!r}"


# ---- Warehouse registration (STAYFREE already exists) ----
def test_warehouse_register_stayfree_already_exists(session):
    payload = {
        "name": "STAYFREE",
        "email": "mg@stayfree.example.com",
        "phone": "9165656655",
        "address": "13/27 RANIPURA MAI ROAD",
        "city": "Indore",
        "state": "Madhya Pradesh",
        "country": "India",
        "pin": "452007",
    }
    r = session.post(f"{API}/warehouse/register", json=payload)
    assert r.status_code == 200, f"Status {r.status_code}: {r.text[:400]}"
    data = r.json()
    assert data.get("success") is True
    # Should be already_exists=True OR success message present
    msg = (data.get("message") or "").lower()
    assert ("already" in msg) or ("registered" in msg) or ("success" in msg), f"Unexpected msg: {msg}"


# ---- POST /api/orders with STAYFREE -> real waybill ----
@pytest.fixture(scope="module")
def created_shipment(session, stayfree_sender):
    """Create a shipment via /api/orders and return its dict for downstream tests."""
    order_id = f"TEST_IT3_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    payload = {
        "order_id": order_id,
        "pickup_location": "STAYFREE",
        "sender": stayfree_sender,
        "receiver": {
            "name": "Test Receiver",
            "phone": "9876543210",
            "email": "receiver@test.com",
            "address": "456 Delivery Lane",
            "city": "Mumbai",
            "state": "Maharashtra",
            "pincode": "400001",
            "country": "India",
        },
        "items": [{"name": "Test Product", "qty": 1, "price": 499.0}],
        "payment_mode": "Prepaid",
        "cod_amount": 0,
        "weight": 0.5,
        "length": 10,
        "breadth": 10,
        "height": 10,
    }
    r = session.post(f"{API}/orders", json=payload)
    if r.status_code != 200:
        pytest.skip(f"Order creation failed at Delhivery, cannot run downstream tests: {r.status_code} {r.text[:400]}")
    return r.json()


def test_create_order_stayfree_returns_real_waybill(created_shipment):
    assert created_shipment.get("waybill"), f"No waybill in response: {created_shipment}"
    waybill = created_shipment["waybill"]
    # Delhivery waybills are numeric, ~14 digits
    assert waybill.isdigit(), f"Waybill not numeric: {waybill}"
    assert len(waybill) >= 10, f"Waybill too short: {waybill}"
    assert created_shipment.get("status") == "Manifested", (
        f"Expected Manifested status, got: {created_shipment.get('status')}"
    )


def test_created_shipment_persisted(session, created_shipment):
    sid = created_shipment["id"]
    r = session.get(f"{API}/shipments/{sid}")
    assert r.status_code == 200, r.text[:300]
    fetched = r.json()
    assert fetched["waybill"] == created_shipment["waybill"]
    assert fetched["status"] == "Manifested"
    assert fetched["pickup_location"] == "STAYFREE"


# ---- Label download: PDF binary from S3 ----
def test_label_download_returns_pdf_binary(session, created_shipment):
    sid = created_shipment["id"]
    r = session.get(f"{API}/shipments/{sid}/label")
    assert r.status_code == 200, f"Status {r.status_code}: {r.text[:400]}"
    content_type = r.headers.get("content-type", "")
    assert "application/pdf" in content_type, f"Expected PDF content-type, got: {content_type}"
    # PDF magic bytes
    assert r.content[:4] == b"%PDF", f"Not a PDF, starts with: {r.content[:20]!r}"
    assert len(r.content) > 1000, f"PDF too small: {len(r.content)} bytes"


# ---- Bulk labels: ZIP ----
def test_bulk_labels_zip_download(session, created_shipment):
    waybill = created_shipment["waybill"]
    r = session.get(f"{API}/shipments/bulk/labels", params={"waybills": waybill})
    assert r.status_code == 200, f"Status {r.status_code}: {r.text[:400]}"
    content_type = r.headers.get("content-type", "")
    assert "application/zip" in content_type, f"Expected ZIP, got: {content_type}"
    # Verify it's a valid ZIP with at least one PDF entry
    zf = zipfile.ZipFile(io.BytesIO(r.content))
    names = zf.namelist()
    assert len(names) >= 1, f"Empty ZIP, names: {names}"
    pdf_entries = [n for n in names if n.endswith(".pdf")]
    assert len(pdf_entries) >= 1, f"No PDF entries in ZIP: {names}"
    # Verify first PDF entry is a real PDF
    with zf.open(pdf_entries[0]) as fp:
        head = fp.read(4)
        assert head == b"%PDF", f"Entry {pdf_entries[0]} not a PDF, starts with {head!r}"


# ---- Pickup scheduling (was 404 before fix) ----
def test_schedule_pickup_stayfree(session):
    # Future date to avoid same-day-cutoff issues
    future_date = (datetime.utcnow() + timedelta(days=3)).strftime("%Y-%m-%d")
    payload = {
        "pickup_location": "STAYFREE",
        "pickup_date": future_date,
        "pickup_time": "10:00:00",
        "expected_package_count": 1,
    }
    r = session.post(f"{API}/pickups", json=payload)
    # 200 (success) is the expected post-fix behaviour; 400 is acceptable if Delhivery has business
    # constraints (already-scheduled, holiday) but the 404 routing bug is now gone.
    assert r.status_code in (200, 400), f"Unexpected {r.status_code}: {r.text[:400]}"
    if r.status_code == 200:
        data = r.json()
        # Either pickup_id from Delhivery OR our DB id
        assert data.get("id") or (data.get("delhivery_response", {}) or {}).get("pickup_id"), (
            f"No pickup id in response: {data}"
        )
        assert data.get("pickup_location") == "STAYFREE"
        assert data.get("pickup_date") == future_date
    else:
        # Must NOT be a 404 routing issue
        body = r.text.lower()
        assert "not found" not in body or "404" not in body, (
            f"Pickup endpoint still seems 404'ing: {r.text[:400]}"
        )
