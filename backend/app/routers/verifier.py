# secrets generates cryptographically secure random tokens for verifier action links
import secrets
# datetime provides utcnow() to reset the check-in timer when a verifier denies
from datetime import datetime

# FastAPI routing, dependency injection, HTTP exceptions, request object, and status codes
from fastapi import APIRouter, Depends, HTTPException, Request, status
# SQLAlchemy session for DB access
from sqlalchemy.orm import Session

# Database session dependency
from app.database import get_db
# Rate limiter — applied to the public confirm/deny endpoints to prevent token brute-forcing
from app.middleware.rate_limit import limiter
# TrustedVerifier ORM model
from app.models.trusted_verifier import TrustedVerifier
# User ORM model and SwitchStatus enum for state machine transitions
from app.models.user import SwitchStatus, User
# Generic message response schema
from app.schemas.auth import MessageResponse
# All verifier-related Pydantic schemas
from app.schemas.verifier import (
    VerifierActionResponse,  # Response returned after a confirm or deny action
    VerifierConfirmRequest,  # Body for the confirm endpoint: requires the user's name to be typed
    VerifierCreate,          # Body for setting a verifier: name + email
    VerifierResponse,        # Public verifier info (no tokens — they are secret)
)
# JWT validation and audit logging
from app.services.auth_service import get_current_user, log_audit
# trigger_release starts the secret distribution process when the verifier confirms
from app.services.release_service import trigger_release

# Protected verifier management routes — require a valid JWT
router = APIRouter(prefix="/api/verifier", tags=["Verifier"])
# Public verify routes — accessed via email link tokens, no JWT required
public_verify_router = APIRouter(prefix="/api/verify", tags=["Verify"])


# _to_response converts a TrustedVerifier ORM object to the safe public response schema
def _to_response(v: TrustedVerifier) -> VerifierResponse:
    return VerifierResponse(
        id=v.id,
        name=v.name,
        email=v.email,
        # Whether the verifier has already clicked the confirm link
        has_confirmed=v.has_confirmed,
        # Whether the verifier has already clicked the deny link
        has_denied=v.has_denied,
    )


# ── Protected: manage verifier ────────────────────────────────────────────────

