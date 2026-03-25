import secrets
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.trusted_verifier import TrustedVerifier
from app.models.user import SwitchStatus, User
from app.schemas.auth import MessageResponse
from app.schemas.verifier import (
    VerifierActionResponse,
    VerifierConfirmRequest,
    VerifierCreate,
    VerifierResponse,
)
from app.services.auth_service import get_current_user, log_audit

router = APIRouter(prefix="/api/verifier", tags=["Verifier"])
public_verify_router = APIRouter(prefix="/api/verify", tags=["Verify"])


def _to_response(v: TrustedVerifier) -> VerifierResponse:
    return VerifierResponse(
        id=v.id,
        name=v.name,
        email=v.email,
        has_confirmed=v.has_confirmed,
        has_denied=v.has_denied,
    )


# ── Protected: manage verifier ────────────────────────────────────────────────

@router.post("", response_model=VerifierResponse, status_code=status.HTTP_200_OK)
def set_verifier(
    body: VerifierCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    existing = db.query(TrustedVerifier).filter(TrustedVerifier.user_id == current_user.id).first()
    if existing:
        # Silent upsert — update in place, regenerate tokens
        existing.name = body.name
        existing.email = str(body.email)
        existing.verification_token = secrets.token_urlsafe(32)
        existing.denial_token = secrets.token_urlsafe(32)
        existing.has_confirmed = False
        existing.has_denied = False
        existing.contacted_at = None
        db.commit()
        db.refresh(existing)
        log_audit(db, current_user.id, "verifier.set", details=str(body.email), ip_address=request.client.host)
        return _to_response(existing)

    v = TrustedVerifier(
        user_id=current_user.id,
        name=body.name,
        email=str(body.email),
        verification_token=secrets.token_urlsafe(32),
        denial_token=secrets.token_urlsafe(32),
    )
    db.add(v)
    db.commit()
    db.refresh(v)
    log_audit(db, current_user.id, "verifier.set", details=str(body.email), ip_address=request.client.host)
    return _to_response(v)


@router.get("", response_model=VerifierResponse)
def get_verifier(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    v = db.query(TrustedVerifier).filter(TrustedVerifier.user_id == current_user.id).first()
    if not v:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No trusted verifier set")
    return _to_response(v)


@router.delete("", response_model=MessageResponse)
def delete_verifier(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    v = db.query(TrustedVerifier).filter(TrustedVerifier.user_id == current_user.id).first()
    if not v:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No trusted verifier set")
    db.delete(v)
    db.commit()
    log_audit(db, current_user.id, "verifier.delete", details="", ip_address=request.client.host)
    return MessageResponse(message="Trusted verifier removed")


# ── Public: confirm / deny ────────────────────────────────────────────────────

@public_verify_router.post("/{token}/confirm", response_model=VerifierActionResponse)
def confirm_death(
    token: str,
    body: VerifierConfirmRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    v = db.query(TrustedVerifier).filter(TrustedVerifier.verification_token == token).first()
    if not v:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid verification link")

    user: User = v.user
    if user.switch_status != SwitchStatus.verifier_alerted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active verification request for this user.",
        )

    if body.confirmation_text.strip().lower() != user.name.strip().lower():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Name does not match. Please type the person's full name exactly.",
        )

    v.has_confirmed = True
    user.switch_status = SwitchStatus.released
    db.commit()

    log_audit(db, user.id, "verifier.confirmed", details=v.email, ip_address=request.client.host)
    # Step 9 will hook into this point to trigger the secret release flow.
    return VerifierActionResponse(
        message="Thank you. The account has been marked as incapacitated. Beneficiaries will be notified.",
        action="confirmed",
    )


@public_verify_router.post("/{token}/deny", response_model=VerifierActionResponse)
def deny_death(
    token: str,
    request: Request,
    db: Session = Depends(get_db),
):
    v = db.query(TrustedVerifier).filter(TrustedVerifier.denial_token == token).first()
    if not v:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid verification link")

    user: User = v.user
    if user.switch_status != SwitchStatus.verifier_alerted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active verification request for this user.",
        )

    v.has_denied = True
    user.switch_status = SwitchStatus.active
    user.last_check_in_at = datetime.utcnow()
    user.reminder_sent_at = None
    user.verifier_contacted_at = None
    db.commit()

    log_audit(db, user.id, "verifier.denied", details=v.email, ip_address=request.client.host)
    return VerifierActionResponse(
        message="Thank you. The account has been reset and the timer restarted.",
        action="denied",
    )
