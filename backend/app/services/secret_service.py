"""Business logic for secrets: encryption, owner-key storage, beneficiary assignment."""

import base64
import os

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.beneficiary import Beneficiary
from app.models.secret import Secret, SecretType
from app.models.secret_assignment import SecretAssignment
from app.services.encryption_service import (
    decrypt_content,
    derive_key,
    encrypt_content,
    encrypt_key_for_beneficiary,
    generate_aes_key,
)

# Separator used when packing multiple base64 values into owner_encrypted_key column
_SEP = ":"


def _pack(*parts: str) -> str:
    """Join base64 parts with separator into a single string for storage."""
    return _SEP.join(parts)


def _unpack(packed: str) -> tuple[str, str, str, str]:
    """Unpack owner_encrypted_key string → (salt_b64, ct_b64, iv_b64, tag_b64)."""
    parts = packed.split(_SEP, 3)
    if len(parts) != 4:
        raise ValueError("Malformed owner_encrypted_key")
    return tuple(parts)  # type: ignore[return-value]


def _encrypt_aes_key_for_owner(aes_key: bytes, password: str) -> str:
    """Encrypt an AES key with a password-derived Argon2id key.

    Returns a packed string: salt_b64:ct_b64:iv_b64:tag_b64
    The AES key is base64-encoded before encrypting so encrypt_content (which
    takes str input) can process it.
    """
    salt = os.urandom(16)
    owner_key = derive_key(password, salt)
    aes_key_b64_str = base64.b64encode(aes_key).decode("utf-8")
    ct_b64, iv_b64, tag_b64 = encrypt_content(aes_key_b64_str, owner_key)
    salt_b64 = base64.b64encode(salt).decode("utf-8")
    return _pack(salt_b64, ct_b64, iv_b64, tag_b64)


def _decrypt_aes_key_from_owner(owner_encrypted_key: str, password: str) -> bytes:
    """Recover the raw AES key from the packed owner_encrypted_key field."""
    salt_b64, ct_b64, iv_b64, tag_b64 = _unpack(owner_encrypted_key)
    salt = base64.b64decode(salt_b64)
    owner_key = derive_key(password, salt)
    try:
        aes_key_b64_str = decrypt_content(ct_b64, owner_key, iv_b64, tag_b64)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password",
        )
    return base64.b64decode(aes_key_b64_str)


def _assign_beneficiary(
    db: Session,
    secret: Secret,
    aes_key: bytes,
    beneficiary_id: int,
    owner_user_id: int,
) -> None:
    """Create a SecretAssignment row — raises 404/400 on bad beneficiary."""
    beneficiary = (
        db.query(Beneficiary)
        .filter(
            Beneficiary.id == beneficiary_id,
            Beneficiary.user_id == owner_user_id,
        )
        .first()
    )
    if beneficiary is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Beneficiary {beneficiary_id} not found",
        )
    if beneficiary.public_key is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Beneficiary {beneficiary_id} has no RSA key — generate one first",
        )
    # Check for existing assignment to avoid duplicates
    existing = (
        db.query(SecretAssignment)
        .filter(
            SecretAssignment.secret_id == secret.id,
            SecretAssignment.beneficiary_id == beneficiary_id,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Secret is already assigned to beneficiary {beneficiary_id}",
        )
    encrypted_key = encrypt_key_for_beneficiary(aes_key, beneficiary.public_key)
    db.add(
        SecretAssignment(
            secret_id=secret.id,
            beneficiary_id=beneficiary_id,
            encrypted_key=encrypted_key,
        )
    )


# ── Public API ──────────────────────────────────────────────────────────────


def get_secret_or_404(db: Session, secret_id: int, user_id: int) -> Secret:
    secret = (
        db.query(Secret)
        .filter(Secret.id == secret_id, Secret.user_id == user_id)
        .first()
    )
    if not secret:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Secret not found",
        )
    return secret


def create_secret(
    db: Session,
    user_id: int,
    title: str,
    content: str,
    secret_type: SecretType,
    password: str,
    beneficiary_ids: list[int],
) -> Secret:
    aes_key = generate_aes_key()
    encrypted_content, iv, tag = encrypt_content(content, aes_key)
    owner_encrypted_key = _encrypt_aes_key_for_owner(aes_key, password)

    secret = Secret(
        user_id=user_id,
        title=title,
        encrypted_content=encrypted_content,
        encryption_iv=iv,
        encryption_tag=tag,
        secret_type=secret_type,
        owner_encrypted_key=owner_encrypted_key,
    )
    db.add(secret)
    db.flush()  # get secret.id before creating assignments

    for b_id in beneficiary_ids:
        _assign_beneficiary(db, secret, aes_key, b_id, user_id)

    db.commit()
    db.refresh(secret)
    return secret


def update_secret(
    db: Session,
    secret: Secret,
    title: str | None,
    content: str | None,
    secret_type: SecretType | None,
    password: str | None,
) -> Secret:
    if content is not None:
        if password is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password is required when updating secret content",
            )
        aes_key = generate_aes_key()
        secret.encrypted_content, secret.encryption_iv, secret.encryption_tag = (
            encrypt_content(content, aes_key)
        )
        secret.owner_encrypted_key = _encrypt_aes_key_for_owner(aes_key, password)
        # Existing beneficiary assignments become stale — delete and let the owner reassign
        db.query(SecretAssignment).filter(
            SecretAssignment.secret_id == secret.id
        ).delete()

    if title is not None:
        secret.title = title
    if secret_type is not None:
        secret.secret_type = secret_type

    db.commit()
    db.refresh(secret)
    return secret


def assign_secret(
    db: Session,
    secret: Secret,
    password: str,
    beneficiary_id: int,
) -> None:
    """Post-creation assignment: derive owner key → decrypt AES key → re-encrypt for beneficiary."""
    aes_key = _decrypt_aes_key_from_owner(secret.owner_encrypted_key, password)
    _assign_beneficiary(db, secret, aes_key, beneficiary_id, secret.user_id)
    db.commit()
