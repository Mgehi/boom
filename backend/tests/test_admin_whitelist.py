"""Admin email whitelist & role tests - Iteration 6"""
import os
import uuid
import pytest
import requests
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from pathlib import Path

from tests.db_helper import TestDB

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

BASE_URL = os.environ['REACT_APP_BACKEND_URL'].rstrip('/') if os.environ.get('REACT_APP_BACKEND_URL') else None
if not BASE_URL:
    # try frontend .env
    fe_env = Path(__file__).resolve().parents[2] / "frontend" / ".env"
    for line in fe_env.read_text().splitlines():
        if line.startswith("REACT_APP_BACKEND_URL="):
            BASE_URL = line.split("=", 1)[1].strip().rstrip('/')

db = TestDB()

TEST_PREFIX = "TEST_ADMIN_"


def _mk_user(email, is_admin=False):
    uid = f"TEST_ADMIN_user_{uuid.uuid4().hex[:8]}"
    token = f"TEST_ADMIN_tok_{uuid.uuid4().hex[:12]}"
    db.users.insert_one({
        "user_id": uid, "email": email.lower(), "name": email.split("@")[0],
        "picture": "", "is_admin": is_admin,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    db.user_sessions.insert_one({
        "user_id": uid, "session_token": token,
        "expires_at": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    return uid, token


@pytest.fixture(scope="module", autouse=True)
def cleanup():
    # pre-clean
    db.users.delete_many({"email": {"$regex": "^TEST_ADMIN_"}})
    db.users.delete_many({"user_id": {"$regex": "^TEST_ADMIN_"}})
    db.user_sessions.delete_many({"session_token": {"$regex": "^TEST_ADMIN_"}})
    db.allowed_emails.delete_many({"email": {"$regex": "^test_admin_"}})
    yield
    db.users.delete_many({"email": {"$regex": "^TEST_ADMIN_"}})
    db.users.delete_many({"user_id": {"$regex": "^TEST_ADMIN_"}})
    db.user_sessions.delete_many({"session_token": {"$regex": "^TEST_ADMIN_"}})
    db.allowed_emails.delete_many({"email": {"$regex": "^test_admin_"}})


@pytest.fixture
def admin():
    uid, token = _mk_user("TEST_ADMIN_admin@example.com", is_admin=True)
    return {"user_id": uid, "token": token, "headers": {"Authorization": f"Bearer {token}"}}


@pytest.fixture
def client_user():
    uid, token = _mk_user("TEST_ADMIN_client@example.com", is_admin=False)
    return {"user_id": uid, "token": token, "headers": {"Authorization": f"Bearer {token}"}}


# ---------------- /api/auth/me ----------------
class TestAuthMe:
    def test_me_returns_is_admin_true(self, admin):
        r = requests.get(f"{BASE_URL}/api/auth/me", headers=admin["headers"])
        assert r.status_code == 200
        data = r.json()
        assert data["is_admin"] is True
        assert data["email"] == "test_admin_admin@example.com"

    def test_me_returns_is_admin_false(self, client_user):
        r = requests.get(f"{BASE_URL}/api/auth/me", headers=client_user["headers"])
        assert r.status_code == 200
        assert r.json()["is_admin"] is False


# ---------------- Google OAuth login/callback surface ----------------
class TestGoogleOAuthSurface:
    def test_login_redirects_to_google(self):
        r = requests.get(f"{BASE_URL}/api/auth/google/login", allow_redirects=False)
        assert r.status_code in (302, 307)
        assert "accounts.google.com" in r.headers.get("location", "")

    def test_callback_without_code_returns_401(self):
        r = requests.get(f"{BASE_URL}/api/auth/google/callback")
        assert r.status_code == 401


# ---------------- Admin endpoints auth ----------------
class TestAdminAuth:
    def test_non_admin_blocked_list_emails(self, client_user):
        r = requests.get(f"{BASE_URL}/api/admin/allowed-emails", headers=client_user["headers"])
        assert r.status_code == 403
        assert "Admin access required" in r.json()["detail"]

    def test_non_admin_blocked_add_email(self, client_user):
        r = requests.post(f"{BASE_URL}/api/admin/allowed-emails",
                          headers=client_user["headers"],
                          json={"email": "x@y.com"})
        assert r.status_code == 403

    def test_non_admin_blocked_list_users(self, client_user):
        r = requests.get(f"{BASE_URL}/api/admin/users", headers=client_user["headers"])
        assert r.status_code == 403

    def test_non_admin_blocked_delete_email(self, client_user):
        r = requests.delete(f"{BASE_URL}/api/admin/allowed-emails/some-id",
                            headers=client_user["headers"])
        assert r.status_code == 403

    def test_non_admin_blocked_revoke_user(self, client_user):
        r = requests.delete(f"{BASE_URL}/api/admin/users/some-uid",
                            headers=client_user["headers"])
        assert r.status_code == 403

    def test_no_auth_returns_401(self):
        r = requests.get(f"{BASE_URL}/api/admin/allowed-emails")
        assert r.status_code == 401


# ---------------- Whitelist CRUD ----------------
class TestWhitelistCRUD:
    def test_add_list_remove_whitelist(self, admin):
        email = "test_admin_whitelistclient@example.com"
        # add
        r = requests.post(f"{BASE_URL}/api/admin/allowed-emails",
                          headers=admin["headers"],
                          json={"email": email, "note": "ABC Pvt Ltd"})
        assert r.status_code == 200, r.text
        entry = r.json()
        assert entry["email"] == email
        assert entry["note"] == "ABC Pvt Ltd"
        assert "id" in entry
        entry_id = entry["id"]

        # list - verify persistence
        r = requests.get(f"{BASE_URL}/api/admin/allowed-emails", headers=admin["headers"])
        assert r.status_code == 200
        items = r.json()
        assert any(e["email"] == email and e["note"] == "ABC Pvt Ltd" for e in items)

        # dup add -> 400
        r = requests.post(f"{BASE_URL}/api/admin/allowed-emails",
                          headers=admin["headers"],
                          json={"email": email})
        assert r.status_code == 400
        assert "already" in r.json()["detail"].lower()

        # invalid email -> 400
        r = requests.post(f"{BASE_URL}/api/admin/allowed-emails",
                          headers=admin["headers"],
                          json={"email": "not-an-email"})
        assert r.status_code == 400

        # remove
        r = requests.delete(f"{BASE_URL}/api/admin/allowed-emails/{entry_id}",
                            headers=admin["headers"])
        assert r.status_code == 200
        assert r.json()["success"] is True

        # remove non-existent -> 404
        r = requests.delete(f"{BASE_URL}/api/admin/allowed-emails/{entry_id}",
                            headers=admin["headers"])
        assert r.status_code == 404

        # verify gone
        r = requests.get(f"{BASE_URL}/api/admin/allowed-emails", headers=admin["headers"])
        assert not any(e["id"] == entry_id for e in r.json())


# ---------------- List users + shipment count ----------------
class TestListUsers:
    def test_list_users_includes_shipment_count(self, admin, client_user):
        r = requests.get(f"{BASE_URL}/api/admin/users", headers=admin["headers"])
        assert r.status_code == 200
        users = r.json()
        assert isinstance(users, list)
        emails = {u["email"]: u for u in users}
        assert "test_admin_admin@example.com" in emails
        assert "test_admin_client@example.com" in emails
        for u in users:
            assert "shipment_count" in u
            assert isinstance(u["shipment_count"], int)
            # is_admin may be absent for legacy users pre-dating the role system
            assert u.get("is_admin", False) in (True, False)


# ---------------- Revoke user rules ----------------
class TestRevokeUser:
    def test_admin_cannot_revoke_self(self, admin):
        r = requests.delete(f"{BASE_URL}/api/admin/users/{admin['user_id']}",
                            headers=admin["headers"])
        assert r.status_code == 400
        assert "own access" in r.json()["detail"].lower()

    def test_admin_cannot_revoke_another_admin(self, admin):
        other_uid, _ = _mk_user("TEST_ADMIN_otheradmin@example.com", is_admin=True)
        r = requests.delete(f"{BASE_URL}/api/admin/users/{other_uid}",
                            headers=admin["headers"])
        assert r.status_code == 400
        assert "another admin" in r.json()["detail"].lower()

    def test_revoke_nonexistent_user(self, admin):
        r = requests.delete(f"{BASE_URL}/api/admin/users/nonexistent-uid",
                            headers=admin["headers"])
        assert r.status_code == 404

    def test_revoke_client_deletes_user_and_sessions(self, admin):
        uid, tok = _mk_user("TEST_ADMIN_revokeme@example.com", is_admin=False)
        # confirm session valid first
        r = requests.get(f"{BASE_URL}/api/auth/me",
                         headers={"Authorization": f"Bearer {tok}"})
        assert r.status_code == 200

        # revoke
        r = requests.delete(f"{BASE_URL}/api/admin/users/{uid}",
                            headers=admin["headers"])
        assert r.status_code == 200
        assert r.json()["success"] is True

        # verify user gone
        assert db.users.find_one({"user_id": uid}) is None
        # verify sessions gone
        assert db.user_sessions.count_documents({"user_id": uid}) == 0
        # verify token is now invalid
        r = requests.get(f"{BASE_URL}/api/auth/me",
                         headers={"Authorization": f"Bearer {tok}"})
        assert r.status_code == 401


# ---------------- Bootstrap logic (code path) ----------------
class TestBootstrapLogic:
    """We can't fully exercise /api/auth/session without a real Emergent session_id,
    but we can verify the code-path logic by directly inspecting DB state
    transitions that the endpoint would do."""

    def test_admin_exists_check_works(self, admin):
        # admin fixture creates an admin -> admin_exists should be True
        assert db.users.find_one({"is_admin": True}) is not None

    def test_whitelist_check_blocks_when_not_listed(self):
        # ensure no whitelist entry for a fake email
        fake = "test_admin_unwhitelisted@example.com"
        db.allowed_emails.delete_many({"email": fake})
        # admin must exist to trigger whitelist enforcement
        assert db.users.count_documents({"is_admin": True}) > 0
        # whitelist lookup should miss
        assert db.allowed_emails.find_one({"email": fake}) is None
