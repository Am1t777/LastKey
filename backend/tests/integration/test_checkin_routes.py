import pytest
from datetime import datetime, timedelta


def test_checkin_authenticated(client, auth_headers):
    resp = client.post("/api/checkin/auth", headers=auth_headers)
    assert resp.status_code == 200
    assert "next_checkin_due" in resp.json()


def test_checkin_by_token(client, db_session, test_user):
    import secrets
    token = secrets.token_urlsafe(32)
    test_user.checkin_token = token
    test_user.checkin_token_expires_at = datetime.utcnow() + timedelta(hours=24)
    db_session.commit()
    # Public checkin endpoint - no X-Requested-With needed (CSRF exempt)
    resp = client.post("/api/checkin", json={"token": token})
    assert resp.status_code == 200


def test_checkin_invalid_token(client):
    resp = client.post("/api/checkin", json={"token": "invalid-token-xyz"})
    assert resp.status_code == 400


def test_checkin_expired_token(client, db_session, test_user):
    import secrets
    token = secrets.token_urlsafe(32)
    test_user.checkin_token = token
    test_user.checkin_token_expires_at = datetime.utcnow() - timedelta(hours=1)
    db_session.commit()
    resp = client.post("/api/checkin", json={"token": token})
    assert resp.status_code == 400
