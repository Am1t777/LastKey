import pytest
from datetime import timedelta

from app.services.auth_service import (
    hash_password,
    verify_password,
    create_access_token,
)
from app.models.audit_log import AuditLog


def test_hash_and_verify():
    pw = "mypassword"
    hashed = hash_password(pw)
    assert hashed != pw
    assert verify_password(pw, hashed)
    assert not verify_password("wrong", hashed)


def test_jwt_create_and_decode():
    from jose import jwt
    from app.config import settings
    token = create_access_token(42)
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    assert payload["sub"] == "42"


def test_jwt_expired():
    from jose import JWTError, jwt
    from datetime import datetime
    from app.config import settings
    # Create an already-expired token by patching expire time in the past
    expire = datetime.utcnow() - timedelta(seconds=10)
    payload = {"sub": "1", "exp": expire}
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    with pytest.raises(JWTError):
        jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])


def test_log_audit_creates_row(db_session, test_user):
    from app.services.auth_service import log_audit
    log_audit(db_session, test_user.id, "test.action", details="detail", ip_address="127.0.0.1")
    db_session.flush()
    entry = db_session.query(AuditLog).filter(AuditLog.user_id == test_user.id).first()
    assert entry is not None
    assert entry.action == "test.action"