# POST /api/verifier — set or update the trusted verifier (upsert semantics)
@router.post("", response_model=VerifierResponse, status_code=status.HTTP_200_OK)
def set_verifier(
    body: VerifierCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Check if a verifier already exists for this user
    existing = db.query(TrustedVerifier).filter(TrustedVerifier.user_id == current_user.id).first()
    if existing:
        # Silent upsert — update the existing record in place rather than deleting and recreating
        existing.name = body.name
        existing.email = str(body.email)
        # Regenerate tokens so any old confirmation/denial links are invalidated
        existing.verification_token = secrets.token_urlsafe(32)
        existing.denial_token = secrets.token_urlsafe(32)
        # Reset confirmation/denial flags since the new verifier hasn't acted yet
        existing.has_confirmed = False
        existing.has_denied = False
        # Clear contacted_at — the new verifier hasn't been contacted yet
        existing.contacted_at = None
        db.commit()
        db.refresh(existing)
        log_audit(db, current_user.id, "verifier.set", details=str(body.email), ip_address=request.client.host)
        return _to_response(existing)

    # No existing verifier — create a new one with fresh tokens
    v = TrustedVerifier(
        user_id=current_user.id,
        name=body.name,
        email=str(body.email),
        # Generate tokens immediately so they exist even before the verifier is ever contacted
        verification_token=secrets.token_urlsafe(32),
        denial_token=secrets.token_urlsafe(32),
    )
    db.add(v)
    db.commit()
    db.refresh(v)
    log_audit(db, current_user.id, "verifier.set", details=str(body.email), ip_address=request.client.host)
    return _to_response(v)


# GET /api/verifier — retrieve the current user's trusted verifier
@router.get("", response_model=VerifierResponse)
def get_verifier(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Look up the verifier for this user (at most one per user)
    v = db.query(TrustedVerifier).filter(TrustedVerifier.user_id == current_user.id).first()
    if not v:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No trusted verifier set")
    return _to_response(v)


# DELETE /api/verifier — remove the trusted verifier
@router.delete("", response_model=MessageResponse)
def delete_verifier(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    v = db.query(TrustedVerifier).filter(TrustedVerifier.user_id == current_user.id).first()
    if not v:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No trusted verifier set")
    # Hard delete — all tokens are discarded
    db.delete(v)
    db.commit()
    log_audit(db, current_user.id, "verifier.delete", details="", ip_address=request.client.host)
    return MessageResponse(message="Trusted verifier removed")


# ── Public: confirm / deny ────────────────────────────────────────────────────

# POST /api/verify/{token}/confirm — verifier confirms the user is dead/incapacitated
# This is a public endpoint — the token in the URL acts as the authentication credential
@public_verify_router.post("/{token}/confirm", response_model=VerifierActionResponse)
# Rate-limited to prevent attackers from brute-forcing the confirmation token
@limiter.limit("10/minute")
def confirm_death(
    token: str,                 # The confirmation token from the email link
    body: VerifierConfirmRequest,  # Requires the user's full name to be typed as a safety check
    request: Request,
    db: Session = Depends(get_db),
):
    # Look up the verifier by their confirmation token — an invalid token returns 404
    v = db.query(TrustedVerifier).filter(TrustedVerifier.verification_token == token).first()
    if not v:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid verification link")

    # Navigate from the verifier to the user they are watching over
    user: User = v.user
    # Only allow confirmation when the switch is in the "verifier_alerted" state
    # (prevents replaying old confirmation links after the user has checked in again)
    if user.switch_status != SwitchStatus.verifier_alerted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active verification request for this user.",
        )

    # Require the verifier to type the user's full name as a deliberate confirmation step
    # Case-insensitive comparison after stripping whitespace from both sides
    if body.confirmation_text.strip().lower() != user.name.strip().lower():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Name does not match. Please type the person's full name exactly.",
        )

    # Mark the verifier as having confirmed
    v.has_confirmed = True
    # Advance the user's switch to the final "released" state
    user.switch_status = SwitchStatus.released
    db.commit()

    # Log the confirmation event with the verifier's email for auditing
    log_audit(db, user.id, "verifier.confirmed", details=v.email, ip_address=request.client.host)
    # Trigger the release flow — generates tokens and emails all beneficiaries
    trigger_release(db=db, user=user, ip_address=request.client.host)
    return VerifierActionResponse(
        message="Thank you. The account has been marked as incapacitated. Beneficiaries will be notified.",
        action="confirmed",
    )


# POST /api/verify/{token}/deny — verifier confirms the user is alive (false alarm)
# This is a public endpoint — the token in the URL acts as the authentication credential
@public_verify_router.post("/{token}/deny", response_model=VerifierActionResponse)
# Rate-limited to prevent attackers from brute-forcing the denial token
@limiter.limit("10/minute")
def deny_death(
    token: str,  # The denial token from the email link
    request: Request,
    db: Session = Depends(get_db),
):
    # Look up the verifier by their denial token — an invalid token returns 404
    v = db.query(TrustedVerifier).filter(TrustedVerifier.denial_token == token).first()
    if not v:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid verification link")

    # Navigate from the verifier to the user they are watching over
    user: User = v.user
    # Only allow denial when the switch is in the "verifier_alerted" state
    if user.switch_status != SwitchStatus.verifier_alerted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active verification request for this user.",
        )

    # Record that the verifier has denied (user is alive)
    v.has_denied = True
    # Reset the switch back to "active" — the user is confirmed alive
    user.switch_status = SwitchStatus.active
    # Reset the check-in timer to now so the user gets a fresh interval
    user.last_check_in_at = datetime.utcnow()
    # Clear the reminder timestamp since the cycle is being reset
    user.reminder_sent_at = None
    # Clear the verifier contact timestamp
    user.verifier_contacted_at = None
    db.commit()

    # Log the denial event for auditing
    log_audit(db, user.id, "verifier.denied", details=v.email, ip_address=request.client.host)
    return VerifierActionResponse(
        message="Thank you. The account has been reset and the timer restarted.",
        action="denied",
    )
