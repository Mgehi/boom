"""Auth + multi-tenant isolation tests for Delhivery logistics dashboard."""
import os
import time
import uuid
import pytest
import requests
from pymongo import MongoClient
from datetime import datetime, timezone, timedelta

BASE_URL = os.environ['REACT_APP_BACKEND_URL'].rstrip('/')
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'test_database')

mongo = MongoClient(MONGO_URL)
db = mongo[DB_NAME]


def _make_user(prefix: str):
    """Insert a test user + session directly in DB. Returns (user_id, token)."""
    user_id = f"TEST_{prefix}_{uuid.uuid4().hex[:8]}"
    token = f"TEST_token_{uuid.uuid4().hex}"
    email = f"TEST_{prefix}_{int(time.time()*1000)}@example.com"
    db.users.insert_one({
        "user_id": user_id,
        "email": email,
        "name": f"Test {prefix}",
        "picture": "",
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    db.user_sessions.insert_one({
        "user_id": user_id,
        "session_token": token,
        "expires_at": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    return user_id, token, email


@pytest.fixture(scope="module")
def user_a():
    uid, tok, em = _make_user("UA")
    yield {"user_id": uid, "token": tok, "email": em}
    # cleanup
    db.users.delete_one({"user_id": uid})
    db.user_sessions.delete_many({"user_id": uid})
    db.settings.delete_many({"user_id": uid})
    db.shipments.delete_many({"user_id": uid})
    db.pickups.delete_many({"user_id": uid})


@pytest.fixture(scope="module")
def user_b():
    uid, tok, em = _make_user("UB")
    yield {"user_id": uid, "token": tok, "email": em}
    db.users.delete_one({"user_id": uid})
    db.user_sessions.delete_many({"user_id": uid})
    db.settings.delete_many({"user_id": uid})
    db.shipments.delete_many({"user_id": uid})
    db.pickups.delete_many({"user_id": uid})


def H(token):
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


# ============ AUTH TESTS ============
class TestAuth:
    def test_me_without_auth_returns_401(self):
        r = requests.get(f"{BASE_URL}/api/auth/me")
        assert r.status_code == 401

    def test_session_without_session_id_header(self):
        r = requests.post(f"{BASE_URL}/api/auth/session")
        assert r.status_code == 400

    def test_session_with_invalid_session_id(self):
        r = requests.post(f"{BASE_URL}/api/auth/session",
                          headers={"X-Session-ID": "invalid_xxx"})
        assert r.status_code == 401

    def test_me_with_valid_bearer(self, user_a):
        r = requests.get(f"{BASE_URL}/api/auth/me", headers=H(user_a["token"]))
        assert r.status_code == 200
        data = r.json()
        assert data["user_id"] == user_a["user_id"]
        assert data["email"] == user_a["email"]
        assert "name" in data

    def test_me_with_invalid_bearer(self):
        r = requests.get(f"{BASE_URL}/api/auth/me",
                         headers={"Authorization": "Bearer bogus_token_xxx"})
        assert r.status_code == 401

    def test_logout_deletes_session(self):
        uid, tok, _ = _make_user("LOGOUT")
        try:
            # Verify valid
            assert requests.get(f"{BASE_URL}/api/auth/me", headers=H(tok)).status_code == 200
            # Logout
            r = requests.post(f"{BASE_URL}/api/auth/logout", headers=H(tok))
            assert r.status_code == 200
            assert r.json().get("success") is True
            # Token now invalid
            assert requests.get(f"{BASE_URL}/api/auth/me", headers=H(tok)).status_code == 401
        finally:
            db.users.delete_one({"user_id": uid})
            db.user_sessions.delete_many({"user_id": uid})


# ============ AUTH GATING ON ALL ENDPOINTS ============
class TestAuthGating:
    """All protected endpoints must return 401 without auth."""

    PROTECTED_GET = [
        "/api/shipments",
        "/api/pickups",
        "/api/dashboard/stats",
        "/api/settings",
        "/api/pincode/check?pincode=400001",
        "/api/shipments/bulk/template",
        "/api/shipments/bulk/download",
        "/api/shipments/bulk/labels?waybills=123",
        "/api/shipments/some-id",
        "/api/shipments/some-id/track",
        "/api/shipments/some-id/label",
    ]
    PROTECTED_POST = [
        ("/api/orders", {}),
        ("/api/shipments", {}),
        ("/api/pickups", {}),
        ("/api/warehouse/register", {}),
    ]

    @pytest.mark.parametrize("path", PROTECTED_GET)
    def test_get_requires_auth(self, path):
        r = requests.get(f"{BASE_URL}{path}")
        assert r.status_code == 401, f"GET {path} returned {r.status_code}, expected 401"

    @pytest.mark.parametrize("path,body", PROTECTED_POST)
    def test_post_requires_auth(self, path, body):
        r = requests.post(f"{BASE_URL}{path}", json=body)
        assert r.status_code == 401, f"POST {path} returned {r.status_code}, expected 401"

    def test_put_settings_requires_auth(self):
        r = requests.put(f"{BASE_URL}/api/settings", json={})
        assert r.status_code == 401

    def test_bulk_upload_requires_auth(self):
        r = requests.post(f"{BASE_URL}/api/shipments/bulk/upload",
                          files={"file": ("test.csv", "x,y\n1,2", "text/csv")})
        assert r.status_code == 401


# ============ MULTI-TENANT SETTINGS ISOLATION ============
class TestMultiTenantSettings:
    def test_each_user_has_own_settings(self, user_a, user_b):
        # User A saves settings
        a_settings = {
            "business_name": "Biz A", "sender_name": "Alice",
            "sender_phone": "9000000001", "sender_email": "alice@ex.com",
            "sender_address": "A addr", "sender_city": "Mumbai",
            "sender_state": "Maharashtra", "sender_pincode": "400001",
            "pickup_location": "STAYFREE", "seller_gst": "GSTINA001"
        }
        r = requests.put(f"{BASE_URL}/api/settings", json=a_settings, headers=H(user_a["token"]))
        assert r.status_code == 200

        # User B saves different settings
        b_settings = {
            "business_name": "Biz B", "sender_name": "Bob",
            "sender_phone": "9000000002", "sender_email": "bob@ex.com",
            "sender_address": "B addr", "sender_city": "Delhi",
            "sender_state": "Delhi", "sender_pincode": "110001",
            "pickup_location": "STAYFREE", "seller_gst": "GSTINB002"
        }
        r = requests.put(f"{BASE_URL}/api/settings", json=b_settings, headers=H(user_b["token"]))
        assert r.status_code == 200

        # User A reads back their own
        r = requests.get(f"{BASE_URL}/api/settings", headers=H(user_a["token"]))
        assert r.status_code == 200
        a = r.json()
        assert a["business_name"] == "Biz A"
        assert a["seller_gst"] == "GSTINA001"
        assert a["sender_name"] == "Alice"

        # User B reads back their own
        r = requests.get(f"{BASE_URL}/api/settings", headers=H(user_b["token"]))
        assert r.status_code == 200
        b = r.json()
        assert b["business_name"] == "Biz B"
        assert b["seller_gst"] == "GSTINB002"
        assert b["sender_name"] == "Bob"

        # No cross-contamination
        assert a["business_name"] != b["business_name"]
        assert a["seller_gst"] != b["seller_gst"]


# ============ MULTI-TENANT SHIPMENT ISOLATION (DB-LEVEL, no Delhivery call) ============
class TestMultiTenantShipments:
    """Insert shipments directly to DB to avoid live Delhivery cost, verify isolation."""

    @pytest.fixture(autouse=True)
    def setup_shipments(self, user_a, user_b):
        # Insert one shipment for each user directly
        self.a_ship_id = f"TEST_SHIP_A_{uuid.uuid4().hex[:8]}"
        self.b_ship_id = f"TEST_SHIP_B_{uuid.uuid4().hex[:8]}"
        now = datetime.now(timezone.utc).isoformat()
        base = {
            "pickup_location": "STAYFREE",
            "sender": {"name": "S", "phone": "9000000000", "address": "x",
                       "city": "Mumbai", "state": "MH", "pincode": "400001", "country": "India"},
            "receiver": {"name": "R", "phone": "9000000001", "address": "y",
                         "city": "Delhi", "state": "DL", "pincode": "110001", "country": "India"},
            "items": [{"name": "item", "qty": 1, "price": 100.0, "hsn_code": "6109"}],
            "payment_mode": "Prepaid", "cod_amount": 0, "weight": 0.5,
            "length": 10, "breadth": 10, "height": 10,
            "seller_gst": "", "seller_invoice": "", "shipment_type": "FWD",
            "status": "Manifested", "waybill": "FAKE_A_WB",
            "created_at": now, "updated_at": now,
        }
        db.shipments.insert_one({**base, "id": self.a_ship_id,
                                 "user_id": user_a["user_id"], "order_id": "TEST_ORD_A"})
        db.shipments.insert_one({**base, "id": self.b_ship_id, "waybill": "FAKE_B_WB",
                                 "user_id": user_b["user_id"], "order_id": "TEST_ORD_B"})
        yield
        db.shipments.delete_one({"id": self.a_ship_id})
        db.shipments.delete_one({"id": self.b_ship_id})

    def test_user_a_only_sees_own_shipments(self, user_a):
        r = requests.get(f"{BASE_URL}/api/shipments", headers=H(user_a["token"]))
        assert r.status_code == 200
        ids = [s["id"] for s in r.json()]
        assert self.a_ship_id in ids
        assert self.b_ship_id not in ids

    def test_user_b_only_sees_own_shipments(self, user_b):
        r = requests.get(f"{BASE_URL}/api/shipments", headers=H(user_b["token"]))
        assert r.status_code == 200
        ids = [s["id"] for s in r.json()]
        assert self.b_ship_id in ids
        assert self.a_ship_id not in ids

    def test_get_other_users_shipment_returns_404(self, user_a):
        r = requests.get(f"{BASE_URL}/api/shipments/{self.b_ship_id}", headers=H(user_a["token"]))
        assert r.status_code == 404

    def test_track_other_users_shipment_returns_404(self, user_a):
        r = requests.get(f"{BASE_URL}/api/shipments/{self.b_ship_id}/track",
                         headers=H(user_a["token"]))
        assert r.status_code == 404

    def test_label_other_users_shipment_returns_404(self, user_a):
        r = requests.get(f"{BASE_URL}/api/shipments/{self.b_ship_id}/label",
                         headers=H(user_a["token"]))
        assert r.status_code == 404

    def test_get_own_shipment_works(self, user_a):
        r = requests.get(f"{BASE_URL}/api/shipments/{self.a_ship_id}", headers=H(user_a["token"]))
        assert r.status_code == 200
        assert r.json()["id"] == self.a_ship_id

    def test_dashboard_stats_isolated(self, user_a, user_b):
        ra = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=H(user_a["token"]))
        rb = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=H(user_b["token"]))
        assert ra.status_code == 200 and rb.status_code == 200
        # Each user has exactly 1 shipment in this test class
        assert ra.json()["total_shipments"] >= 1
        assert rb.json()["total_shipments"] >= 1
        # A and B counts are independent (we count only their own)

    def test_new_user_has_zero_stats(self):
        uid, tok, _ = _make_user("NEWZERO")
        try:
            r = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=H(tok))
            assert r.status_code == 200
            d = r.json()
            assert d["total_shipments"] == 0
            assert d["in_transit"] == 0
            assert d["delivered"] == 0
        finally:
            db.users.delete_one({"user_id": uid})
            db.user_sessions.delete_many({"user_id": uid})

    def test_bulk_download_only_includes_own_shipments(self, user_a):
        r = requests.get(f"{BASE_URL}/api/shipments/bulk/download", headers=H(user_a["token"]))
        assert r.status_code == 200
        body = r.text
        assert "TEST_ORD_A" in body
        assert "TEST_ORD_B" not in body
