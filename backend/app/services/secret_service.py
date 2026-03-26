"""Business logic for secrets: encryption, owner-key storage, beneficiary assignment."""

# base64 is used to encode/decode the AES key when packing it into the owner_encrypted_key column
import base64
# os.urandom generates the random salt for each Argon2id key derivation
import os

# FastAPI HTTP exception and status codes for returning errors to clients
from fastapi import HTTPException, status
# SQLAlchemy session type for DB operations
from sqlalchemy.orm import Session

# ORM models we need to query
from app.models.beneficiary import Beneficiary
from app.models.secret import Secret, SecretType
from app.models.secret_assignment import SecretAssignment
# Cryptographic helpers for generating keys, encrypting content, and wrapping keys
from app.services.encryption_service import (
    decrypt_content,
    derive_key,
    encrypt_content,
    encrypt_key_for_beneficiary,
    generate_aes_key,
)

# Separator character used to join the four base64 parts of owner_encrypted_key into one string
_SEP = ":"


# _pack concatenates multiple base64 strings with ":" so they can be stored in a single DB column
def _pack(*parts: str) -> str:
    """Join base64 parts with separator into a single string for storage."""
    return _SEP.join(parts)


# _unpack splits the packed owner_encrypted_key string back into its four components
def _unpack(packed: str) -> tuple[str, str, str, str]:
    """Unpack owner_encrypted_key string → (salt_b64, ct_b64, iv_b64, tag_b64)."""
    # Split on ":" into at most 4 parts (the base64 values themselves cannot contain ":")
    parts = packed.split(_SEP, 3)
    # Validate that all four parts are present — a missing part means the data is corrupt
    if len(parts) != 4:
        raise ValueError("Malformed owner_encrypted_key")
    return tuple(parts)  # type: ignore[return-value]


# _encrypt_aes_key_for_owner password-protects the AES key so only the owner can decrypt it
def _encrypt_aes_key_for_owner(aes_key: bytes, password: str) -> str:
    """Encrypt an AES key with a password-derived Argon2id key.

    Returns a packed string: salt_b64:ct_b64:iv_b64:tag_b64
    The AES key is base64-encoded before encrypting so encrypt_content (which
    takes str input) can process it.
    """
    # Generate a fresh 16-byte random salt — unique per secret so the same password
    # produces a different derived key each time
    salt = os.urandom(16)
    # Derive a 256-bit AES key from the user's password and this salt using Argon2id
    owner_key = derive_key(password, salt)
    # Base64-encode the raw AES key bytes so encrypt_content (which expects a str) can handle it
    aes_key_b64_str = base64.b64encode(aes_key).decode("utf-8")
    # Encrypt the base64-encoded AES key with the Argon2id-derived key
    ct_b64, iv_b64, tag_b64 = encrypt_content(aes_key_b64_str, owner_key)
    # Base64-encode the salt so all parts can be safely joined with ":"
    salt_b64 = base64.b64encode(salt).decode("utf-8")
    # Pack all four parts into one string for single-column storage
    return _pack(salt_b64, ct_b64, iv_b64, tag_b64)


# _decrypt_aes_key_from_owner recovers the AES key by re-deriving the owner's Argon2id key
def _decrypt_aes_key_from_owner(owner_encrypted_key: str, password: str) -> bytes:
    """Recover the raw AES key from the packed owner_encrypted_key field."""
    # Unpack the stored string back into its four base64 components
    salt_b64, ct_b64, iv_b64, tag_b64 = _unpack(owner_encrypted_key)
    # Decode the salt from base64 back to raw bytes
    salt = base64.b64decode(salt_b64)
    # Re-derive the owner's AES key from the provided password and the stored salt
    owner_key = derive_key(password, salt)
    try:
        # Decrypt the stored ciphertext — raises if the password is wrong (GCM tag mismatch)
        aes_key_b64_str = decrypt_content(ct_b64, owner_key, iv_b64, tag_b64)
    except Exception:
        # Translate any decryption failure into an HTTP 401 with a user-friendly message
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password",
        )
    # The decrypted value is the AES key itself encoded as base64 — decode it back to bytes
    return base64.b64decode(aes_key_b64_str)


# _assign_beneficiary creates one SecretAssignment row linking a secret to a beneficiary
def _assign_beneficiary(
    db: Session,
    secret: Secret,       # The secret to assign
    aes_key: bytes,       # The raw AES key that decrypts the secret's content
    beneficiary_id: int,  # ID of the beneficiary who should receive the secret
    owner_user_id: int,   # ID of the user who owns the secret (for ownership validation)
) -> None:
    """Create a SecretAssignment row — raises 404/400 on bad beneficiary."""
    # Look up the beneficiary, verifying it belongs to the same user (prevents IDOR)
    beneficiary = (
        db.query(Beneficiary)
        .filter(
            Beneficiary.id == beneficiary_id,
            Beneficiary.user_id == owner_user_id,
        )
        .first()
    )
    # Beneficiary not found or belongs to a different user — return 404 to avoid leaking existence
    if beneficiary is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Beneficiary {beneficiary_id} not found",
        )
    # The beneficiary must have an RSA key before secrets can be assigned to them
    if beneficiary.public_key is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Beneficiary {beneficiary_id} has no RSA key — generate one first",
        )
    # Check for existing assignment to avoid duplicates (same secret assigned to same beneficiary twice)
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
    # Encrypt the AES key with the beneficiary's RSA public key
    encrypted_key = encrypt_key_for_beneficiary(aes_key, beneficiary.public_key)
    # Add the SecretAssignment row to the session (will be committed by the caller)
    db.add(
        SecretAssignment(
            secret_id=secret.id,
            beneficiary_id=beneficiary_id,
            encrypted_key=encrypted_key,
        )
    )


