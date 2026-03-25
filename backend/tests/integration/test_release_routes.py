import pytest
from datetime import datetime, timedelta


def test_get_release(client, db_session, test_user, secret_with_assignment, mock_email):
    from app.services.release_service import trigger_release
    secret, beneficiary, private_pem, password = secret_with_assignment
    trigger_release(db=db_session, user=test_user, ip_address="127.0.0.1")
    db_session.refresh(beneficiary)
    token = beneficiary.release_token
    resp = client.get(f"/api/release/{token}")
    assert resp.status_code == 200


def test_get_release_invalid_token(client):
    resp = client.get("/api/release/invalid-token-xyz")
    assert resp.status_code == 404
