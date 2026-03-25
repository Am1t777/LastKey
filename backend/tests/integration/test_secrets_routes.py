import pytest


def _create_secret(client, auth_headers, title="My Secret", content="secret content"):
    return client.post("/api/secrets", json={
        "title": title,
        "content": content,
        "secret_type": "note",
        "password": "password123",
        "beneficiary_ids": [],
    }, headers=auth_headers)


def test_create_secret(client, auth_headers):
    resp = _create_secret(client, auth_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "My Secret"
    assert "owner_encrypted_key" in data


def test_list_secrets(client, auth_headers):
    _create_secret(client, auth_headers, "S1")
    _create_secret(client, auth_headers, "S2")
    resp = client.get("/api/secrets", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) >= 2


def test_get_secret(client, auth_headers):
    create_resp = _create_secret(client, auth_headers)
    sid = create_resp.json()["id"]
    resp = client.get(f"/api/secrets/{sid}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == sid


def test_delete_secret(client, auth_headers):
    create_resp = _create_secret(client, auth_headers)
    sid = create_resp.json()["id"]
    resp = client.delete(f"/api/secrets/{sid}", headers=auth_headers)
    assert resp.status_code == 200
    resp2 = client.get(f"/api/secrets/{sid}", headers=auth_headers)
    assert resp2.status_code == 404


def test_cross_user_secret_returns_404(client, auth_headers, auth_headers_b):
    create_resp = _create_secret(client, auth_headers)
    sid = create_resp.json()["id"]
    resp = client.get(f"/api/secrets/{sid}", headers=auth_headers_b)
    assert resp.status_code == 404


def test_update_secret(client, auth_headers):
    create_resp = _create_secret(client, auth_headers, "Original")
    sid = create_resp.json()["id"]
    resp = client.put(f"/api/secrets/{sid}", json={
        "title": "Updated",
        "content": "new content",
        "secret_type": "note",
        "password": "password123",
        "beneficiary_ids": [],
    }, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["title"] == "Updated"
