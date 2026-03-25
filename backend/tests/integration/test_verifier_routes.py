import pytest


def test_set_verifier(client, auth_headers):
    resp = client.post("/api/verifier", json={
        "name": "Verif Person", "email": "verif@test.com"
    }, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["email"] == "verif@test.com"


def test_get_verifier(client, auth_headers):
    client.post("/api/verifier", json={"name": "V", "email": "v@test.com"}, headers=auth_headers)
    resp = client.get("/api/verifier", headers=auth_headers)
    assert resp.status_code == 200


def test_get_verifier_not_found(client, auth_headers):
    resp = client.get("/api/verifier", headers=auth_headers)
    assert resp.status_code == 404


def test_delete_verifier(client, auth_headers):
    client.post("/api/verifier", json={"name": "V", "email": "v@test.com"}, headers=auth_headers)
    resp = client.delete("/api/verifier", headers=auth_headers)
    assert resp.status_code == 200


def test_confirm_death(client, db_session, verifier_alerted_user):
    user, verifier = verifier_alerted_user
    resp = client.post(
        f"/api/verify/{verifier.verification_token}/confirm",
        json={"confirmation_text": user.name},
    )
    assert resp.status_code == 200
    assert resp.json()["action"] == "confirmed"


def test_confirm_death_wrong_name(client, verifier_alerted_user):
    user, verifier = verifier_alerted_user
    resp = client.post(
        f"/api/verify/{verifier.verification_token}/confirm",
        json={"confirmation_text": "Wrong Name"},
    )
    assert resp.status_code == 400


def test_deny_death(client, db_session, verifier_alerted_user):
    user, verifier = verifier_alerted_user
    resp = client.post(f"/api/verify/{verifier.denial_token}/deny")
    assert resp.status_code == 200
    assert resp.json()["action"] == "denied"
