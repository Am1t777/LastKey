import pytest
from fastapi import HTTPException
from app.services.secret_service import create_secret, assign_secret
from app.models.secret import SecretType


def test_create_secret_no_beneficiaries(db_session, test_user):
    secret = create_secret(
        db=db_session,
        user_id=test_user.id,
        title="My Note",
        content="content",
        secret_type=SecretType.note,
        password="pass",
        beneficiary_ids=[],
    )
    assert secret.id is not None
    assert secret.title == "My Note"
    assert len(secret.assignments) == 0


def test_create_secret_with_beneficiary(db_session, test_user, beneficiary_with_key):
    beneficiary, _ = beneficiary_with_key
    secret = create_secret(
        db=db_session,
        user_id=test_user.id,
        title="Assigned Secret",
        content="content",
        secret_type=SecretType.password,
        password="pass",
        beneficiary_ids=[beneficiary.id],
    )
    assert len(secret.assignments) == 1


def test_cross_user_assignment_raises(db_session, test_user, test_user_b, beneficiary_with_key):
    # beneficiary belongs to test_user; try to assign from test_user_b context
    beneficiary, _ = beneficiary_with_key
    # Create a secret for user_b
    secret = create_secret(
        db=db_session,
        user_id=test_user_b.id,
        title="B's Secret",
        content="b content",
        secret_type=SecretType.note,
        password="pass",
        beneficiary_ids=[],
    )
    # try to assign user_a's beneficiary to user_b's secret
    # assign_secret uses secret.user_id internally, so this should raise 404
    # (beneficiary belongs to test_user, not test_user_b)
    with pytest.raises(HTTPException) as exc_info:
        assign_secret(
            db=db_session,
            secret=secret,
            password="pass",
            beneficiary_id=beneficiary.id,
        )
    assert exc_info.value.status_code == 404


def test_assign_beneficiary_without_key_raises(db_session, test_user):
    from app.models.beneficiary import Beneficiary
    # Create beneficiary without a public key
    b = Beneficiary(
        user_id=test_user.id,
        name="No Key Beneficiary",
        email="nokey@test.com",
        public_key=None,
    )
    db_session.add(b)
    db_session.commit()
    db_session.refresh(b)

    secret = create_secret(
        db=db_session,
        user_id=test_user.id,
        title="Test",
        content="content",
        secret_type=SecretType.note,
        password="pass",
        beneficiary_ids=[],
    )
    with pytest.raises(HTTPException) as exc_info:
        assign_secret(
            db=db_session,
            secret=secret,
            password="pass",
            beneficiary_id=b.id,
        )
    assert exc_info.value.status_code == 400
