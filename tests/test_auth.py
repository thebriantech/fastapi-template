"""Tests for the authentication endpoints."""
import pytest
from fastapi.testclient import TestClient


class TestLogin:
    def test_login_success(self, client: TestClient, registered_user, plain_password):
        resp = client.post("/api/v1/auth/login", json={
            "username": registered_user["username"],
            "password": plain_password,
        })
        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body["detail"]

    def test_login_wrong_password(self, client: TestClient, registered_user):
        resp = client.post("/api/v1/auth/login", json={
            "username": registered_user["username"],
            "password": "WrongPassword!",
        })
        assert resp.status_code == 401

    def test_login_nonexistent_user(self, client: TestClient):
        resp = client.post("/api/v1/auth/login", json={
            "username": "nobody",
            "password": "pass",
        })
        assert resp.status_code in (400, 404)

    def test_login_missing_fields(self, client: TestClient):
        resp = client.post("/api/v1/auth/login", json={"username": "only"})
        assert resp.status_code == 422


class TestCheckLogin:
    def test_check_login_success(self, client: TestClient, auth_headers):
        resp = client.get("/api/v1/auth/check-login", headers=auth_headers)
        assert resp.status_code == 200

    def test_check_login_no_token(self, client: TestClient):
        resp = client.get("/api/v1/auth/check-login")
        assert resp.status_code == 401

    def test_check_login_invalid_token(self, client: TestClient):
        resp = client.get("/api/v1/auth/check-login",
                          headers={"Authorization": "Bearer invalid.token.here"})
        assert resp.status_code == 401

    def test_check_login_bad_format(self, client: TestClient, user_token):
        resp = client.get("/api/v1/auth/check-login",
                          headers={"Authorization": user_token})  # missing "Bearer "
        assert resp.status_code == 401
