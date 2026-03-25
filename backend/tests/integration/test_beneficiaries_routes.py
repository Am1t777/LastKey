import pytest


def _create_beneficiary(client, auth_headers, name="Alice", email="alice@ex.com"):
    return client.post("/api/beneficiaries", json={
        "name": name, "email": email
    }, headers=auth_headers)


def test_create_beneficiary(client, auth_headers):
    resp = _create_beneficiary(client, auth_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Alice"


def test_list_beneficiaries(client, auth_headers):
    _create_beneficiary(client, auth_headers, "Alice", "alice@ex.com")
    _create_beneficiary(client, auth_headers, "Bob", "bob@ex.com")
    resp = client.get("/api/beneficiaries", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) >= 2


def test_generate_key(client, auth_headers):
    resp = _create_beneficiary(client, auth_headers, "KeyUser", "key@ex.com")
    bid = resp.json()["id"]
    resp2 = client.post(f"/api/beneficiaries/{bid}/generate-key", headers=auth_headers)
    assert resp2.status_code == 200
    assert "private_key_pem" in resp2.json()


def test_generate_key_second_call_returns_400(client, auth_headers):
    resp = _create_beneficiary(client, auth_headers, "KeyUser2", "key2@ex.com")
    bid = resp.json()["id"]
    client.post(f"/api/beneficiaries/{bid}/generate-key", headers=auth_headers)
    resp2 = client.post(f"/api/beneficiaries/{bid}/generate-key", headers=auth_headers)
    assert resp2.status_code == 400


def test_delete_beneficiary(client, auth_headers):
    resp = _create_beneficiary(client, auth_headers, "ToDelete", "del@ex.com")
    bid = resp.json()["id"]
    del_resp = client.delete(f"/api/beneficiaries/{bid}", headers=auth_headers)
    assert del_resp.status_code == 200
    list_resp = client.get("/api/beneficiaries", headers=auth_headers)
    ids = [b["id"] for b in list_resp.json()]
    assert bid not in ids


def test_cross_user_beneficiary_returns_404(client, auth_headers, auth_headers_b):
    resp = _create_beneficiary(client, auth_headers, "Alice", "alice2@ex.com")
    bid = resp.json()["id"]
    resp2 = client.get(f"/api/beneficiaries/{bid}", headers=auth_headers_b)
    assert resp2.status_code == 404
