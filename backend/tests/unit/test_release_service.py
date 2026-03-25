import pytest
from datetime import datetime
from app.services.release_service import trigger_release
from app.models.user import SwitchStatus


def test_trigger_release_sets_released_at(db_session, test_user, beneficiary_with_key, mock_email):
    beneficiary, private_pem = beneficiary_with_key
    trigger_release(db=db_session, user=test_user, ip_address="127.0.0.1")
    db_session.refresh(test_user)
    db_session.refresh(beneficiary)
    # trigger_release sets released_at timestamp
    assert test_user.released_at is not None
    assert test_user.released_at <= datetime.utcnow()


def test_trigger_release_sets_beneficiary_token(
    db_session, test_user, secret_with_assignment, mock_email
):
    secret, beneficiary, private_pem, password = secret_with_assignment
    trigger_release(db=db_session, user=test_user, ip_address="127.0.0.1")
    db_session.refresh(beneficiary)
    assert beneficiary.release_token is not None
    assert beneficiary.release_token_expires_at > datetime.utcnow()


def test_trigger_release_calls_email(
    db_session, test_user, secret_with_assignment, mock_email
):
    secret, beneficiary, _, _ = secret_with_assignment
    trigger_release(db=db_session, user=test_user, ip_address="127.0.0.1")
    assert mock_email["release"].called
