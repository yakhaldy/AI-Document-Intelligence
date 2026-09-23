"""API tests against the real dev DB (docker-compose) — no mocks for the DB,
consistent with the rest of this project's integration-style tests."""
import uuid

import pytest
from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)


@pytest.fixture
def token():
    resp = client.post("/auth/login", json={"username": "demo", "password": "demo1234"})
    assert resp.status_code == 200
    return resp.json()["access_token"]


@pytest.fixture
def pending_user():
    """Registers a fresh account (unique username) and returns its credentials.
    Real DB, so usernames must be unique across test runs."""
    username = f"test_{uuid.uuid4().hex[:10]}"
    password = "password123"
    resp = client.post("/auth/register", json={"username": username, "password": password})
    assert resp.status_code == 201
    return {"username": username, "password": password}


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_login_success_returns_token(token):
    assert len(token) > 20


def test_login_wrong_password_rejected():
    resp = client.post("/auth/login", json={"username": "demo", "password": "wrong"})
    assert resp.status_code == 401


def test_invoices_requires_auth():
    resp = client.get("/invoices")
    assert resp.status_code == 401


def test_invoices_list_with_auth(token):
    resp = client.get("/invoices?page=1&page_size=5", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] > 0
    assert len(data["items"]) <= 5


def test_invoices_list_filters_by_payment_status(token):
    resp = client.get(
        "/invoices?payment_status=unpaid&page_size=100",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert all(item["payment_status"] == "unpaid" for item in data["items"])


def test_invoice_detail_not_found_returns_404(token):
    resp = client.get("/invoices/999999999", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 404


def test_chat_requires_auth():
    resp = client.post("/chat", json={"question": "test"})
    assert resp.status_code == 401


@pytest.mark.requires_llm
def test_chat_answers_a_known_fact(token):
    resp = client.post(
        "/chat",
        json={"question": "Combien de factures sont impayées ?"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "40" in data["answer"]
    assert "count_by_payment_status" in data["tools_used"]


def test_upload_rejects_unsupported_format(token):
    resp = client.post(
        "/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("test.txt", b"hello", "text/plain")},
    )
    assert resp.status_code == 422


def test_register_rejects_duplicate_username(pending_user):
    resp = client.post("/auth/register", json=pending_user)
    assert resp.status_code == 409


def test_register_rejects_short_password():
    resp = client.post("/auth/register", json={"username": f"t_{uuid.uuid4().hex[:8]}", "password": "short"})
    assert resp.status_code == 422


def test_login_blocked_before_admin_approval(pending_user):
    resp = client.post("/auth/login", json=pending_user)
    assert resp.status_code == 401


def test_admin_sees_pending_user_in_list(token, pending_user):
    resp = client.get("/admin/users?status=pending", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    usernames = [u["username"] for u in resp.json()]
    assert pending_user["username"] in usernames


def test_admin_routes_require_admin_role(token, pending_user):
    # approve the pending user, then confirm THEY can't reach admin routes
    approve = client.get("/admin/users?status=pending", headers={"Authorization": f"Bearer {token}"})
    user_id = next(u["id"] for u in approve.json() if u["username"] == pending_user["username"])
    client.post(f"/admin/users/{user_id}/approve", headers={"Authorization": f"Bearer {token}"})

    login = client.post("/auth/login", json=pending_user)
    assert login.status_code == 200
    user_token = login.json()["access_token"]

    resp = client.get("/admin/users", headers={"Authorization": f"Bearer {user_token}"})
    assert resp.status_code == 403


def test_admin_approve_then_login_succeeds(pending_user, token):
    listing = client.get("/admin/users?status=pending", headers={"Authorization": f"Bearer {token}"})
    user_id = next(u["id"] for u in listing.json() if u["username"] == pending_user["username"])

    approve_resp = client.post(f"/admin/users/{user_id}/approve", headers={"Authorization": f"Bearer {token}"})
    assert approve_resp.status_code == 200
    assert approve_resp.json()["status"] == "approved"

    login_resp = client.post("/auth/login", json=pending_user)
    assert login_resp.status_code == 200


def test_admin_reject_keeps_login_blocked(pending_user, token):
    listing = client.get("/admin/users?status=pending", headers={"Authorization": f"Bearer {token}"})
    user_id = next(u["id"] for u in listing.json() if u["username"] == pending_user["username"])

    reject_resp = client.post(f"/admin/users/{user_id}/reject", headers={"Authorization": f"Bearer {token}"})
    assert reject_resp.status_code == 200
    assert reject_resp.json()["status"] == "rejected"

    login_resp = client.post("/auth/login", json=pending_user)
    assert login_resp.status_code == 401


def test_cannot_change_admin_status(token):
    me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    admin_id = me.json()["id"]
    resp = client.post(f"/admin/users/{admin_id}/reject", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 400


def test_documents_requires_auth():
    resp = client.get("/documents")
    assert resp.status_code == 401


def test_documents_list_with_auth(token):
    resp = client.get("/documents?page=1&page_size=5", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] > 0
    assert len(data["items"]) <= 5
    assert all(item["doc_type"] in ("invoice", "contract", "report") for item in data["items"])


def test_documents_filters_by_doc_type(token):
    resp = client.get("/documents?doc_type=invoice&page_size=100", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert all(item["doc_type"] == "invoice" for item in data["items"])
