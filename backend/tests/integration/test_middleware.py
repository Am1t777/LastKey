import pytest


def test_security_headers_present(client, auth_headers):
    resp = client.get("/api/auth/me", headers=auth_headers)
    # Check headers case-insensitively
    headers_lower = {k.lower(): v for k, v in resp.headers.items()}
    assert "x-content-type-options" in headers_lower


def test_csrf_blocks_state_change_without_header(client, test_user):
    from app.services.auth_service import create_access_token
    token = create_access_token(test_user.id)
    headers = {"Authorization": f"Bearer {token}"}  # No X-Requested-With
    resp = client.post("/api/auth/logout", headers=headers)
    # CSRF middleware should block state-changing requests without the header
    assert resp.status_code == 403


def test_public_endpoints_no_csrf_needed(client, db_session, test_user):
    import secrets
    from datetime import datetime, timedelta
    token = secrets.token_urlsafe(32)
    test_user.checkin_token = token
    test_user.checkin_token_expires_at = datetime.utcnow() + timedelta(hours=24)
    db_session.commit()
    # Public checkin endpoint should work without X-Requested-With
    resp = client.post("/api/checkin", json={"token": token})
    assert resp.status_code == 200


def test_health_endpoint(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
