# datetime is used to compare the token expiry against the current time
from datetime import datetime

# FastAPI routing, dependency injection, HTTP exceptions, request object, and status codes
from fastapi import APIRouter, Depends, HTTPException, Request, status
# SQLAlchemy session for DB access
from sqlalchemy.orm import Session

# Database session dependency
from app.database import get_db
# Beneficiary ORM model — looked up by release token
from app.models.beneficiary import Beneficiary
# Secret ORM model — accessed via the assignment relationship
from app.models.secret import Secret
# SecretAssignment ORM model — the join table that links secrets to this beneficiary
from app.models.secret_assignment import SecretAssignment
# Pydantic schemas for the release response
from app.schemas.release import ReleasedSecretItem, ReleaseResponse
# Audit logging — records when a beneficiary accesses their release link
from app.services.auth_service import log_audit

# All release endpoints are under /api/release with the "Release" tag
router = APIRouter(prefix="/api/release", tags=["Release"])


# GET /api/release/{token} — public endpoint for a beneficiary to retrieve their inherited secrets
# This is accessed from the email link — the token is the only authentication credential
@router.get("/{token}", response_model=ReleaseResponse)
def get_release(token: str, request: Request, db: Session = Depends(get_db)):
    # Record the current time for token expiry comparison
    now = datetime.utcnow()
    # Look up the beneficiary by their unique release token
    b = (
        db.query(Beneficiary)
        .filter(
            Beneficiary.release_token == token,        # Token must match exactly
            Beneficiary.release_token_expires_at > now, # Token must not be expired
        )
        .first()
    )
    if not b:
        # Token doesn't exist or has expired — return 404 (same error for both cases)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid or expired release link.")

    # Log that this beneficiary's release link was accessed (with their IP and email for auditing)
    log_audit(db, b.user_id, "release.accessed", details=b.email, ip_address=request.client.host)

    # Build the list of released secrets from all assignments belonging to this beneficiary
    items = []
    for assignment in b.assignments:
        # Navigate from assignment to the associated Secret via the ORM relationship
        secret: Secret = assignment.secret
        # Build a ReleasedSecretItem containing all the fields the beneficiary needs to decrypt
        items.append(
            ReleasedSecretItem(
                title=secret.title,                      # Human-readable label
                secret_type=secret.secret_type,          # Category (password/note/document/file)
                encrypted_content=secret.encrypted_content, # AES-GCM ciphertext (base64)
                encryption_iv=secret.encryption_iv,      # GCM nonce needed for decryption (base64)
                encryption_tag=secret.encryption_tag,    # GCM auth tag needed for decryption (base64)
                encrypted_key=assignment.encrypted_key,  # AES key encrypted with beneficiary's RSA key (base64)
            )
        )

    # Get the owning user for display information in the release page header
    user = b.user
    return ReleaseResponse(
        # Name of the person who passed away / became incapacitated
        deceased_name=user.name,
        # Name of this beneficiary — shown as a personalised greeting on the release page
        beneficiary_name=b.name,
        # When the secrets were released — shown on the release page for context
        released_at=user.released_at,
        # The list of encrypted secrets with all data needed for client-side decryption
        secrets=items,
    )
