import pytest


def test_register(client):
    resp = client.post("/api/auth/register", json={
        "email": "new@test.com", "password": "password123", "name": "New User"
    }, headers={"X-Requested-With": "XMLHttpRequest"})
    assert resp.status_code == 201
    data = resp.json()
    assert "access_token" in data


def test_register_duplicate_email(client, test_user):
    resp = client.post("/api/auth/register", json={
        "email": test_user.email, "password": "password123", "name": "Dup"
    }, headers={"X-Requested-With": "XMLHttpRequest"})
    assert resp.status_code == 400


def test_login(client, test_user):
    resp = client.post("/api/auth/login", json={
        "email": test_user.email, "password": "password123"
    }, headers={"X-Requested-With": "XMLHttpRequest"})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_login_wrong_password(client, test_user):
    resp = client.post("/api/auth/login", json={
        "email": test_user.email, "password": "wrongpass"
    }, headers={"X-Requested-With": "XMLHttpRequest"})
    assert resp.status_code == 401


def test_me(client, auth_headers):
    resp = client.get("/api/auth/me", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "email" in data
    assert "switch_status" in data


def test_me_no_auth(client):
    resp = client.get("/api/auth/me")
    assert resp.status_code == 401


def test_logout(client, auth_headers):
    resp = client.post("/api/auth/logout", headers=auth_headers)
    assert resp.status_code == 200
