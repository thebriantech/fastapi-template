"""Tests for user management endpoints."""
import pytest

BACKEND = "mongo"
BASE = f"/api/v1/users/{BACKEND}"


@pytest.fixture
def user_data():
    return {"username": "newuser", "user_group": "users",
            "email": "new@example.com", "password": "Pass123!"}


class TestRegisterUser:
    def test_register_success(self, client, user_data):
        resp = client.post(f"{BASE}/register", json=user_data)
        assert resp.status_code == 200

    def test_register_duplicate(self, client, user_data):
        client.post(f"{BASE}/register", json=user_data)
        resp = client.post(f"{BASE}/register", json=user_data)
        assert resp.status_code in (400, 409)

    def test_register_missing_fields(self, client):
        resp = client.post(f"{BASE}/register", json={"username": "only"})
        assert resp.status_code == 422


class TestDeleteUser:
    def test_delete_requires_superuser(self, client, auth_headers, registered_user):
        resp = client.delete(
            f"{BASE}/delete/{registered_user['username']}",
            headers=auth_headers
        )
        assert resp.status_code == 403

    def test_delete_as_superuser(self, client, admin_headers, registered_user):
        resp = client.delete(
            f"{BASE}/delete/{registered_user['username']}",
            headers=admin_headers
        )
        assert resp.status_code == 200

    def test_delete_unauthenticated(self, client, registered_user):
        resp = client.delete(f"{BASE}/delete/{registered_user['username']}")
        assert resp.status_code in (401, 403)
