"""Tests for tasks CRUD endpoints."""
import pytest

BACKEND = "mongo"
BASE = f"/api/v1/tasks/{BACKEND}"


@pytest.fixture
def task_payload():
    return {"title": "Test Task", "description": "Do something",
            "status": "todo", "assignee": "alice"}


@pytest.fixture
def created_task(client, auth_headers, task_payload):
    resp = client.post(BASE, json=task_payload, headers=auth_headers)
    assert resp.status_code == 200
    return resp.json()["detail"]


class TestCreateTask:
    def test_create_success(self, client, auth_headers, task_payload):
        resp = client.post(BASE, json=task_payload, headers=auth_headers)
        assert resp.status_code == 200
        assert "task_id" in resp.json()["detail"]

    def test_create_unauthenticated(self, client, task_payload):
        resp = client.post(BASE, json=task_payload)
        assert resp.status_code == 401

    def test_create_missing_title(self, client, auth_headers):
        resp = client.post(BASE, json={"description": "no title"},
                           headers=auth_headers)
        assert resp.status_code == 422


class TestGetTask:
    def test_get_existing(self, client, auth_headers, created_task):
        task_id = created_task["task_id"]
        resp = client.get(f"{BASE}/{task_id}", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["detail"]["task_id"] == task_id

    def test_get_nonexistent(self, client, auth_headers):
        resp = client.get(f"{BASE}/no-such-task", headers=auth_headers)
        assert resp.status_code == 404


class TestUpdateTask:
    def test_update_status(self, client, auth_headers, created_task):
        task_id = created_task["task_id"]
        resp = client.put(f"{BASE}/{task_id}",
                          json={"status": "done"},
                          headers=auth_headers)
        assert resp.status_code == 200

    def test_update_nonexistent(self, client, auth_headers):
        resp = client.put(f"{BASE}/ghost", json={"status": "done"},
                          headers=auth_headers)
        assert resp.status_code == 404


class TestDeleteTask:
    def test_delete_success(self, client, auth_headers, created_task):
        task_id = created_task["task_id"]
        resp = client.delete(f"{BASE}/{task_id}", headers=auth_headers)
        assert resp.status_code == 200

    def test_delete_nonexistent(self, client, auth_headers):
        resp = client.delete(f"{BASE}/ghost", headers=auth_headers)
        assert resp.status_code == 404


class TestAssigneeFilter:
    def test_filter_by_assignee(self, client, auth_headers, task_payload):
        client.post(BASE, json=task_payload, headers=auth_headers)
        client.post(BASE, json={**task_payload, "assignee": "bob"},
                    headers=auth_headers)
        resp = client.get(f"{BASE}/assignee/alice", headers=auth_headers)
        assert resp.status_code == 200
        tasks = resp.json()["detail"]
        assert all(t.get("assignee") == "alice" for t in tasks)