# ── Public API ──────────────────────────────────────────────────────────────


# get_secret_or_404 fetches a secret by ID, verifying ownership, or raises 404
def get_secret_or_404(db: Session, secret_id: int, user_id: int) -> Secret:
    secret = (
        db.query(Secret)
        # Filter by both secret ID and user_id to prevent IDOR (accessing another user's secret)
        .filter(Secret.id == secret_id, Secret.user_id == user_id)
        .first()
    )
    if not secret:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Secret not found",
        )
    return secret


# create_secret is the main entry point for storing a new encrypted secret
def create_secret(
    db: Session,
    user_id: int,                # Owner of the secret
    title: str,                  # Human-readable label (stored unencrypted)
    content: str,                # The actual secret data — will be encrypted
    secret_type: SecretType,     # Category (password / note / document / file)
    password: str,               # Owner's password used to protect the AES key
    beneficiary_ids: list[int],  # Beneficiaries who should receive this secret
) -> Secret:
    # Generate a fresh random AES-256 key unique to this secret
    aes_key = generate_aes_key()
    # Encrypt the content with the AES key; store ciphertext, nonce, and auth tag separately
    encrypted_content, iv, tag = encrypt_content(content, aes_key)
    # Encrypt the AES key with the owner's password-derived key for self-decryption
    owner_encrypted_key = _encrypt_aes_key_for_owner(aes_key, password)

    # Build the Secret ORM object — the plaintext is never stored in the database
    secret = Secret(
        user_id=user_id,
        title=title,
        encrypted_content=encrypted_content,
        encryption_iv=iv,
        encryption_tag=tag,
        secret_type=secret_type,
        owner_encrypted_key=owner_encrypted_key,
    )
    # Stage the secret for insertion
    db.add(secret)
    # flush() sends the INSERT to the DB (but does not commit) so secret.id is populated
    db.flush()  # get secret.id before creating assignments

    # For each beneficiary, encrypt the AES key with their RSA public key and create an assignment row
    for b_id in beneficiary_ids:
        _assign_beneficiary(db, secret, aes_key, b_id, user_id)

    # Commit the transaction — persists the secret and all assignments atomically
    db.commit()
    # Refresh reloads the secret object with any DB-generated values (e.g., updated_at)
    db.refresh(secret)
    return secret


# update_secret modifies an existing secret's metadata and/or content
def update_secret(
    db: Session,
    secret: Secret,
    title: str | None,            # New title (None = no change)
    content: str | None,          # New plaintext content (None = no change)
    secret_type: SecretType | None,  # New type category (None = no change)
    password: str | None,         # Required when content is being updated
) -> Secret:
    # Only re-encrypt if content is being changed
    if content is not None:
        # Password is mandatory when updating content — it's needed to produce a new owner_encrypted_key
        if password is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password is required when updating secret content",
            )
        # Generate a completely new AES key for the updated content
        aes_key = generate_aes_key()
        # Re-encrypt the new content with the new AES key
        secret.encrypted_content, secret.encryption_iv, secret.encryption_tag = (
            encrypt_content(content, aes_key)
        )
        # Re-encrypt the new AES key with the owner's password
        secret.owner_encrypted_key = _encrypt_aes_key_for_owner(aes_key, password)
        # The old beneficiary assignments encrypted the OLD AES key — they are now stale
        # Delete them so the owner must manually re-assign with the new key
        db.query(SecretAssignment).filter(
            SecretAssignment.secret_id == secret.id
        ).delete()

    # Update title if a new one was provided
    if title is not None:
        secret.title = title
    # Update secret type if a new one was provided
    if secret_type is not None:
        secret.secret_type = secret_type

    # Persist all changes
    db.commit()
    # Reload to get DB-updated fields (e.g., updated_at)
    db.refresh(secret)
    return secret


# assign_secret adds a new beneficiary assignment to an existing secret after creation
def assign_secret(
    db: Session,
    secret: Secret,      # The secret to assign
    password: str,       # Owner's password — needed to decrypt the AES key
    beneficiary_id: int, # ID of the beneficiary to assign
) -> None:
    """Post-creation assignment: derive owner key → decrypt AES key → re-encrypt for beneficiary."""
    # Recover the raw AES key by decrypting the owner_encrypted_key with the provided password
    aes_key = _decrypt_aes_key_from_owner(secret.owner_encrypted_key, password)
    # Create the SecretAssignment row (encrypts the AES key with the beneficiary's RSA key)
    _assign_beneficiary(db, secret, aes_key, beneficiary_id, secret.user_id)
    # Commit the new assignment to the database
    db.commit()
