"""Tests for items CRUD endpoints (MongoDB backend)."""
import pytest
from fastapi.testclient import TestClient

BACKEND = "mongo"
BASE = f"/api/v1/items/{BACKEND}"


@pytest.fixture
def item_payload():
    return {"name": "Test Widget", "description": "A test item",
            "price": 9.99, "quantity": 10}


@pytest.fixture
def created_item(client: TestClient, auth_headers, item_payload):
    resp = client.post(BASE, json=item_payload, headers=auth_headers)
    assert resp.status_code == 200
    return resp.json()["detail"]


class TestCreateItem:
    def test_create_success(self, client, auth_headers, item_payload):
        resp = client.post(BASE, json=item_payload, headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert "item_id" in body["detail"]

    def test_create_unauthenticated(self, client, item_payload):
        resp = client.post(BASE, json=item_payload)
        assert resp.status_code == 401

    def test_create_missing_fields(self, client, auth_headers):
        resp = client.post(BASE, json={"name": "only name"}, headers=auth_headers)
        assert resp.status_code == 422


class TestGetItem:
    def test_get_existing(self, client, auth_headers, created_item):
        item_id = created_item["item_id"]
        resp = client.get(f"{BASE}/{item_id}", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["detail"]["item_id"] == item_id

    def test_get_nonexistent(self, client, auth_headers):
        resp = client.get(f"{BASE}/nonexistent-id", headers=auth_headers)
        assert resp.status_code == 404

    def test_get_unauthenticated(self, client, created_item):
        item_id = created_item["item_id"]
        resp = client.get(f"{BASE}/{item_id}")
        assert resp.status_code == 401


class TestListItems:
    def test_list_empty(self, client, auth_headers):
        resp = client.get(BASE, headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json()["detail"], list)

    def test_list_after_create(self, client, auth_headers, item_payload):
        client.post(BASE, json=item_payload, headers=auth_headers)
        resp = client.get(BASE, headers=auth_headers)
        assert resp.status_code == 200
        assert len(resp.json()["detail"]) >= 1


class TestUpdateItem:
    def test_update_success(self, client, auth_headers, created_item):
        item_id = created_item["item_id"]
        resp = client.put(f"{BASE}/{item_id}",
                          json={"price": 19.99},
                          headers=auth_headers)
        assert resp.status_code == 200

    def test_update_nonexistent(self, client, auth_headers):
        resp = client.put(f"{BASE}/ghost-id",
                          json={"price": 5.0},
                          headers=auth_headers)
        assert resp.status_code == 404


class TestDeleteItem:
    def test_delete_success(self, client, auth_headers, created_item):
        item_id = created_item["item_id"]
        resp = client.delete(f"{BASE}/{item_id}", headers=auth_headers)
        assert resp.status_code == 200
        # Verify gone
        get_resp = client.get(f"{BASE}/{item_id}", headers=auth_headers)
        assert get_resp.status_code == 404

    def test_delete_nonexistent(self, client, auth_headers):
        resp = client.delete(f"{BASE}/ghost-id", headers=auth_headers)
        assert resp.status_code == 404
